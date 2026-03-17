from __future__ import annotations

import dataclasses
import mimetypes
from pathlib import Path  # noqa: TC003
from uuid import uuid4

_MAX_FILENAME_LENGTH: int = 240


def _truncate_name(path: Path) -> str:
    if len(path.name) <= _MAX_FILENAME_LENGTH:
        return path.name

    max_bytes = _MAX_FILENAME_LENGTH - len(path.suffix) - 2
    new_stem = path.name.encode("utf-8")[:max_bytes].decode("utf-8", "ignore")
    return f"{new_stem}..{path.suffix}"


@dataclasses.dataclass(slots=True, eq=False)
class Chunk:
    data: bytes
    index: int
    total: int
    offset: int


@dataclasses.dataclass(slots=True, kw_only=True)
class FileUpload:
    path: Path
    name: str
    upload_name: str
    size: int
    mimetype: str
    uuid: str
    album_id: str | None = None

    @staticmethod
    def create(path: Path, /, size: int | None = None) -> FileUpload:
        if size is None:
            size = path.stat().st_size

        return FileUpload(
            path=path,
            name=path.name,
            upload_name=_truncate_name(path),
            size=size,
            mimetype=mimetypes.guess_type(path)[0] or "application/octet-stream",
            uuid=str(uuid4()),
        )
