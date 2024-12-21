from dataclasses import dataclass


@dataclass
class ChunkSize:
    max: str
    default: str
    timeout: int


@dataclass
class FileIdentifierLength:
    min: int
    max: int
    default: int
    force: bool


@dataclass
class StripTags:
    default: bool
    video: bool
    force: bool
    blacklist_extensions: list[str]

@dataclass
class Permissions:
    user: bool
    vip: bool
    vvip: bool
    moderator: bool
    admin: bool
    superadmin: bool


@dataclass
class File:
    name: str
    url: str

    # Properties not preset on official API
    original: str
    albumid: str
    file_path_MD5: str
    file_name_MD5: str
    upload_success: str

