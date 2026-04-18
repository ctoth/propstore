"""Read-only virtual paths over semantic knowledge trees."""

from __future__ import annotations

from abc import ABC, abstractmethod
from io import BytesIO, StringIO
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, BinaryIO, Iterator, Protocol, Self, TextIO

if TYPE_CHECKING:
    from propstore.storage.git_backend import GitStore


class KnowledgePath(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def stem(self) -> str: ...

    @property
    def suffix(self) -> str: ...

    @property
    def parent(self) -> KnowledgePath: ...

    def joinpath(self, *parts: str) -> KnowledgePath: ...
    def __truediv__(self, part: str) -> KnowledgePath: ...
    def exists(self) -> bool: ...
    def is_dir(self) -> bool: ...
    def is_file(self) -> bool: ...
    def iterdir(self) -> Iterator[KnowledgePath]: ...
    def read_bytes(self) -> bytes: ...
    def read_text(self, encoding: str = "utf-8") -> str: ...
    def open(self, mode: str = "r", encoding: str = "utf-8") -> TextIO | BinaryIO: ...
    def as_posix(self) -> str: ...
    def cache_key(self) -> str: ...


class _BaseKnowledgePath(ABC):
    def __init__(self, relative_path: PurePosixPath | None = None) -> None:
        self._relative_path = PurePosixPath() if relative_path is None else relative_path

    @property
    def name(self) -> str:
        return self._relative_path.name

    @property
    def stem(self) -> str:
        return self._relative_path.stem

    @property
    def suffix(self) -> str:
        return self._relative_path.suffix

    @property
    def parent(self) -> Self:
        if not self._relative_path.parts:
            return self
        return self._with_relative_path(self._relative_path.parent)

    def joinpath(self, *parts: str) -> Self:
        path = self._relative_path
        for part in parts:
            path /= PurePosixPath(str(part).replace("\\", "/"))
        return self._with_relative_path(path)

    def __truediv__(self, part: str) -> Self:
        return self.joinpath(part)

    def read_text(self, encoding: str = "utf-8") -> str:
        return self.read_bytes().decode(encoding)

    def open(self, mode: str = "r", encoding: str = "utf-8") -> TextIO | BinaryIO:
        if mode == "rb":
            return BytesIO(self.read_bytes())
        if mode == "r":
            return StringIO(self.read_text(encoding=encoding))
        raise ValueError(f"KnowledgePath.open only supports 'r' and 'rb', got {mode!r}")

    def as_posix(self) -> str:
        if not self._relative_path.parts:
            return ""
        return self._relative_path.as_posix()

    @abstractmethod
    def cache_key(self) -> str: ...

    @abstractmethod
    def _with_relative_path(self, path: PurePosixPath) -> Self: ...

    @abstractmethod
    def exists(self) -> bool: ...

    @abstractmethod
    def is_dir(self) -> bool: ...

    @abstractmethod
    def is_file(self) -> bool: ...

    @abstractmethod
    def iterdir(self) -> Iterator[Self]: ...

    @abstractmethod
    def read_bytes(self) -> bytes: ...


class FilesystemKnowledgePath(_BaseKnowledgePath):
    @classmethod
    def from_filesystem_path(cls, path: Path) -> FilesystemKnowledgePath:
        absolute = path.resolve()
        anchor = Path(absolute.anchor)
        relative_path = PurePosixPath(*absolute.relative_to(anchor).parts)
        return cls(anchor, relative_path)

    def __init__(
        self,
        root: Path,
        relative_path: PurePosixPath | None = None,
    ) -> None:
        super().__init__(relative_path)
        self._root = root

    def _with_relative_path(self, path: PurePosixPath) -> FilesystemKnowledgePath:
        return FilesystemKnowledgePath(self._root, path)

    def _absolute_path(self) -> Path:
        path = self._root
        if self._relative_path.parts:
            path /= Path(*self._relative_path.parts)
        return path

    def concrete_path(self) -> Path:
        return self._absolute_path()

    def cache_key(self) -> str:
        return f"fs:{self._absolute_path().resolve().as_posix()}"

    def exists(self) -> bool:
        return self._absolute_path().exists()

    def is_dir(self) -> bool:
        return self._absolute_path().is_dir()

    def is_file(self) -> bool:
        return self._absolute_path().is_file()

    def iterdir(self) -> Iterator[FilesystemKnowledgePath]:
        path = self._absolute_path()
        if not path.is_dir():
            raise NotADirectoryError(self.as_posix())
        for child in sorted(path.iterdir(), key=lambda entry: entry.name):
            yield self / child.name

    def read_bytes(self) -> bytes:
        path = self._absolute_path()
        if not path.is_file():
            raise FileNotFoundError(self.as_posix())
        return path.read_bytes()


class GitKnowledgePath(_BaseKnowledgePath):
    def __init__(
        self,
        repo: GitStore,
        commit: str | None = None,
        relative_path: PurePosixPath | None = None,
    ) -> None:
        super().__init__(relative_path)
        self._repo = repo
        self._commit = commit

    def _with_relative_path(self, path: PurePosixPath) -> GitKnowledgePath:
        return GitKnowledgePath(self._repo, self._commit, path)

    def exists(self) -> bool:
        return self.is_dir() or self.is_file()

    def is_dir(self) -> bool:
        if not self._relative_path.parts:
            return True
        return len(self._repo.list_dir_entries(self.as_posix(), commit=self._commit)) > 0

    def is_file(self) -> bool:
        try:
            self._repo.read_file(self.as_posix(), commit=self._commit)
        except (FileNotFoundError, KeyError):
            return False
        return True

    def iterdir(self) -> Iterator[GitKnowledgePath]:
        entries = self._repo.list_dir_entries(self.as_posix(), commit=self._commit)
        if not self.is_dir():
            raise NotADirectoryError(self.as_posix())
        for name, _is_dir in entries:
            yield self / name

    def read_bytes(self) -> bytes:
        return self._repo.read_file(self.as_posix(), commit=self._commit)

    def cache_key(self) -> str:
        commit = self._commit or "WORKTREE"
        repo_root = self._repo.root
        if repo_root is None:
            raise ValueError("GitKnowledgePath cache keys require a filesystem-backed GitStore")
        return f"git:{repo_root.resolve().as_posix()}:{commit}:{self.as_posix()}"


def coerce_knowledge_path(path: KnowledgePath | Path) -> KnowledgePath:
    if isinstance(path, Path):
        return FilesystemKnowledgePath.from_filesystem_path(path)
    return path
