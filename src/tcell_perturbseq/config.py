"""Configuration for the lightweight official CD4 Perturb-seq workflow."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

OFFICIAL_CONDITIONS = ("Rest", "Stim8hr", "Stim48hr")


@dataclass(frozen=True)
class AnalysisConfig:
    """Runtime choices that materially affect candidate prioritization."""

    data_dir: Path = Path("data/official_cd4_perturbseq")
    output_dir: Path = Path("output/official_cd4_perturbseq")
    conditions: tuple[str, ...] = OFFICIAL_CONDITIONS
    top_n: int = 15
    min_cells_target: int = 100

    def __post_init__(self) -> None:
        object.__setattr__(self, "data_dir", Path(self.data_dir))
        object.__setattr__(self, "output_dir", Path(self.output_dir))
        if tuple(self.conditions) != OFFICIAL_CONDITIONS:
            raise ValueError(
                "The official workflow requires conditions Rest, Stim8hr, and Stim48hr "
                "in that order"
            )
        if self.top_n < 1:
            raise ValueError("top_n must be at least 1")
        if self.min_cells_target < 1:
            raise ValueError("min_cells_target must be at least 1")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable analysis contract."""

        payload = asdict(self)
        payload["data_dir"] = str(self.data_dir)
        payload["output_dir"] = str(self.output_dir)
        payload["conditions"] = list(self.conditions)
        payload["hard_gates"] = {
            "ontarget_significant": True,
            "ontarget_effect_size": "< 0",
            "offtarget_flag": False,
            "n_cells_target": f">= {self.min_cells_target}",
            "crossdonor_correlation_min": "present and > 0",
            "crossguide_correlation": "present and > 0",
        }
        return payload
