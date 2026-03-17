import asyncio
import dataclasses
import itertools
import logging
from collections.abc import AsyncGenerator, Mapping
from json import dumps as json_dumps
from typing import Any, Self

from aiohttp import ClientSession, ClientTimeout, FormData
from multidict import CIMultiDict
from pydantic.type_adapter import TypeAdapter
from yarl import URL

from bunkr.api.album import Album
from bunkr.api.errors import ChunkUploadError, FileUploadError
from bunkr.api.responses import (
    AlbumResponse,
    CreateAlbumResponse,
    InfoResponse,
    NodeResponse,
    UploadResponse,
    VerifyTokenResponse,
)
from bunkr.api.upload import Chunk, FileUpload

_API_ENTRYPOINT = URL("https://dash.bunkr.cr/api/")
_SEMAPHORE = asyncio.Semaphore(50)
_parse_albums = TypeAdapter(list[AlbumResponse]).validate_python

logger = logging.getLogger(__name__)


@dataclasses.dataclass(slots=True)
class BunkrAPI:
    _token: str | None = None
    _chunk_size: int = 0
    _session: ClientSession | None = dataclasses.field(init=False, default=None)
    _info: InfoResponse | None = dataclasses.field(init=False, default=None)

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    async def connect(self) -> None:
        info = await self.check()
        self._chunk_size = self.chunk_size or info.chunkSize.max
        if self._chunk_size > info.chunkSize.max:
            msg = f"Chunk size is too high. Using max chunksize ({info.chunkSize.max.human_readable(decimal=True)})"
            logger.warning(msg)
            self._chunk_size = info.chunkSize.max

        if self._token:
            _ = await self.verify_token(self._token)

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._session is not None:
            await self._session.close()

    @property
    def session(self) -> ClientSession:
        if self._session is None:
            self._session = ClientSession(
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
                    "Referer": "https://dash.bunkr.cr/",
                    "striptags": "null",
                    "Origin": "https://dash.bunkr.cr",
                },
                raise_for_status=True,
                timeout=ClientTimeout(sock_connect=30, sock_read=20),
            )
        return self._session

    async def _request_json(
        self,
        path_or_url: URL | str,
        *,
        form: FormData | None = None,
        headers: Mapping[str, str] | None = None,
        **json: Any,
    ) -> dict[str, Any]:
        method = "POST" if (form or json) else "GET"
        url = _API_ENTRYPOINT / path_or_url if isinstance(path_or_url, str) else path_or_url

        async with (
            _SEMAPHORE,
            self.session.request(
                method,
                url,
                data=form,
                json=json or None,
                headers=self._prepare_json_headers(headers),
            ) as resp,
        ):
            data = await resp.json()
            record = {
                "url": resp.url,
                "headers": dict(resp.headers),
                "data": data,
            }
            logger.debug(json_dumps(record, indent=4, default=str))

            return data

    def _prepare_json_headers(self, headers: Mapping[str, str] | None = None) -> CIMultiDict[str]:
        """Add default headers and transform it to CIMultiDict"""
        if not self._token:
            raise RuntimeError
        combined = CIMultiDict(token=self._token, Accept="application/json, text/plain")
        if headers:
            headers = CIMultiDict(headers)
            new: set[str] = set()
            for key, value in headers.items():
                if key in new:
                    combined.add(key, value)
                else:
                    combined[key] = value
                    new.add(key)
        return combined

    async def check(self) -> InfoResponse:
        if not self._info:
            response = await self._request_json("check")
            self._info = InfoResponse.model_validate(response)
        return self._info

    async def node(self) -> NodeResponse:
        response = await self._request_json("node")
        return NodeResponse.model_validate(response)

    async def verify_token(self, token: str) -> VerifyTokenResponse:
        response = await self._request_json("tokens/verify", token=token)
        try:
            resp = VerifyTokenResponse.model_validate(response)
        except ValueError:
            raise ValueError("Invalid Token") from None
        if not resp.success:
            raise ValueError("Invalid Token")
        return resp

    async def albums(self) -> list[AlbumResponse]:
        albums: list[AlbumResponse] = []
        async for new_albums in self.iter_albums():
            albums.extend(new_albums)
        return albums

    async def iter_albums(self) -> AsyncGenerator[list[AlbumResponse]]:
        for page in itertools.count(0):
            response = await self._request_json(f"albums/{page}")
            new_albums = _parse_albums(response["albums"])
            yield new_albums
            if len(new_albums) < 50:
                break

    async def album(self, url_or_slug: URL | str, /) -> Album:
        url = (
            URL(f"https://bunkr.cr/a/{url_or_slug}", encoded="%" in url_or_slug)
            if isinstance(url_or_slug, str)
            else url_or_slug
        )
        async with self.session.get(url.with_query(advanced=1)) as resp:
            page = await resp.text()

        return Album.parse(url.name, page)

    async def create_album(
        self,
        name: str,
        *,
        description: str = "",
        public: bool = True,
        download: bool = True,
    ) -> CreateAlbumResponse:
        response = await self._request_json(
            "albums",
            name=name,
            description=description,
            public=public,
            download=download,
        )
        return CreateAlbumResponse.model_validate(response)

    async def upload(
        self,
        file: FileUpload,
        server: URL,
        album_id: str | None = None,
    ) -> UploadResponse:
        file.album_id = album_id = file.album_id or album_id
        try:
            chunk_data = await asyncio.to_thread(file.path.read_bytes)
            form = FormData()
            form.add_field(
                "files[]",
                chunk_data,
                filename=file.path.name,
                content_type=file.mimetype,
            )
            headers = {"albumid": album_id} if album_id else None
            response = await self._request_json(server / "upload", form=form, headers=headers)

        except Exception as e:
            raise FileUploadError(file) from e

        result = UploadResponse.model_validate(response)
        if not result.success:
            raise FileUploadError(file)
        return result

    async def upload_chunk(self, file: FileUpload, server: URL, chunk: Chunk) -> None:
        try:
            form = _create_chunk_form(file, chunk, self.chunk_size)
            result = await self._request_json(server / "upload", form=form)
        except Exception as e:
            raise ChunkUploadError(file, chunk) from e

        if not result["success"]:
            raise ChunkUploadError(file, chunk)

    async def finish_chunks(
        self, file: FileUpload, server: URL, album_id: str | None = None
    ) -> UploadResponse:
        file.album_id = album_id = file.album_id or album_id

        for retry in (True, False):
            try:
                response = await self._request_json(
                    server / "upload/finishchunks",
                    files=[
                        {
                            "uuid": file.uuid,
                            "original": file.original_name,
                            "type": file.mimetype,
                            "albumid": album_id or None,
                            "filelength": None,
                            "age": None,
                        }
                    ],
                )
                break
            except Exception as e:
                if retry:
                    continue
                raise FileUploadError(file) from e

        else:
            raise FileUploadError(file)

        result = UploadResponse.model_validate(response)
        if not result.success:
            raise FileUploadError(file)
        return result


def _create_chunk_form(file: FileUpload, chunk: Chunk, chunk_size: int) -> FormData:
    form = FormData()
    form.add_fields(
        ("dzuuid", file.uuid),
        ("dzchunkindex", str(chunk.index)),
        ("dztotalfilesize", str(file.size)),
        ("dzchunksize", str(chunk_size)),
        ("dztotalchunkcount", str(chunk.total)),
        ("dzchunkbyteoffset", str(chunk.offset)),
    )
    form.add_field(
        "files[]",
        chunk.data,
        filename=file.upload_name,
        content_type="application/octet-stream",
    )
    return form
