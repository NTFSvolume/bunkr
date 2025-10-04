import asyncio
import itertools
import json
import logging
from typing import Any, Final, Self

import aiofiles
from aiohttp import ClientResponse, ClientSession, ClientTimeout, FormData
from yarl import URL

from bunkr_uploader.api import _responses
from bunkr_uploader.api._exceptions import ChunkUploadError, FileUploadError
from bunkr_uploader.api._files import Chunk, File

_logger = logging.getLogger(__name__)
_API_ENTRYPOINT = URL("https://dash.bunkr.cr/api/")
_DEFAULT_HEADERS: dict[str, str] = {
    "Accept": "application/json, text/plain",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
    "Referer": "https://dash.bunkr.cr/",
    "striptags": "null",
    "Origin": "https://dash.bunkr.cr",
}


def _log_resp(resp: ClientResponse, response: Any) -> None:
    record = {
        "url": resp.url,
        "headers": dict(resp.headers),
        "response": response,
    }
    _logger.debug(f"response: \n {json.dumps(record, indent=4, default=str)}")


class BunkrrAPI:
    RATE_LIMIT: Final[int] = 50

    def __init__(self, token: str, chunk_size: int | None = None) -> None:
        self._token = token
        self._session_headers = _DEFAULT_HEADERS | {"token": self._token}
        self._chunk_size: int = chunk_size or 0
        self._info: _responses.Check
        self._semaphore = asyncio.Semaphore(self.RATE_LIMIT)
        self.__session: ClientSession | None = None

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    @property
    def _session(self) -> ClientSession:
        if self.__session is None:
            self.__session = ClientSession(
                _API_ENTRYPOINT,
                headers=self._session_headers,
                raise_for_status=True,
                timeout=ClientTimeout(sock_connect=30, sock_read=20),
            )
        return self.__session

    async def _request(
        self,
        path_or_url: URL | str,
        *,
        form: FormData | None = None,
        headers: dict[str, str] | None = None,
        **json: Any,
    ) -> dict[str, Any]:
        method = "POST" if (form or json) else "GET"
        headers = self._session_headers | (headers or {})

        async with (
            self._semaphore,
            self._session.request(
                method, path_or_url, data=form, json=json or None, headers=headers
            ) as resp,
        ):
            response = await resp.json()
            _log_resp(resp, response)
            return response

    async def startup(self) -> None:
        self._info = await self.check()
        self._chunk_size = self._chunk_size or self._info.chunkSize.default
        assert 0 < self._chunk_size <= self._info.chunkSize.max
        await self.verify_token()

    async def close(self) -> None:
        if self.__session is not None:
            await self.__session.close()

    async def check(self) -> _responses.Check:
        if self._info:
            return self._info
        response = await self._request("check")
        return _responses.Check.model_validate(response)

    async def node(self) -> _responses.Node:
        response = await self._request("node")
        return _responses.Node.model_validate(response)

    async def verify_token(self) -> _responses.VerifyToken:
        response = await self._request("tokens/verify", token=self._token)
        try:
            resp = _responses.VerifyToken.model_validate(response)
        except ValueError:
            raise ValueError("Invalid Token") from None
        if not resp.success:
            raise ValueError("Invalid Token")
        return resp

    async def get_albums(self) -> _responses.Albums:
        albums: list[_responses.AlbumItem] = []
        for page in itertools.count(0):
            response = await self._request(f"albums/{page}")
            new_albums = response["albums"]
            albums.extend(new_albums)
            if new_albums < 50:
                break

        return _responses.Albums.model_validate({"albums": albums, "count": len(albums)})

    async def create_album(
        self,
        name: str,
        *,
        description: str = "",
        public: bool = True,
        download: bool = True,
    ) -> _responses.CreateAlbum:
        response = await self._request(
            "albums", name=name, description=description, public=public, download=download
        )
        return _responses.CreateAlbum.model_validate(response)

    async def direct_upload(
        self, file: File, server: URL, album_id: str | None = None
    ) -> _responses.UploadResponse:
        file.album_id = album_id = file.album_id or album_id
        assert file.size <= self._info.maxSize
        try:
            async with aiofiles.open(file.path, "rb") as file_data:
                chunk_data = await file_data.read(self._chunk_size)

            form = FormData()
            form.add_field(
                "files[]", chunk_data, filename=file.path.name, content_type=file.mimetype
            )
            headers = {"albumid": album_id} if album_id else None
            response = await self._request(server / "upload", form=form, headers=headers)

        except Exception as e:
            raise FileUploadError(file) from e

        result = _responses.UploadResponse.model_validate(response)
        if not result.success:
            raise FileUploadError(file)
        return result

    async def upload_chunk(self, file: File, server: URL, chunk: Chunk) -> None:
        try:
            form = self._create_chunk_dataform(file, chunk)
            result = await self._request(server / "upload", form=form)
        except Exception as e:
            raise ChunkUploadError(file, chunk) from e

        if not result["success"]:
            raise ChunkUploadError(file, chunk)

    def _create_chunk_dataform(self, file_info: File, chunk: Chunk) -> FormData:
        form = FormData()
        form.add_fields(
            ("dzuuid", file_info.uuid),
            ("dzchunkindex", str(chunk.index)),
            ("dztotalfilesize", str(file_info.size)),
            ("dzchunksize", str(self._chunk_size)),
            ("dztotalchunkcount", str(chunk.total)),
            ("dzchunkbyteoffset", str(chunk.offset)),
        )
        form.add_field(
            "files[]",
            chunk.data,
            filename=file_info.upload_name,
            content_type="application/octet-stream",
        )
        return form

    async def finish_chunks(
        self, file: File, server: URL, album_id: str | None = None
    ) -> _responses.UploadResponse:
        file.album_id = album_id = file.album_id or album_id
        payload = {
            "uuid": file.uuid,
            "original": file.original_name,
            "type": file.mimetype,
            "albumid": album_id or None,
            "filelength": None,
            "age": None,
        }
        for _ in range(2):
            try:
                response = await self._request(server / "upload/finishchunks", files=[payload])
                break
            except Exception:
                _logger.exception("")
                continue
        else:
            raise FileUploadError(file)

        result = _responses.UploadResponse.model_validate(response)
        if not result.success:
            raise FileUploadError(file)
        return result


__all__ = ["BunkrrAPI"]
