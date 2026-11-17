"""Shared figure lifecycle and filename helpers for every chart module."""

import hashlib
import re
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


@contextmanager
def figure(*args: Any, **kwargs: Any) -> Iterator[tuple[Any, Any]]:
    """Yield ``plt.subplots(...)`` and always close the figure, even if plotting fails."""
    fig, axes = plt.subplots(*args, **kwargs)
    try:
        yield fig, axes
    finally:
        plt.close(fig)


def safe_chart_path(output_dir: Path, prefix: str, label: str) -> Path:
    """Readable, collision-safe filename for a user-controlled label.

    Sanitising alone can map different names (``a/b`` and ``a_b``) to the same file,
    so a short hash of the exact label is appended, and an existing file is never reused.
    """
    readable = re.sub(r"[^A-Za-z0-9._-]+", "_", str(label)).strip("._")[:40] or "column"
    digest = hashlib.sha1(str(label).encode("utf-8", "surrogatepass")).hexdigest()[:8]
    path = output_dir / f"{prefix}_{readable}_{digest}.png"
    counter = 2
    while path.exists():
        path = output_dir / f"{prefix}_{readable}_{digest}_{counter}.png"
        counter += 1
    return path
