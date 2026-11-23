"""Output handling shared by the offline command-line tools."""

import json
import os
import stat
import sys
from argparse import ArgumentParser
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

from state import StateError


def json_text(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def abort(parser: ArgumentParser, error: OSError | StateError) -> None:
    message = error.strerror if isinstance(error, OSError) else str(error)
    parser.exit(1, f"{parser.prog}: {message}\n")


def print_text(content: str) -> None:
    output = getattr(sys.stdout, "buffer", None)
    if output is None:
        sys.stdout.write(content)
    else:
        output.write(content.encode("utf-8", errors="backslashreplace"))


def is_link(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


@contextmanager
def temporary_file(destination: Path, content: bytes):
    file = NamedTemporaryFile(dir=destination.parent, prefix=".assumption-hunter-", delete=False)
    temporary = Path(file.name)
    try:
        with file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        yield temporary
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write(destination: Path, content: bytes, *, replace: bool = False) -> None:
    with temporary_file(destination, content) as temporary:
        if replace:
            os.replace(temporary, destination)
        elif os.name == "nt":
            # Windows rename fails when the destination already exists.
            os.rename(temporary, destination)
        else:
            # Publish a fully written file and fail if a destination already exists.
            os.link(temporary, destination)
