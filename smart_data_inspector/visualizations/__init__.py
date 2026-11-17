"""Static, optional Matplotlib visualisations for one inspection run."""

import os
import tempfile

# CI/local CLI users may not have a writable home-directory cache. This is set
# before any pyplot import, preventing Matplotlib diagnostics from polluting CLI stderr.
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "sdi-matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", os.path.join(tempfile.gettempdir(), "sdi-cache"))

from .pipeline import generate_charts

__all__ = ["generate_charts"]
