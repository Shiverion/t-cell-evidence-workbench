"""Pinned official-source definitions, downloads, loading, and schema audits."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from tcell_perturbseq.config import OFFICIAL_CONDITIONS

PINNED_COMMIT = "848d62fc2b7027f7218d6fc5f5b0c37255dc94af"
REPOSITORY_URL = "https://github.com/emdann/GWT_perturbseq_analysis_2025"
RAW_BASE_URL = (
    f"https://raw.githubusercontent.com/emdann/GWT_perturbseq_analysis_2025/{PINNED_COMMIT}"
)


@dataclass(frozen=True)
class SourceSpec:
    """One small, version-pinned official supplementary table."""

    key: str
    filename: str
    relative_path: str
    expected_bytes: int
    expected_sha256: str
    required_columns: tuple[str, ...]

    @property
    def url(self) -> str:
        return f"{RAW_BASE_URL}/{self.relative_path}"


SOURCE_SPECS = (
    SourceSpec(
        key="de_stats",
        filename="DE_stats.suppl_table.csv",
        relative_path="metadata/suppl_tables/DE_stats.suppl_table.csv",
        expected_bytes=5_341_369,
        expected_sha256="66fb80b93ef107095a8218efa06a5b272093d9343e9009b3ea4a88ba3cafdead",
        required_columns=(
            "target_contrast_gene_name",
            "culture_condition",
            "target_contrast",
            "n_cells_target",
            "ontarget_effect_size",
            "ontarget_significant",
            "offtarget_flag",
            "n_downstream",
            "crossdonor_correlation_min",
            "crossguide_correlation",
        ),
    ),
    SourceSpec(
        key="sample_metadata",
        filename="sample_metadata.suppl_table.csv",
        relative_path="metadata/suppl_tables/sample_metadata.suppl_table.csv",
        expected_bytes=2_966,
        expected_sha256="766134d11dabb5d63388e00b4d687a809c0254eb3c19d77f439a6bf9dad7abd4",
        required_columns=(
            "cell_sample_id",
            "10xrun_id",
            "donor_id",
            "culture_condition",
            "library_id",
        ),
    ),
    SourceSpec(
        key="arrayed_validation",
        filename="IL10_IL21_arrayed_validation.csv",
        relative_path="metadata/suppl_tables/IL10_IL21_arrayed_validation.csv",
        expected_bytes=2_200,
        expected_sha256="f60cdda392d6f29d10a539727ff7324b04d17e35c0512c889b733e00380b83dc",
        required_columns=("Sample", "IL10_perc", "IL21_perc", "Donor", "Perturbation"),
    ),
    SourceSpec(
        key="polarization_coefficients",
        filename="polarization_prediction_condition_comparison_regulator_coefficients.csv",
        relative_path=(
            "metadata/suppl_tables/"
            "polarization_prediction_condition_comparison_regulator_coefficients.csv"
        ),
        expected_bytes=2_639_223,
        expected_sha256="57e57c9a825b4d49a3fff6c4e529bb3366c432d3639d026953addfcfe19ac25f",
        required_columns=(
            "coef_mean",
            "coef_sem",
            "coef_rank",
            "regulator",
            "dataset_key",
            "signature",
        ),
    ),
)


class SourceSchemaError(ValueError):
    """Raised when an official input no longer matches its declared schema."""


def sha256_file(path: Path, *, chunk_size: int = 1 << 20) -> str:
    """Return a streaming SHA-256 hash."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def source_paths(data_dir: Path) -> dict[str, Path]:
    """Resolve every official input path without touching the filesystem."""

    root = Path(data_dir)
    return {spec.key: root / spec.filename for spec in SOURCE_SPECS}


def _verify_source_file(path: Path, spec: SourceSpec) -> None:
    actual_bytes = path.stat().st_size
    actual_sha256 = sha256_file(path)
    if actual_bytes != spec.expected_bytes or actual_sha256 != spec.expected_sha256:
        raise OSError(
            f"Checksum mismatch for {path}. Expected {spec.expected_bytes} bytes and "
            f"SHA-256 {spec.expected_sha256}, got {actual_bytes} bytes and {actual_sha256}. "
            "Use --force to replace a stale cached file with the pinned official source."
        )


def download_sources(
    data_dir: Path,
    *,
    force: bool = False,
    timeout_seconds: int = 120,
) -> dict[str, Path]:
    """Download the four pinned CSVs using only the Python standard library.

    Each download is first written to a temporary file in the destination directory and then
    atomically replaced, so an interrupted transfer cannot masquerade as a complete input.
    """

    root = Path(data_dir)
    root.mkdir(parents=True, exist_ok=True)
    downloaded: dict[str, Path] = {}
    for spec in SOURCE_SPECS:
        destination = root / spec.filename
        if destination.is_file() and destination.stat().st_size > 0 and not force:
            _verify_source_file(destination, spec)
            downloaded[spec.key] = destination
            continue

        request = urllib.request.Request(
            spec.url,
            headers={"User-Agent": "tcell-perturbseq-learning-project/0.1"},
        )
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f".{spec.filename}.",
                suffix=".part",
                dir=root,
                delete=False,
            ) as temporary:
                temp_path = Path(temporary.name)
                with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                    shutil.copyfileobj(response, temporary)
            if temp_path.stat().st_size == 0:
                raise OSError(f"Downloaded an empty file from {spec.url}")
            _verify_source_file(temp_path, spec)
            temp_path.replace(destination)
        except Exception:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
            raise
        downloaded[spec.key] = destination
    return downloaded


def _drop_csv_index_columns(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.loc[:, ~frame.columns.astype(str).str.startswith("Unnamed:")].copy()


def load_source_tables(
    data_dir: Path,
    *,
    verify_hashes: bool = True,
) -> dict[str, pd.DataFrame]:
    """Load all downloaded CSVs and remove only serialization index columns."""

    paths = source_paths(data_dir)
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        joined = "\n- ".join(missing)
        raise FileNotFoundError(f"Official source files are missing:\n- {joined}")
    if verify_hashes:
        for spec in SOURCE_SPECS:
            _verify_source_file(paths[spec.key], spec)
    return {
        key: _drop_csv_index_columns(pd.read_csv(path, low_memory=False))
        for key, path in paths.items()
    }


def _require_columns(name: str, frame: pd.DataFrame, columns: tuple[str, ...]) -> None:
    missing = sorted(set(columns).difference(frame.columns))
    if missing:
        raise SourceSchemaError(f"{name} is missing required columns: {', '.join(missing)}")


def coerce_boolean(series: pd.Series, *, column: str) -> pd.Series:
    """Parse a strict boolean column and reject unfamiliar source encodings."""

    if pd.api.types.is_bool_dtype(series):
        return series.astype(bool)
    mapping: dict[Any, bool] = {
        True: True,
        False: False,
        "true": True,
        "false": False,
        "1": True,
        "0": False,
    }
    lowered = series.map(lambda value: value.strip().lower() if isinstance(value, str) else value)
    parsed = lowered.map(mapping)
    invalid = series[parsed.isna() & series.notna()]
    if not invalid.empty:
        examples = ", ".join(map(str, invalid.astype(str).unique()[:5]))
        raise SourceSchemaError(f"{column} contains invalid boolean values: {examples}")
    return parsed.astype("boolean")


def _require_numeric(name: str, frame: pd.DataFrame, columns: tuple[str, ...]) -> None:
    for column in columns:
        converted = pd.to_numeric(frame[column], errors="coerce")
        invalid = frame[column].notna() & converted.isna()
        if invalid.any():
            examples = ", ".join(map(str, frame.loc[invalid, column].astype(str).unique()[:5]))
            raise SourceSchemaError(f"{name}.{column} contains nonnumeric values: {examples}")


def audit_source_tables(
    tables: dict[str, pd.DataFrame],
    *,
    conditions: tuple[str, ...] = OFFICIAL_CONDITIONS,
) -> dict[str, Any]:
    """Block on schema drift and return a compact, JSON-ready source audit."""

    missing_tables = sorted({spec.key for spec in SOURCE_SPECS}.difference(tables))
    if missing_tables:
        raise SourceSchemaError(f"Missing source tables: {', '.join(missing_tables)}")
    for spec in SOURCE_SPECS:
        _require_columns(spec.key, tables[spec.key], spec.required_columns)

    de = tables["de_stats"]
    _require_numeric(
        "de_stats",
        de,
        (
            "n_cells_target",
            "ontarget_effect_size",
            "n_downstream",
            "crossdonor_correlation_min",
            "crossguide_correlation",
        ),
    )
    coerce_boolean(de["ontarget_significant"], column="ontarget_significant")
    coerce_boolean(de["offtarget_flag"], column="offtarget_flag")
    duplicated_de = de.duplicated(["target_contrast_gene_name", "culture_condition"], keep=False)
    if duplicated_de.any():
        raise SourceSchemaError(
            "de_stats has duplicate target_contrast_gene_name/culture_condition rows"
        )
    found_conditions = set(de["culture_condition"].dropna().astype(str))
    missing_conditions = sorted(set(conditions).difference(found_conditions))
    if missing_conditions:
        raise SourceSchemaError(
            f"de_stats is missing expected conditions: {', '.join(missing_conditions)}"
        )

    metadata = tables["sample_metadata"]
    duplicated_samples = metadata["cell_sample_id"].duplicated(keep=False)
    if duplicated_samples.any():
        raise SourceSchemaError("sample_metadata has duplicate cell_sample_id values")
    metadata_conditions = set(metadata["culture_condition"].dropna().astype(str))
    missing_metadata_conditions = sorted(set(conditions).difference(metadata_conditions))
    if missing_metadata_conditions:
        raise SourceSchemaError(
            "sample_metadata is missing expected conditions: "
            + ", ".join(missing_metadata_conditions)
        )

    validation = tables["arrayed_validation"]
    _require_numeric("arrayed_validation", validation, ("IL10_perc", "IL21_perc"))
    control_mask = (
        validation["Perturbation"].astype(str).str.fullmatch(r"NTC[123]?", case=False, na=False)
    )
    donors = set(validation["Donor"].dropna().astype(str))
    control_donors = set(validation.loc[control_mask, "Donor"].dropna().astype(str))
    missing_control_donors = sorted(donors.difference(control_donors))
    if missing_control_donors:
        raise SourceSchemaError(
            "arrayed_validation lacks an NTC/NTC1/NTC2/NTC3 control for donors: "
            + ", ".join(missing_control_donors)
        )

    coefficients = tables["polarization_coefficients"]
    _require_numeric(
        "polarization_coefficients",
        coefficients,
        ("coef_mean", "coef_sem", "coef_rank"),
    )

    table_rows = {
        spec.key: {
            "rows": int(len(tables[spec.key])),
            "columns": int(tables[spec.key].shape[1]),
            "required_columns_present": True,
        }
        for spec in SOURCE_SPECS
    }
    return {
        "status": "passed",
        "source": {
            "repository": REPOSITORY_URL,
            "pinned_commit": PINNED_COMMIT,
        },
        "tables": table_rows,
        "design": {
            "conditions": list(conditions),
            "screen_donors": sorted(metadata["donor_id"].dropna().astype(str).unique()),
            "screen_samples": int(len(metadata)),
            "arrayed_validation_donors": sorted(donors),
        },
        "checks": {
            "unique_gene_condition_rows": True,
            "unique_sample_ids": True,
            "all_validation_donors_have_ntc": True,
            "numeric_columns_parse": True,
            "boolean_columns_parse": True,
        },
    }
