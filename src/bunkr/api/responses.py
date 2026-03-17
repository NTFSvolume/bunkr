# ruff: noqa: N815
import dataclasses
from datetime import datetime, timedelta
from typing import Annotated

import yarl
from pydantic import BaseModel, ByteSize, HttpUrl, PlainValidator

HttpURL = Annotated[yarl.URL, PlainValidator(lambda url: yarl.URL(str(HttpUrl(url))))]


@dataclasses.dataclass(slots=True)
class ChunkSize:
    max: ByteSize
    default: ByteSize
    timeout: timedelta


@dataclasses.dataclass(slots=True)
class FileIDLimits:
    min: int
    max: int
    default: int
    force: bool


@dataclasses.dataclass(slots=True)
class StripTags:
    blacklistExtensions: set[str]
    default: bool
    force: bool
    video: bool


@dataclasses.dataclass(slots=True)
class Permissions:
    admin: bool
    moderator: bool
    superadmin: bool
    user: bool
    vip: bool
    vvip: bool


@dataclasses.dataclass(slots=True)
class AlbumResponse:
    descriptionHtml: str
    download: bool
    editedAt: datetime
    enabled: bool
    id: int
    identifier: str
    name: str
    public: bool
    size: ByteSize
    timestamp: datetime
    uploads: int
    zipGeneratedAt: datetime
    zipSize: ByteSize | None


class _Response(BaseModel, populate_by_name=True, defer_build=True):
    description: str = ""
    success: bool = True


class FileResponse(_Response):
    name: str
    url: HttpURL | None

    def model_post_init(self, *_) -> None:
        if self.url is None:
            self.success = False


class UploadResponse(_Response):
    files: list[FileResponse] = []


class CreateAlbumResponse(_Response):
    id: int


class VerifyTokenResponse(_Response):
    defaultRetentionPeriod: timedelta
    group: str
    permissions: Permissions
    retentionPeriods: list[timedelta]
    username: str


class InfoResponse(_Response):
    chunkSize: ChunkSize
    defaultTemporaryUploadAge: int
    enableUserAccounts: bool
    fileIdentifierLength: FileIDLimits
    maintenance: bool
    maxSize: ByteSize
    private: bool
    stripTags: StripTags
    temporaryUploadAges: list[int]


class NodeResponse(_Response):
    url: HttpURL
