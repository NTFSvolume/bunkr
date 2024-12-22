from __future__ import annotations

import sys
from argparse import SUPPRESS, ArgumentDefaultsHelpFormatter, ArgumentParser, BooleanOptionalAction
from argparse import _ArgumentGroup as ArgGroup
from typing import TYPE_CHECKING

from pydantic import BaseModel, ByteSize, ConfigDict, Field, ValidationError
from rich.console import Console

from bunkrr_uploader import __version__

if TYPE_CHECKING:
    from pathlib import Path

    from rich.text import Text

ERROR_PREFIX = "\n[bold red]ERROR: [/bold red]"

console = Console()


def print_to_console(text: Text | str, *, error: bool = False, **kwargs) -> None:
    msg = (ERROR_PREFIX + text) if error else text  # type: ignore
    console.print(msg, **kwargs)


def handle_validation_error(e: ValidationError, *, title: str | None = None, sources: dict | None = None):
    error_count = e.error_count()
    source: Path = sources.get(e.title, None) if sources else None  # type: ignore
    title = title or e.title
    source = f"from {source.resolve()}" if source else ""  # type: ignore
    msg = f"found {error_count} error{'s' if error_count>1 else ''} parsing {title} {source}"
    print_to_console(msg, error=True)
    for error in e.errors(include_url=False):
        loc = ".".join(map(str, error["loc"]))
        if title == "CLI arguments":
            loc = error["loc"][-1]
            if isinstance(error["loc"][-1], int):
                loc = ".".join(map(str, error["loc"][-2:]))
            loc = f"--{loc}"
        msg = f"\nValue of '{loc}' is invalid:"
        print_to_console(msg, markup=False)
        print_to_console(
            f"  {error['msg']} (input_value='{error['input']}', input_type='{error['type']}')", style="bold red"
        )


class ParsedArgs(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    path: Path = Field(description="File or directory to look for files in to upload")
    token: str = Field(
        alias="t",
        description="API token for your account so that you can upload to a specific account/folder. You can also set the BUNKRR_TOKEN environment variable for this",
    )
    album_name: str = Field(alias="n")
    chunk_size: ByteSize = ByteSize(0)
    use_max_chunk_size: bool = Field(True, description="Use the server's maximum chunk size instead of the default one")
    concurrent_uploads: int = Field(2, alias="c", description="Maximum parallel uploads to do at once")
    public: bool = Field(True, description="Make all files uploaded public")
    config_file: Path | None = None
    upload_retries: int = Field(1, description="How many times to retry a failed upload")
    chunk_retries: int = Field(2, description="How many times to retry a failed chunk or chunk completion")

    @staticmethod
    def parse_args() -> ParsedArgs:
        """Parses the command line arguments passed into the program. Returns an instance of `ParsedArgs`"""
        return parse_args()


def _add_args_from_model(
    parser: ArgumentParser | ArgGroup, model: type[BaseModel], *, cli_args: bool = False, deprecated: bool = False
) -> None:
    for name, field in model.model_fields.items():
        cli_name = name.replace("_", "-")
        arg_type = type(field.default)
        if arg_type not in (list, set, bool):
            arg_type = str
        help_text = field.description or ""
        default = field.default if cli_args else SUPPRESS
        default_options = {"default": default, "dest": name, "help": help_text}
        name_or_flags = [f"--{cli_name}"]
        alias = field.alias or field.validation_alias or field.serialization_alias
        if alias and len(alias) == 1:  # type: ignore
            name_or_flags.insert(0, f"-{alias}")
        if arg_type is bool:
            action = BooleanOptionalAction
            default_options.pop("default")
            if cli_args:
                action = "store_false" if default else "store_true"
            if deprecated:
                default_options = default_options | {"default": SUPPRESS}
            parser.add_argument(*name_or_flags, action=action, **default_options)
            continue
        if cli_name == "links":
            default_options.pop("dest")
            parser.add_argument(cli_name, metavar="LINK(S)", nargs="*", **default_options)
            continue
        if arg_type in (list, set):
            parser.add_argument(*name_or_flags, nargs="*", **default_options)
            continue
        parser.add_argument(*name_or_flags, type=arg_type, **default_options)


def parse_args() -> ParsedArgs:
    """Parses the command line arguments passed into the program."""
    parser = ArgumentParser(
        description="Bulk asynchronous uploader for bunkrr",
        usage="bunkrr-uploader [OPTIONS] URL [URL...]",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    cli_args = parser.add_argument_group("CLI-args")
    _add_args_from_model(cli_args, ParsedArgs, cli_args=True)
    group_lists = {"cli_args": [cli_args]}
    args = parser.parse_args()
    parsed_args = {}
    for name, groups in group_lists.items():
        parsed_args[name] = {}
        for group in groups:
            group_dict = {
                arg.dest: getattr(args, arg.dest)
                for arg in group._group_actions
                if getattr(args, arg.dest, None) is not None
            }
            if group_dict:
                parsed_args[name][group.title] = group_dict

    try:
        parsed_args = ParsedArgs.model_validate(parsed_args)

    except ValidationError as e:
        handle_validation_error(e, title="CLI arguments")
        sys.exit(1)
    return parsed_args
