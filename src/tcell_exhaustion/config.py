"""Typed, pre-registered configuration for the exhaustion triage workflow.

The defaults in this module are analysis decisions, not tuning suggestions.  In
particular, the gene panels and Leiden resolution sweep mirror ``PROJECT.md`` so
that they are fixed before looking at an input dataset.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when a configuration file is missing or internally inconsistent."""


@dataclass(frozen=True)
class QCConfig:
    """Conservative first-pass single-cell QC thresholds."""

    min_genes: int = 200
    max_genes: int = 6_000
    max_mito_pct: float = 20.0
    min_cells_per_gene: int = 3

    def __post_init__(self) -> None:
        if self.min_genes < 0:
            raise ConfigError("qc.min_genes must be non-negative")
        if self.max_genes <= self.min_genes:
            raise ConfigError("qc.max_genes must be greater than qc.min_genes")
        if not 0 <= self.max_mito_pct <= 100:
            raise ConfigError("qc.max_mito_pct must be between 0 and 100")
        if self.min_cells_per_gene < 1:
            raise ConfigError("qc.min_cells_per_gene must be at least 1")


@dataclass(frozen=True)
class MarkerPanels:
    """Pre-registered marker panels used to annotate CD8 states."""

    memory_stem_like: tuple[str, ...] = ("TCF7", "IL7R", "SELL", "CCR7")
    effector_cytotoxic: tuple[str, ...] = ("GZMB", "PRF1", "NKG7", "GZMK")
    terminally_exhausted: tuple[str, ...] = (
        "TOX",
        "PDCD1",
        "HAVCR2",
        "ENTPD1",
        "LAYN",
    )

    def __post_init__(self) -> None:
        for name, genes in asdict(self).items():
            _validate_gene_list(f"marker_panels.{name}", genes)

    def as_dict(self) -> dict[str, tuple[str, ...]]:
        """Return a regular mapping for APIs that consume named gene sets."""

        return {
            "memory_stem_like": self.memory_stem_like,
            "effector_cytotoxic": self.effector_cytotoxic,
            "terminally_exhausted": self.terminally_exhausted,
        }


@dataclass(frozen=True)
class MarkerRule:
    """An explicit positive/negative rule for a marker-defined subtype.

    Effector-memory is deliberately registered as a rule because it occupies a
    continuum between the memory and cytotoxic panels.  Requiring two positive
    markers and absence of the terminal markers makes that ambiguity visible
    instead of resolving it by eyeballing a UMAP after the fact.
    """

    positive: tuple[str, ...] = ("GZMK", "NKG7", "IL7R")
    negative: tuple[str, ...] = ("HAVCR2", "ENTPD1")
    min_positive: int = 2

    def __post_init__(self) -> None:
        _validate_gene_list("effector_memory_rule.positive", self.positive)
        _validate_gene_list("effector_memory_rule.negative", self.negative)
        if not 1 <= self.min_positive <= len(self.positive):
            raise ConfigError(
                "effector_memory_rule.min_positive must be between 1 and the number "
                "of positive markers"
            )
        overlap = set(self.positive).intersection(self.negative)
        if overlap:
            raise ConfigError(
                f"effector_memory_rule positive and negative markers overlap: {sorted(overlap)}"
            )


@dataclass(frozen=True)
class AnalysisConfig:
    """Complete configuration for one reproducible analysis run.

    ``input_path`` and ``output_dir`` have no defaults on purpose: every run
    must say which evidence it read and where it wrote its artifacts.
    """

    input_path: Path
    output_dir: Path
    condition_key: str = "condition"
    donor_key: str = "donor"
    condition_a: str = "A"
    condition_b: str = "B"
    counts_layer: str = "counts"
    seed: int = 42
    qc: QCConfig = field(default_factory=QCConfig)
    resolutions: tuple[float, ...] = (0.4, 0.6, 0.8, 1.0)
    marker_panels: MarkerPanels = field(default_factory=MarkerPanels)
    effector_memory_rule: MarkerRule = field(default_factory=MarkerRule)
    exhaustion_genes: tuple[str, ...] = (
        "PDCD1",
        "HAVCR2",
        "LAG3",
        "TOX",
        "TIGIT",
        "ENTPD1",
    )
    min_donors_per_condition: int = 4

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_path", Path(self.input_path))
        object.__setattr__(self, "output_dir", Path(self.output_dir))
        for name in ("condition_key", "donor_key", "condition_a", "condition_b", "counts_layer"):
            if not str(getattr(self, name)).strip():
                raise ConfigError(f"{name} must be a non-empty string")
        if self.condition_a == self.condition_b:
            raise ConfigError("condition_a and condition_b must be different")
        if self.seed < 0:
            raise ConfigError("seed must be non-negative")
        if self.min_donors_per_condition < 2:
            raise ConfigError("min_donors_per_condition must be at least 2")
        if not self.resolutions:
            raise ConfigError("resolutions must contain at least one value")
        if any(resolution <= 0 for resolution in self.resolutions):
            raise ConfigError("all resolutions must be positive")
        if len(set(self.resolutions)) != len(self.resolutions):
            raise ConfigError("resolutions must not contain duplicates")
        _validate_gene_list("exhaustion_genes", self.exhaustion_genes)

    @property
    def raw_counts_layer(self) -> str:
        """Compatibility/readability alias for :attr:`counts_layer`."""

        return self.counts_layer

    @property
    def random_seed(self) -> int:
        """Compatibility/readability alias for :attr:`seed`."""

        return self.seed

    @classmethod
    def from_yaml(cls, path: str | Path) -> AnalysisConfig:
        """Load and validate a YAML config, resolving paths beside that file."""

        config_path = Path(path)
        try:
            with config_path.open("r", encoding="utf-8") as handle:
                payload = yaml.safe_load(handle)
        except OSError as exc:
            raise ConfigError(f"Could not read config file {config_path}: {exc}") from exc
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc

        if payload is None:
            raise ConfigError(f"Config file {config_path} is empty")
        if not isinstance(payload, Mapping):
            raise ConfigError("The YAML document must be a mapping")
        return cls.from_mapping(payload, base_dir=config_path.resolve().parent)

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
        *,
        base_dir: str | Path | None = None,
    ) -> AnalysisConfig:
        """Construct a config from a mapping.

        A few descriptive aliases are accepted (``obs_keys``, ``conditions``,
        ``raw_counts_layer``, and ``random_seed``).  Arbitrary unknown keys are
        rejected so a typo cannot silently alter a pre-registered run.
        """

        data = dict(payload)
        _expand_nested_aliases(data)
        aliases = {
            "raw_counts_layer": "counts_layer",
            "random_seed": "seed",
            "leiden_resolutions": "resolutions",
            "markers": "marker_panels",
        }
        for alias, canonical in aliases.items():
            if alias in data:
                if canonical in data:
                    raise ConfigError(f"Specify only one of {alias!r} and {canonical!r}")
                data[canonical] = data.pop(alias)

        allowed = {
            "input_path",
            "output_dir",
            "condition_key",
            "donor_key",
            "condition_a",
            "condition_b",
            "counts_layer",
            "seed",
            "qc",
            "resolutions",
            "marker_panels",
            "effector_memory_rule",
            "exhaustion_genes",
            "min_donors_per_condition",
        }
        unknown = sorted(set(data).difference(allowed))
        if unknown:
            raise ConfigError(f"Unknown config key(s): {', '.join(unknown)}")
        missing = [name for name in ("input_path", "output_dir") if name not in data]
        if missing:
            raise ConfigError(f"Missing required config key(s): {', '.join(missing)}")

        root = Path(base_dir) if base_dir is not None else None
        data["input_path"] = _config_path(data["input_path"], root, "input_path")
        data["output_dir"] = _config_path(data["output_dir"], root, "output_dir")
        if "qc" in data:
            data["qc"] = _nested_dataclass(QCConfig, data["qc"], "qc")
        if "marker_panels" in data:
            marker_data = _normalise_marker_panel_names(data["marker_panels"])
            data["marker_panels"] = _nested_dataclass(
                MarkerPanels, marker_data, "marker_panels", tuple_fields=True
            )
        if "effector_memory_rule" in data:
            data["effector_memory_rule"] = _nested_dataclass(
                MarkerRule, data["effector_memory_rule"], "effector_memory_rule", tuple_fields=True
            )
        if "resolutions" in data:
            data["resolutions"] = _as_tuple(data["resolutions"], "resolutions", float)
        if "exhaustion_genes" in data:
            data["exhaustion_genes"] = _as_tuple(data["exhaustion_genes"], "exhaustion_genes", str)

        try:
            return cls(**data)
        except TypeError as exc:
            raise ConfigError(f"Invalid configuration: {exc}") from exc

    def to_dict(self) -> dict[str, Any]:
        """Return a YAML/JSON-friendly representation."""

        result = asdict(self)
        result["input_path"] = str(self.input_path)
        result["output_dir"] = str(self.output_dir)
        return result


# Short public name for callers that prefer ``Config``.
Config = AnalysisConfig


def load_config(path: str | Path) -> AnalysisConfig:
    """Load :class:`AnalysisConfig` from YAML."""

    return AnalysisConfig.from_yaml(path)


def _expand_nested_aliases(data: dict[str, Any]) -> None:
    obs_keys = data.pop("obs_keys", data.pop("obs", None))
    if obs_keys is not None:
        if not isinstance(obs_keys, Mapping):
            raise ConfigError("obs_keys must be a mapping with condition and donor keys")
        unknown = set(obs_keys).difference({"condition", "donor"})
        if unknown:
            raise ConfigError(f"Unknown obs_keys key(s): {', '.join(sorted(unknown))}")
        for short, canonical in (("condition", "condition_key"), ("donor", "donor_key")):
            if short in obs_keys:
                if canonical in data:
                    raise ConfigError(f"Specify {canonical!r} either directly or in obs_keys")
                data[canonical] = obs_keys[short]

    conditions = data.pop("conditions", None)
    if conditions is not None:
        if not isinstance(conditions, Mapping):
            raise ConfigError("conditions must be a mapping with a and b keys")
        lowered = {str(key).lower(): value for key, value in conditions.items()}
        unknown = set(lowered).difference({"a", "b"})
        if unknown:
            raise ConfigError(f"Unknown conditions key(s): {', '.join(sorted(unknown))}")
        for short, canonical in (("a", "condition_a"), ("b", "condition_b")):
            if short in lowered:
                if canonical in data:
                    raise ConfigError(f"Specify {canonical!r} either directly or in conditions")
                data[canonical] = lowered[short]


def _normalise_marker_panel_names(value: Any) -> Any:
    if not isinstance(value, Mapping):
        return value
    result = dict(value)
    aliases = {
        "memory": "memory_stem_like",
        "stem_like": "memory_stem_like",
        "effector": "effector_cytotoxic",
        "cytotoxic": "effector_cytotoxic",
        "terminal": "terminally_exhausted",
    }
    for alias, canonical in aliases.items():
        if alias in result:
            if canonical in result:
                raise ConfigError(
                    f"Specify only one of marker_panels.{alias} and marker_panels.{canonical}"
                )
            result[canonical] = result.pop(alias)
    return result


def _nested_dataclass(
    cls: type[Any],
    value: Any,
    name: str,
    *,
    tuple_fields: bool = False,
) -> Any:
    if isinstance(value, cls):
        return value
    if not isinstance(value, Mapping):
        raise ConfigError(f"{name} must be a mapping")
    nested = dict(value)
    field_names = set(cls.__dataclass_fields__)
    unknown = sorted(set(nested).difference(field_names))
    if unknown:
        raise ConfigError(f"Unknown {name} key(s): {', '.join(unknown)}")
    if tuple_fields:
        for key in ("positive", "negative", *MarkerPanels.__dataclass_fields__):
            if key in nested:
                nested[key] = _as_tuple(nested[key], f"{name}.{key}", str)
    try:
        return cls(**nested)
    except TypeError as exc:
        raise ConfigError(f"Invalid {name}: {exc}") from exc


def _as_tuple(value: Any, name: str, item_type: type[Any]) -> tuple[Any, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise ConfigError(f"{name} must be a list")
    try:
        return tuple(item_type(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Invalid value in {name}: {exc}") from exc


def _config_path(value: Any, root: Path | None, name: str) -> Path:
    if value is None or not str(value).strip():
        raise ConfigError(f"{name} must be a non-empty path")
    path = Path(value).expanduser()
    if root is not None and not path.is_absolute():
        path = root / path
    return path.resolve() if root is not None else path


def _validate_gene_list(name: str, genes: Any) -> None:
    if not genes:
        raise ConfigError(f"{name} must not be empty")
    if any(not isinstance(gene, str) or not gene.strip() for gene in genes):
        raise ConfigError(f"{name} must contain non-empty gene symbols")
    if len(set(genes)) != len(genes):
        raise ConfigError(f"{name} must not contain duplicate genes")


__all__ = [
    "AnalysisConfig",
    "Config",
    "ConfigError",
    "MarkerPanels",
    "MarkerRule",
    "QCConfig",
    "load_config",
]
