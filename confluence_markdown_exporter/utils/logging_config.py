"""CLI logging: console plus mandatory log file."""

from __future__ import annotations

import logging
import sys
from pathlib import Path


_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_export_logging(log_file: Path, *, debug: bool = False) -> None:
    """Send all log records to stderr and to *log_file* (UTF-8).

    Safe to call once per process; replaces existing root handlers so CLI
    output is consistent.
    """
    level = logging.DEBUG if debug else logging.INFO
    log_file = log_file.expanduser().resolve()
    log_file.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(stream_handler)
    root.addHandler(file_handler)
