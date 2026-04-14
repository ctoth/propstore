from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from functools import lru_cache
from typing import cast

from lark import Lark, Transformer, UnexpectedInput
from lark.exceptions import VisitError
from lark.tree import Tree


class EquationFailureCode(StrEnum):
    MISSING_VARIABLES = "missing_variables"
    MISSING_EQUATION_TEXT = "missing_equation_text"
    INVALID_RELATION = "invalid_relation"
    UNKNOWN_SYMBOL = "unknown_symbol"
    PARSE_ERROR = "parse_error"
    UNSUPPORTED_SURFACE = "unsupported_surface"
    SYMPY_UNAVAILABLE = "sympy_unavailable"


@dataclass(frozen=True)
class EquationFailure:
    code: EquationFailureCode
    detail: str


@dataclass(frozen=True)
class EquationSymbolBinding:
    symbol: str
    concept_id: str
    role: str | None = None


@dataclass(frozen=True)
class NumberExpr:
    token: str


@dataclass(frozen=True)
class SymbolExpr:
    symbol: str
    concept_id: str


@dataclass(frozen=True)
class UnaryExpr:
    operator: str
    operand: EquationExpr


@dataclass(frozen=True)
class BinaryExpr:
    operator: str
    left: EquationExpr
    right: EquationExpr


@dataclass(frozen=True)
class FunctionExpr:
    name: str
    arguments: tuple[EquationExpr, ...]


type EquationExpr = NumberExpr | SymbolExpr | UnaryExpr | BinaryExpr | FunctionExpr


@dataclass(frozen=True)
class ParsedEquation:
    lhs: EquationExpr
    rhs: EquationExpr
    source_text: str


_GRAMMAR = r"""
?start: expr

?expr: sum

?sum: product
    | sum "+" product -> add
    | sum "-" product -> sub

?product: power
    | product "*" power -> mul
    | product "/" power -> div

?power: unary
    | unary "^" power -> pow

?unary: "+" unary -> pos
    | "-" unary -> neg
    | atom

?atom: NUMBER -> number
    | NAME "(" [arguments] ")" -> function
    | NAME -> symbol
    | "(" expr ")"

arguments: expr ("," expr)*

NAME: /[A-Za-z][A-Za-z0-9_]*/
NUMBER: /(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][+-]?\d+)?/

%import common.WS_INLINE
%ignore WS_INLINE
"""

_ALLOWED_FUNCTIONS = frozenset({"log", "ln", "exp", "sqrt"})


class _EquationTransformer(Transformer):
    def __init__(self, bindings: dict[str, EquationSymbolBinding]) -> None:
        super().__init__()
        self._bindings = bindings

    def number(self, items: list[object]) -> EquationExpr:
        return NumberExpr(token=str(items[0]))

    def symbol(self, items: list[object]) -> EquationExpr:
        name = str(items[0])
        binding = self._bindings.get(name)
        if binding is None:
            raise ValueError(f"unknown symbol: {name}")
        return SymbolExpr(symbol=name, concept_id=binding.concept_id)

    def function(self, items: list[object]) -> EquationExpr:
        name = str(items[0])
        if name not in _ALLOWED_FUNCTIONS:
            raise NotImplementedError(f"unsupported function: {name}")
        args: tuple[EquationExpr, ...]
        if len(items) == 1:
            args = ()
        else:
            raw_args = items[1]
            if isinstance(raw_args, tuple):
                args = tuple(
                    item
                    for item in raw_args
                    if isinstance(item, _EXPR_TYPES)
                )
            elif isinstance(raw_args, _EXPR_TYPES):
                args = (raw_args,)
            else:
                args = ()
        if len(args) != 1:
            raise ValueError(f"function {name} expects exactly one argument")
        return FunctionExpr(name=name, arguments=args)

    def arguments(self, items: list[object]) -> tuple[EquationExpr, ...]:
        return tuple(item for item in items if isinstance(item, _EXPR_TYPES))

    def add(self, items: list[EquationExpr]) -> EquationExpr:
        return BinaryExpr(operator="+", left=items[0], right=items[1])

    def sub(self, items: list[EquationExpr]) -> EquationExpr:
        return BinaryExpr(operator="-", left=items[0], right=items[1])

    def mul(self, items: list[EquationExpr]) -> EquationExpr:
        return BinaryExpr(operator="*", left=items[0], right=items[1])

    def div(self, items: list[EquationExpr]) -> EquationExpr:
        return BinaryExpr(operator="/", left=items[0], right=items[1])

    def pow(self, items: list[EquationExpr]) -> EquationExpr:
        return BinaryExpr(operator="^", left=items[0], right=items[1])

    def pos(self, items: list[EquationExpr]) -> EquationExpr:
        return UnaryExpr(operator="+", operand=items[0])

    def neg(self, items: list[EquationExpr]) -> EquationExpr:
        return UnaryExpr(operator="-", operand=items[0])


_EXPR_TYPES = (NumberExpr, SymbolExpr, UnaryExpr, BinaryExpr, FunctionExpr)


@lru_cache(maxsize=1)
def _expression_parser() -> Lark:
    return Lark(_GRAMMAR, parser="lalr", maybe_placeholders=False)


def parse_equation(
    source_text: str,
    bindings: tuple[EquationSymbolBinding, ...],
) -> ParsedEquation | EquationFailure:
    relation = split_equation_relation(source_text)
    if isinstance(relation, EquationFailure):
        return relation
    lhs_text, rhs_text = relation
    binding_map = {binding.symbol: binding for binding in bindings}
    lhs = _parse_expression(lhs_text, binding_map)
    if isinstance(lhs, EquationFailure):
        return lhs
    rhs = _parse_expression(rhs_text, binding_map)
    if isinstance(rhs, EquationFailure):
        return rhs
    return ParsedEquation(lhs=lhs, rhs=rhs, source_text=source_text.strip())


def split_equation_relation(source_text: str) -> tuple[str, str] | EquationFailure:
    text = source_text.strip()
    if not text:
        return EquationFailure(
            code=EquationFailureCode.MISSING_EQUATION_TEXT,
            detail="equation text is empty",
        )
    if any(token in text for token in ("==", "<=", ">=", "<", ">")):
        return EquationFailure(
            code=EquationFailureCode.INVALID_RELATION,
            detail="equation must contain exactly one '=' and no other relation operators",
        )
    if text.count("=") != 1:
        return EquationFailure(
            code=EquationFailureCode.INVALID_RELATION,
            detail="equation must contain exactly one '=' and no other relation operators",
        )
    lhs, rhs = text.split("=", 1)
    if not lhs.strip() or not rhs.strip():
        return EquationFailure(
            code=EquationFailureCode.PARSE_ERROR,
            detail="equation must have non-empty left and right sides",
        )
    return lhs.strip(), rhs.strip()


def render_equation(expression: EquationExpr) -> str:
    return _render_expression(expression, parent_precedence=0)


def normalized_number_token(token: str) -> str:
    if "." in token or "e" in token.lower():
        return format(Decimal(token).normalize(), "f").rstrip("0").rstrip(".") or "0"
    return str(int(token))


def structural_signature(expression: EquationExpr) -> str:
    names: dict[str, str] = {}
    counter = 0

    def assign(symbol: str) -> str:
        nonlocal counter
        placeholder = names.get(symbol)
        if placeholder is None:
            placeholder = f"v{counter}"
            names[symbol] = placeholder
            counter += 1
        return placeholder

    def build(node: EquationExpr) -> str:
        if isinstance(node, NumberExpr):
            return f"num:{normalized_number_token(node.token)}"
        if isinstance(node, SymbolExpr):
            return f"sym:{assign(node.symbol)}"
        if isinstance(node, UnaryExpr):
            return f"unary:{node.operator}({build(node.operand)})"
        if isinstance(node, BinaryExpr):
            return f"bin:{node.operator}({build(node.left)},{build(node.right)})"
        if isinstance(node, FunctionExpr):
            args = ",".join(build(argument) for argument in node.arguments)
            return f"fn:{node.name}({args})"
        raise TypeError(f"unsupported node: {node!r}")

    return build(expression)


def _parse_expression(
    text: str,
    bindings: dict[str, EquationSymbolBinding],
) -> EquationExpr | EquationFailure:
    try:
        tree = cast(Tree[object], _expression_parser().parse(text))
        return cast(EquationExpr, _EquationTransformer(bindings).transform(tree))
    except UnexpectedInput as exc:
        return EquationFailure(
            code=EquationFailureCode.PARSE_ERROR,
            detail=f"parse error: {exc.__class__.__name__}",
        )
    except ValueError as exc:
        return EquationFailure(
            code=EquationFailureCode.UNKNOWN_SYMBOL,
            detail=str(exc),
        )
    except NotImplementedError as exc:
        return EquationFailure(
            code=EquationFailureCode.UNSUPPORTED_SURFACE,
            detail=str(exc),
        )
    except VisitError as exc:
        original = exc.orig_exc
        if isinstance(original, ValueError):
            return EquationFailure(
                code=EquationFailureCode.UNKNOWN_SYMBOL,
                detail=str(original),
            )
        if isinstance(original, NotImplementedError):
            return EquationFailure(
                code=EquationFailureCode.UNSUPPORTED_SURFACE,
                detail=str(original),
            )
        return EquationFailure(
            code=EquationFailureCode.PARSE_ERROR,
            detail=f"parse error: {original.__class__.__name__}",
        )


def _precedence(expression: EquationExpr) -> int:
    if isinstance(expression, BinaryExpr):
        if expression.operator in {"+", "-"}:
            return 1
        if expression.operator in {"*", "/"}:
            return 2
        if expression.operator == "^":
            return 3
    if isinstance(expression, UnaryExpr):
        return 4
    return 5


def _render_expression(expression: EquationExpr, parent_precedence: int) -> str:
    if isinstance(expression, NumberExpr):
        return normalized_number_token(expression.token)
    if isinstance(expression, SymbolExpr):
        return expression.symbol
    if isinstance(expression, FunctionExpr):
        args = ", ".join(_render_expression(arg, 0) for arg in expression.arguments)
        return f"{expression.name}({args})"
    if isinstance(expression, UnaryExpr):
        text = f"{expression.operator}{_render_expression(expression.operand, _precedence(expression))}"
        return f"({text})" if _precedence(expression) < parent_precedence else text
    if isinstance(expression, BinaryExpr):
        precedence = _precedence(expression)
        left = _render_expression(expression.left, precedence)
        right_parent = precedence + (1 if expression.operator == "^" else 0)
        right = _render_expression(expression.right, right_parent)
        text = f"{left} {expression.operator} {right}"
        return f"({text})" if precedence < parent_precedence else text
    raise TypeError(f"unsupported node: {expression!r}")
