from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Self

from yarl import URL

if TYPE_CHECKING:
    from collections.abc import Generator

_FILE_ATTRS = (
    "id",
    "name",
    "original",
    "slug",
    "type",
    "extension",
    "size",
    "timestamp",
    "thumbnail",
    "cdnEndpoint",
)


_translation_map = {f" {key}: ": f'"{key}": ' for key in _FILE_ATTRS}
_find_files = re.compile("|".join(sorted(_translation_map.keys(), key=len, reverse=True))).sub


def _fix_unicode(value: str) -> str:
    return value.encode("raw_unicode_escape").decode("unicode-escape")


def _decode_files(text: str) -> Generator[File]:
    content = _find_files(lambda m: _translation_map[m.group(0)], text.replace("\\'", "'"))

    for file in json.loads(content):
        yield File(
            name=_fix_unicode(file.get("original") or file["name"]),
            slug=_fix_unicode(file["slug"]),
            thumbnail=_fix_unicode(file["thumbnail"]),
            date=file["timestamp"],
        )


@dataclasses.dataclass(slots=True, order=True)
class Album:
    id: int
    slug: str
    name: str
    files: tuple[File, ...]

    @classmethod
    def parse(cls, slug: str, html: str) -> Self:
        def extr(before: str, after: str) -> str:
            start = html.index(before) + len(before)
            end = html.index(after, start)
            return html[start:end]

        id_ = int(extr('albumID = "', '";'))
        name = extr('<meta property="og:title" content="', '">')

        album_js = extr("window.albumFiles = ", "</script>")
        files = _decode_files(album_js[: album_js.rindex("];") + 1])
        return cls(id_, slug, name, tuple(files))


@dataclasses.dataclass(slots=True)
class File:
    name: str
    thumbnail: str
    date: str
    slug: str
    src: URL | None = None

    def __post_init__(self) -> None:
        if self.thumbnail.count("https://") != 1:
            return

        if URL(self.thumbnail, encoded="%" in self.thumbnail).parts[1:2] != ("thumbs",):
            return

        src_str = self.thumbnail.replace("/thumbs/", "/")
        src = (
            URL(src_str, encoded="%" in src_str)
            .with_suffix(Path(self.name).suffix)
            .with_query(None)
        )
        if src.suffix.lower() not in _IMAGE_EXTS:
            src = src.with_host(src.host.replace("i-", ""))
        self.src = src


_IMAGE_EXTS = frozenset(
    {
        ".gif",
        ".gifv",
        ".heic",
        ".jfif",
        ".jif",
        ".jpe",
        ".jpeg",
        ".jpg",
        ".jxl",
        ".png",
        ".svg",
        ".tif",
        ".tiff",
        ".webp",
    }
)
