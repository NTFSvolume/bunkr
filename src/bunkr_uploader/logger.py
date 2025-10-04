from __future__ import annotations

import logging

# from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

if TYPE_CHECKING:
    from bunkr_uploader.client import FileUploadResult

_CONSOLE_THEME = Theme(
    {
        "logging.level.warning": "yellow",
        "logging.level.debug": "blue",
        "logging.level.info": "white",
        "logging.level.error": "red",
    }
)
_CONSOLE = Console(theme=_CONSOLE_THEME)
_CONSOLE_CONFIG: dict = {
    "show_time": False,
    "rich_tracebacks": False,
    "tracebacks_show_locals": False,
}
_FILE_CONFIG: dict = {
    "show_time": True,
    "rich_tracebacks": True,
    "tracebacks_show_locals": True,
}


def setup_logger(name: str) -> None:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    console_handler = RichHandler(**_CONSOLE_CONFIG, level=20, console=_CONSOLE)
    logger.addHandler(console_handler)

    project_folder = Path(__file__).parent
    log_folder = project_folder / "logs"
    log_folder.mkdir(exist_ok=True)
    log_file_path = log_folder / project_folder.with_suffix(".log").name
    log_file_path.unlink(missing_ok=True)
    file_handler = RichHandler(
        **_FILE_CONFIG,
        level=logging.DEBUG,
        console=Console(file=log_file_path.open("a", encoding="utf8"), width=280),
    )
    logger.addHandler(file_handler)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        result: FileUploadResult = cast("FileUploadResult", record.msg)
        return result.dumps()


json_logger = logging.getLogger("bunkr_output_json")
json_file_handler = logging.FileHandler(Path("bunkr_upload.json"))
json_file_handler.setFormatter(JsonFormatter())
json_logger.addHandler(json_file_handler)
json_logger.setLevel(10)
