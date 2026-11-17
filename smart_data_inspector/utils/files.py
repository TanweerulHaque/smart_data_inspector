"""Failure-safe local output: stage everything, then move it into place together."""

import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4


def write_text_atomic(path: Path, text: str) -> None:
    """Encode first, write beside the destination, then atomically replace it."""
    payload = text.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix=".sdi-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def remove_path(path: Path) -> None:
    """Delete a file, link or directory tree if it exists."""
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


def commit_staged(moves: list[tuple[Path, Path]]) -> None:
    """Move each staged path onto its destination as one unit.

    Existing destinations are set aside first. If any move fails, every destination
    already moved is removed and the previous contents are restored, so a run never
    leaves a report without its charts (or charts without a report).
    """
    done: list[tuple[Path, Path | None]] = []
    try:
        for staged, destination in moves:
            backup = None
            if destination.exists() or destination.is_symlink():
                backup = destination.with_name(f".{destination.name}.sdi-backup-{uuid4().hex[:8]}")
                os.replace(destination, backup)
            done.append((destination, backup))
            os.replace(staged, destination)
    except BaseException:
        for destination, backup in reversed(done):
            if destination.exists() or destination.is_symlink():
                remove_path(destination)
            if backup is not None:
                os.replace(backup, destination)
        raise
    for _, backup in done:
        if backup is not None:
            remove_path(backup)
