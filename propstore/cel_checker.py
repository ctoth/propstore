"""CEL condition expression type-checker for the propstore concept registry.

Parses a subset of CEL sufficient for the condition expressions used in
concept relationships and parameterization relationships. Type-checks
every name reference against the concept registry's kind system.

The expressions are simple: comparisons, arithmetic, &&, ||, in-lists.
We parse a sufficient subset rather than implementing full CEL.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from propstore.cel_bindings import STANDARD_SYNTHETIC_BINDING_NAMES as _STANDARD_SYNTHETIC_BINDING_NAMES
from propstore.cel_types import (
    CelExpr,
    CelRegistryFingerprint,
    CheckedCelConditionSet,
    CheckedCelExpr,
    ParsedCelExpr,
    checked_condition_set,
    to_cel_expr,
)


class KindType(Enum):
    QUANTITY = "quantity"
    CATEGORY = "category"
    BOOLEAN = "boolean"
    STRUCTURAL = "structural"
    TIMEPOINT = "timepoint"


@dataclass
class ConceptInfo:
    """Minimal concept info needed for type-checking."""
    id: str
    canonical_name: str
    kind: KindType
    # For category kinds: the valid value set
    category_values: list[str] = field(default_factory=list)
    category_extensible: bool = True

def scope_cel_registry(
    registry: Mapping[str, ConceptInfo],
    concept_ids: set[str] | frozenset[str] | list[str] | tuple[str, ...],
) -> dict[str, ConceptInfo]:
    """Return the canonical-name keyed subset for the requested concept ids."""
    scoped_ids = {str(concept_id) for concept_id in concept_ids}
    return {
        canonical_name: info
        for canonical_name, info in registry.items()
        if info.id in scoped_ids
    }


def with_synthetic_concepts(
    registry: Mapping[str, ConceptInfo],
    concepts: Iterable[ConceptInfo],
) -> dict[str, ConceptInfo]:
    """Return a copy of *registry* augmented with synthetic CEL concepts."""
    result = dict(registry)
    for info in concepts:
        result[info.canonical_name] = info
    return result


def synthetic_category_concept(
    *,
    concept_id: str,
    canonical_name: str,
    values: Sequence[str],
    extensible: bool,
) -> ConceptInfo:
    """Build a synthetic category concept for CEL-only runtime state."""
    return ConceptInfo(
        id=concept_id,
        canonical_name=canonical_name,
        kind=KindType.CATEGORY,
        category_values=[value for value in values if isinstance(value, str)],
        category_extensible=extensible,
    )


def with_standard_synthetic_bindings(
    registry: Mapping[str, ConceptInfo],
) -> dict[str, ConceptInfo]:
    """Augment a registry with standard non-concept CEL binding dimensions."""
    synthetic_concepts = [
        synthetic_category_concept(
            concept_id=f"ps:concept:__{canonical_name}__",
            canonical_name=canonical_name,
            values=(),
            extensible=True,
        )
        for canonical_name in _STANDARD_SYNTHETIC_BINDING_NAMES
        if canonical_name not in registry
    ]
    if not synthetic_concepts:
        return dict(registry)
    return with_synthetic_concepts(registry, synthetic_concepts)


@dataclass
class CelError:
    expression: str
    message: str
    is_warning: bool = False

    def __str__(self) -> str:
        prefix = "WARNING" if self.is_warning else "ERROR"
        return f"{prefix}: {self.message} in expression: {self.expression}"


# ── Tokenizer ────────────────────────────────────────────────────────

class TokenType(Enum):
    NAME = "NAME"
    INT_LIT = "INT_LIT"
    FLOAT_LIT = "FLOAT_LIT"
    STRING_LIT = "STRING_LIT"
    BOOL_LIT = "BOOL_LIT"
    OP = "OP"          # +, -, *, /, ==, !=, <, >, <=, >=, &&, ||, !
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    IN = "IN"
    QUESTION = "QUESTION"
    COLON = "COLON"
    EOF = "EOF"


@dataclass
class Token:
    type: TokenType
    value: Any
    pos: int


_TOKEN_PATTERNS = [
    (r'\s+', None),  # skip whitespace
    (r'&&', TokenType.OP),
    (r'\|\|', TokenType.OP),
    (r'==', TokenType.OP),
    (r'!=', TokenType.OP),
    (r'<=', TokenType.OP),
    (r'>=', TokenType.OP),
    (r'<', TokenType.OP),
    (r'>', TokenType.OP),
    (r'[+\-*/]', TokenType.OP),
    (r'!', TokenType.OP),
    (r'\(', TokenType.LPAREN),
    (r'\)', TokenType.RPAREN),
    (r'\[', TokenType.LBRACKET),
    (r'\]', TokenType.RBRACKET),
    (r',', TokenType.COMMA),
    (r'\?', TokenType.QUESTION),
    (r':', TokenType.COLON),
    (r'"(?:[^"\\]|\\.)*"', TokenType.STRING_LIT),
    (r"'(?:[^'\\]|\\.)*'", TokenType.STRING_LIT),
    (r'\d+\.\d*|\.\d+', TokenType.FLOAT_LIT),
    (r'\d+', TokenType.INT_LIT),
    (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.NAME),
]

_COMPILED_PATTERNS = [(re.compile(p), t) for p, t in _TOKEN_PATTERNS]


def tokenize(expr: str) -> list[Token]:
    tokens: list[Token] = []
    pos = 0
    while pos < len(expr):
        matched = False
        for pattern, token_type in _COMPILED_PATTERNS:
            m = pattern.match(expr, pos)
            if m:
                if token_type is not None:
                    val = m.group()
                    if token_type == TokenType.NAME:
                        if val == "true" or val == "false":
                            token_type = TokenType.BOOL_LIT
                            val = val == "true"
                        elif val == "in":
                            token_type = TokenType.IN
                    elif token_type == TokenType.STRING_LIT:
                        val = val[1:-1]  # strip quotes
                        val = val.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
                    elif token_type == TokenType.INT_LIT:
                        val = int(val)
                    elif token_type == TokenType.FLOAT_LIT:
                        val = float(val)
                    tokens.append(Token(token_type, val, pos))
                pos = m.end()
                matched = True
                break
        if not matched:
            raise ValueError(f"Unexpected character at position {pos}: {expr[pos:]!r}")
    tokens.append(Token(TokenType.EOF, None, pos))
    return tokens


# ── Parser → AST ─────────────────────────────────────────────────────
# Recursive descent. Produces a simple AST for type-checking.

class ASTNode:
    pass


@dataclass
class NameNode(ASTNode):
    name: str


@dataclass
class LiteralNode(ASTNode):
    value: Any
    lit_type: str  # "int", "float", "string", "bool"


@dataclass
class BinaryOpNode(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOpNode(ASTNode):
    op: str
    operand: ASTNode


@dataclass
class InNode(ASTNode):
    """name in [list]"""
    expr: ASTNode
    values: list[ASTNode]


@dataclass
class TernaryNode(ASTNode):
    condition: ASTNode
    true_branch: ASTNode
    false_branch: ASTNode


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, token_type: TokenType) -> Token:
        t = self.advance()
        if t.type != token_type:
            raise ValueError(f"Expected {token_type}, got {t.type} ({t.value!r})")
        return t

    def parse(self) -> ASTNode:
        node = self.parse_ternary()
        if self.peek().type != TokenType.EOF:
            raise ValueError(f"Unexpected token after expression: {self.peek().value!r}")
        return node

    def parse_ternary(self) -> ASTNode:
        node = self.parse_or()
        if self.peek().type == TokenType.QUESTION:
            self.advance()
            true_branch = self.parse_ternary()
            self.expect(TokenType.COLON)
            false_branch = self.parse_ternary()
            return TernaryNode(node, true_branch, false_branch)
        return node

    def parse_or(self) -> ASTNode:
        left = self.parse_and()
        while self.peek().type == TokenType.OP and self.peek().value == "||":
            self.advance()
            right = self.parse_and()
            left = BinaryOpNode("||", left, right)
        return left

    def parse_and(self) -> ASTNode:
        left = self.parse_comparison()
        while self.peek().type == TokenType.OP and self.peek().value == "&&":
            self.advance()
            right = self.parse_comparison()
            left = BinaryOpNode("&&", left, right)
        return left

    def parse_comparison(self) -> ASTNode:
        left = self.parse_additive()
        if self.peek().type == TokenType.OP and self.peek().value in ("==", "!=", "<", ">", "<=", ">="):
            op = self.advance().value
            right = self.parse_additive()
            return BinaryOpNode(op, left, right)
        if self.peek().type == TokenType.IN:
            self.advance()
            self.expect(TokenType.LBRACKET)
            values = []
            if self.peek().type != TokenType.RBRACKET:
                values.append(self.parse_primary())
                while self.peek().type == TokenType.COMMA:
                    self.advance()
                    values.append(self.parse_primary())
            self.expect(TokenType.RBRACKET)
            return InNode(left, values)
        return left

    def parse_additive(self) -> ASTNode:
        left = self.parse_multiplicative()
        while self.peek().type == TokenType.OP and self.peek().value in ("+", "-"):
            op = self.advance().value
            right = self.parse_multiplicative()
            left = BinaryOpNode(op, left, right)
        return left

    def parse_multiplicative(self) -> ASTNode:
        left = self.parse_unary()
        while self.peek().type == TokenType.OP and self.peek().value in ("*", "/"):
            op = self.advance().value
            right = self.parse_unary()
            left = BinaryOpNode(op, left, right)
        return left

    def parse_unary(self) -> ASTNode:
        if self.peek().type == TokenType.OP and self.peek().value == "!":
            self.advance()
            operand = self.parse_unary()
            return UnaryOpNode("!", operand)
        if self.peek().type == TokenType.OP and self.peek().value == "-":
            self.advance()
            operand = self.parse_unary()
            return UnaryOpNode("-", operand)
        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        t = self.peek()
        if t.type == TokenType.NAME:
            self.advance()
            return NameNode(t.value)
        if t.type == TokenType.INT_LIT:
            self.advance()
            return LiteralNode(t.value, "int")
        if t.type == TokenType.FLOAT_LIT:
            self.advance()
            return LiteralNode(t.value, "float")
        if t.type == TokenType.STRING_LIT:
            self.advance()
            return LiteralNode(t.value, "string")
        if t.type == TokenType.BOOL_LIT:
            self.advance()
            return LiteralNode(t.value, "bool")
        if t.type == TokenType.LPAREN:
            self.advance()
            node = self.parse_ternary()
            self.expect(TokenType.RPAREN)
            return node
        raise ValueError(f"Unexpected token: {t.type} ({t.value!r}) at position {t.pos}")


def parse_cel(expr: str | CelExpr) -> ASTNode:
    tokens = tokenize(str(expr))
    parser = Parser(tokens)
    return parser.parse()


def parse_cel_expr(expr: str | CelExpr) -> ParsedCelExpr:
    source = to_cel_expr(expr)
    return ParsedCelExpr(source=source, ast=parse_cel(source))


# ── Type Checker ─────────────────────────────────────────────────────

# Type results from sub-expressions
class ExprType(Enum):
    NUMERIC = "numeric"
    STRING = "string"
    BOOLEAN = "boolean"
    UNKNOWN = "unknown"  # for mixed/error cases


ARITHMETIC_OPS = {"+", "-", "*", "/"}
ORDERING_OPS = {"<", ">", "<=", ">="}
EQUALITY_OPS = {"==", "!="}
LOGICAL_OPS = {"&&", "||"}

_DISALLOWED_KIND_USAGE: dict[str, dict[KindType, str]] = {
    "arithmetic": {
        KindType.CATEGORY: "Category concept '{name}' cannot appear in arithmetic",
        KindType.BOOLEAN: "Boolean concept '{name}' cannot appear in arithmetic",
    },
    "ordering comparison": {
        KindType.CATEGORY: "Category concept '{name}' cannot appear in ordering comparison",
        KindType.BOOLEAN: "Boolean concept '{name}' cannot appear in ordering comparison",
    },
}


def check_cel_expression(
    expr: str | CelExpr,
    registry: Mapping[str, ConceptInfo],
) -> list[CelError]:
    """Type-check a CEL expression against the concept registry.

    Args:
        expr: CEL expression string
        registry: mapping from canonical_name to ConceptInfo

    Returns:
        List of errors/warnings. Empty list means the expression is valid.
    """
    source = to_cel_expr(expr)
    errors: list[CelError] = []

    try:
        ast = parse_cel(source)
    except ValueError as e:
        errors.append(CelError(str(source), f"Parse error: {e}"))
        return errors

    _check_node(ast, str(source), registry, errors)
    return errors


def cel_registry_fingerprint(
    registry: Mapping[str, ConceptInfo],
) -> CelRegistryFingerprint:
    """Return a deterministic fingerprint of CEL-relevant registry semantics."""
    payload = [
        {
            "canonical_name": canonical_name,
            "id": info.id,
            "kind": info.kind.value,
            "category_values": sorted(info.category_values),
            "category_extensible": info.category_extensible,
        }
        for canonical_name, info in sorted(registry.items())
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return CelRegistryFingerprint(f"sha256:{digest}")


def check_cel_expr(
    expr: str | CelExpr,
    registry: Mapping[str, ConceptInfo],
) -> CheckedCelExpr:
    """Parse and type-check one CEL expression, returning a checked carrier."""
    source = to_cel_expr(expr)
    try:
        ast = parse_cel(source)
    except ValueError as exc:
        raise ValueError(f"Parse error: {exc}") from exc
    errors: list[CelError] = []
    _check_node(ast, str(source), registry, errors)
    hard_errors = [error for error in errors if not error.is_warning]
    if hard_errors:
        message = "; ".join(error.message for error in hard_errors)
        raise ValueError(message)
    return CheckedCelExpr._create(
        source=source,
        ast=ast,
        registry_fingerprint=cel_registry_fingerprint(registry),
        warnings=tuple(error for error in errors if error.is_warning),
    )


def check_cel_condition_set(
    conditions: Sequence[str | CelExpr],
    registry: Mapping[str, ConceptInfo],
) -> CheckedCelConditionSet:
    """Parse, type-check, deduplicate, and sort a conjunction of CEL conditions."""
    checked = [
        check_cel_expr(condition, registry)
        for condition in conditions
    ]
    if not checked:
        return CheckedCelConditionSet(
            conditions=(),
            registry_fingerprint=cel_registry_fingerprint(registry),
        )
    return checked_condition_set(checked)


def _resolve_type(node: ASTNode, expr: str, registry: Mapping[str, ConceptInfo], errors: list[CelError]) -> ExprType:
    """Determine the type of an AST node and accumulate errors."""
    if isinstance(node, LiteralNode):
        if node.lit_type in ("int", "float"):
            return ExprType.NUMERIC
        if node.lit_type == "string":
            return ExprType.STRING
        if node.lit_type == "bool":
            return ExprType.BOOLEAN
        return ExprType.UNKNOWN

    if isinstance(node, NameNode):
        info = registry.get(node.name)
        if info is None:
            errors.append(CelError(expr, f"Undefined concept: '{node.name}'"))
            return ExprType.UNKNOWN
        if info.kind == KindType.STRUCTURAL:
            errors.append(CelError(expr, f"Structural concept '{node.name}' cannot appear in CEL expressions"))
            return ExprType.UNKNOWN
        if info.kind in (KindType.QUANTITY, KindType.TIMEPOINT):
            return ExprType.NUMERIC
        if info.kind == KindType.CATEGORY:
            return ExprType.STRING
        if info.kind == KindType.BOOLEAN:
            return ExprType.BOOLEAN
        return ExprType.UNKNOWN

    if isinstance(node, UnaryOpNode):
        if node.op == "!":
            inner = _resolve_type(node.operand, expr, registry, errors)
            if inner == ExprType.NUMERIC:
                errors.append(CelError(expr, "Cannot negate a numeric expression with '!'"))
            return ExprType.BOOLEAN
        if node.op == "-":
            inner = _resolve_type(node.operand, expr, registry, errors)
            if inner == ExprType.STRING:
                errors.append(CelError(expr, "Cannot negate a string expression"))
            if inner == ExprType.BOOLEAN:
                errors.append(CelError(expr, "Cannot negate a boolean expression with unary minus"))
            return ExprType.NUMERIC

    if isinstance(node, BinaryOpNode):
        return _check_binary(node, expr, registry, errors)

    if isinstance(node, InNode):
        return _check_in(node, expr, registry, errors)

    if isinstance(node, TernaryNode):
        _check_node(node.condition, expr, registry, errors)
        t1 = _resolve_type(node.true_branch, expr, registry, errors)
        _resolve_type(node.false_branch, expr, registry, errors)
        return t1

    return ExprType.UNKNOWN


def _check_binary(node: BinaryOpNode, expr: str, registry: Mapping[str, ConceptInfo], errors: list[CelError]) -> ExprType:
    left_type = _resolve_type(node.left, expr, registry, errors)
    right_type = _resolve_type(node.right, expr, registry, errors)

    if node.op in LOGICAL_OPS:
        # Both sides must be boolean-compatible
        _bool_compatible = {ExprType.BOOLEAN, ExprType.UNKNOWN}
        if left_type not in _bool_compatible:
            errors.append(CelError(expr, f"Left operand of '{node.op}' must be boolean, got {left_type.value}"))
        if right_type not in _bool_compatible:
            errors.append(CelError(expr, f"Right operand of '{node.op}' must be boolean, got {right_type.value}"))
        return ExprType.BOOLEAN

    if node.op in ARITHMETIC_OPS:
        _check_disallowed_kind_usage(
            node.left, expr, registry, errors, operation_class="arithmetic"
        )
        _check_disallowed_kind_usage(
            node.right, expr, registry, errors, operation_class="arithmetic"
        )
        return ExprType.NUMERIC

    if node.op in ORDERING_OPS:
        _check_disallowed_kind_usage(
            node.left, expr, registry, errors, operation_class="ordering comparison"
        )
        _check_disallowed_kind_usage(
            node.right, expr, registry, errors, operation_class="ordering comparison"
        )
        _check_comparison_type_mismatch(
            node.left,
            node.right,
            left_type,
            right_type,
            expr,
            registry,
            errors,
        )
        return ExprType.BOOLEAN

    if node.op in EQUALITY_OPS:
        _check_comparison_type_mismatch(
            node.left,
            node.right,
            left_type,
            right_type,
            expr,
            registry,
            errors,
        )
        # Check category value sets
        _check_category_value(node.left, node.right, expr, registry, errors)
        _check_category_value(node.right, node.left, expr, registry, errors)
        return ExprType.BOOLEAN

    return ExprType.UNKNOWN


def _check_in(node: InNode, expr: str, registry: Mapping[str, ConceptInfo], errors: list[CelError]) -> ExprType:
    """Type-check 'x in [a, b, c]'."""
    _resolve_type(node.expr, expr, registry, errors)

    # Check if the LHS is a category concept — validate values against value set
    if isinstance(node.expr, NameNode):
        info = registry.get(node.expr.name)
        if info and info.kind == KindType.CATEGORY:
            for val_node in node.values:
                if isinstance(val_node, LiteralNode) and val_node.lit_type == "string":
                    if val_node.value not in info.category_values:
                        if info.category_extensible:
                            errors.append(CelError(
                                expr,
                                f"Value '{val_node.value}' not in value set for category concept '{node.expr.name}' (extensible, may be valid)",
                                is_warning=True,
                            ))
                        else:
                            errors.append(CelError(
                                expr,
                                f"Value '{val_node.value}' not in value set for category concept '{node.expr.name}'",
                            ))
        if info and info.kind == KindType.BOOLEAN:
            errors.append(CelError(expr, f"Boolean concept '{node.expr.name}' cannot be used with 'in' operator"))
        if info and info.kind in (KindType.QUANTITY, KindType.TIMEPOINT):
            # quantity/timepoint in [...] is ok for numeric lists
            for val_node in node.values:
                if isinstance(val_node, LiteralNode) and val_node.lit_type == "string":
                    errors.append(CelError(expr, f"String literal in 'in' list for quantity concept '{node.expr.name}'"))

    return ExprType.BOOLEAN


def _check_node(node: ASTNode, expr: str, registry: Mapping[str, ConceptInfo], errors: list[CelError]) -> None:
    """Top-level check — just resolves type and accumulates errors."""
    _resolve_type(node, expr, registry, errors)


def _check_disallowed_kind_usage(
    node: ASTNode,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
    *,
    operation_class: str,
) -> None:
    if isinstance(node, NameNode):
        info = registry.get(node.name)
        message_template = (
            None
            if info is None
            else _DISALLOWED_KIND_USAGE.get(operation_class, {}).get(info.kind)
        )
        if message_template is not None:
            errors.append(CelError(expr, message_template.format(name=node.name)))


def _check_comparison_type_mismatch(
    left: ASTNode,
    right: ASTNode,
    left_type: ExprType,
    right_type: ExprType,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
) -> None:
    """Check that comparison operands are type-compatible."""
    if left_type in {ExprType.UNKNOWN} or right_type in {ExprType.UNKNOWN}:
        return
    if left_type == right_type:
        return
    if not isinstance(left, NameNode) and not isinstance(right, NameNode):
        return

    if _check_concept_literal_type_mismatch(
        left,
        right,
        right_type,
        expr,
        registry,
        errors,
    ):
        return
    if _check_concept_literal_type_mismatch(
        right,
        left,
        left_type,
        expr,
        registry,
        errors,
    ):
        return

    left_name = left.name if isinstance(left, NameNode) else None
    right_name = right.name if isinstance(right, NameNode) else None
    left_info = registry.get(left_name) if left_name is not None else None
    right_info = registry.get(right_name) if right_name is not None else None
    if left_info is not None and right_info is not None:
        errors.append(
            CelError(
                expr,
                "Cannot compare "
                f"{left_info.kind.value} concept '{left_name}' "
                f"to {right_info.kind.value} concept '{right_name}'",
            )
        )
        return

    errors.append(
        CelError(
            expr,
            f"Type mismatch: cannot compare {left_type.value} to {right_type.value}",
        )
    )


def _check_concept_literal_type_mismatch(
    concept_node: ASTNode,
    other_node: ASTNode,
    other_type: ExprType,
    expr: str,
    registry: Mapping[str, ConceptInfo],
    errors: list[CelError],
) -> bool:
    """Check that a concept isn't being compared to a mismatched literal type."""
    if not isinstance(concept_node, NameNode) or not isinstance(other_node, LiteralNode):
        return False
    info = registry.get(concept_node.name)
    if info is None:
        return False

    if info.kind in (KindType.QUANTITY, KindType.TIMEPOINT) and other_type == ExprType.STRING:
        errors.append(CelError(expr, f"Quantity concept '{concept_node.name}' compared to string literal"))
        return True
    if info.kind == KindType.CATEGORY and other_type == ExprType.NUMERIC:
        errors.append(CelError(expr, f"Category concept '{concept_node.name}' compared to numeric literal"))
        return True
    if info.kind == KindType.BOOLEAN and other_type == ExprType.STRING:
        errors.append(CelError(expr, f"Boolean concept '{concept_node.name}' compared to string literal"))
        return True
    if info.kind == KindType.BOOLEAN and other_type == ExprType.NUMERIC:
        errors.append(CelError(expr, f"Boolean concept '{concept_node.name}' compared to numeric literal"))
        return True
    return False


def _check_category_value(concept_node: ASTNode, value_node: ASTNode, expr: str, registry: Mapping[str, ConceptInfo], errors: list[CelError]) -> None:
    """If concept_node is a category and value_node is a string literal, check the value set."""
    if not isinstance(concept_node, NameNode) or not isinstance(value_node, LiteralNode):
        return
    if value_node.lit_type != "string":
        return
    info = registry.get(concept_node.name)
    if info is None or info.kind != KindType.CATEGORY:
        return

    if value_node.value not in info.category_values:
        if info.category_extensible:
            errors.append(CelError(
                expr,
                f"Value '{value_node.value}' not in value set for category concept '{concept_node.name}' (extensible, may be valid)",
                is_warning=True,
            ))
        else:
            errors.append(CelError(
                expr,
                f"Value '{value_node.value}' not in value set for category concept '{concept_node.name}'",
            ))
