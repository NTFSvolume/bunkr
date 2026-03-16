from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from bunkr.logger import CONSOLE


def new_progress() -> Progress:
    return Progress(
        SpinnerColumn(),
        "[progress.description]{task.description}",
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>6.2f}%",
        "━",
        DownloadColumn(),
        "━",
        TransferSpeedColumn(),
        "━",
        TimeRemainingColumn(),
        console=CONSOLE,
        expand=True,
        transient=True,
    )
