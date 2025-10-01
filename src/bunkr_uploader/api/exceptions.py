from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bunkr_uploader.api.files import FileInfo


class BunkrUploaderError(Exception): ...


class FileUploadError(BunkrUploaderError):
    """Custom exception for file upload failures"""

    def __init__(self, file: FileInfo) -> None:
        self.file = file
        self.message = f"Failed to upload {self.file.path}"
        super().__init__(self.message)
