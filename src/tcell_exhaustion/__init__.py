"""Verified CD8+ T-cell exhaustion triage.

The package separates fast exploratory signals from donor-aware statistical
corroboration.  It never treats an in-silico result as wet-lab validation.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("verified-tcell-exhaustion-triage")
except PackageNotFoundError:  # pragma: no cover - source checkout before installation
    __version__ = "0.1.0"

__all__ = ["__version__"]

