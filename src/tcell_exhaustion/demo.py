"""Deterministic simulated data for learning and end-to-end demonstrations.

The simulation has an explicitly disclosed ground truth.  It is useful for
learning how the pipeline behaves, but it is never evidence for a biological
claim.  No Scanpy dependency is needed to generate it.
"""

from __future__ import annotations

from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

from tcell_exhaustion.config import AnalysisConfig, QCConfig

CD8_SUBTYPES: tuple[str, ...] = (
    "naive_memory",
    "effector",
    "effector_memory",
    "terminally_exhausted",
)
CD4_DECOY = "cd4_decoy"

EXHAUSTION_GENES: tuple[str, ...] = (
    "PDCD1",
    "HAVCR2",
    "LAG3",
    "TOX",
    "TIGIT",
    "ENTPD1",
)

MARKER_GENES: tuple[str, ...] = (
    "CD8A",
    "CD8B",
    "CD4",
    "TCF7",
    "IL7R",
    "SELL",
    "CCR7",
    "GZMB",
    "PRF1",
    "NKG7",
    "GZMK",
    "TOX",
    "PDCD1",
    "HAVCR2",
    "ENTPD1",
    "LAYN",
    "LAG3",
    "TIGIT",
)

HOUSEKEEPING_GENES: tuple[str, ...] = (
    "ACTB",
    "GAPDH",
    "B2M",
    "RPLP0",
    "RPS18",
    "EEF1A1",
    "MALAT1",
    "LTB",
    "IL32",
    "TRBC1",
    "TRBC2",
    "CD3D",
    "CD3E",
    "CD3G",
)

MITO_GENES: tuple[str, ...] = (
    "MT-CO1",
    "MT-CO2",
    "MT-CO3",
    "MT-ND1",
    "MT-ND2",
    "MT-CYB",
)

# Neutral genes give normalization, PCA, and score-control binning enough
# background without importing a real biological dataset into the demo.
BACKGROUND_GENES: tuple[str, ...] = tuple(f"BG{i:03d}" for i in range(1, 81))


def generate_demo_adata(
    *,
    seed: int = 42,
    donors_per_condition: int = 6,
    cells_per_subtype_per_donor: int = 12,
    cd4_cells_per_donor: int = 6,
) -> ad.AnnData:
    """Generate a balanced AnnData object with a known exhaustion ground truth.

    Each condition has six independent donors by default, and every donor
    contributes the same number of cells from four CD8 subtypes plus a CD4
    decoy population.  Condition B has its largest exhaustion-panel increase in
    ``terminally_exhausted`` cells.  Donor-specific intercepts and exhaustion
    effects make pseudobulk meaningful while remaining centered within each
    condition.
    """

    if seed < 0:
        raise ValueError("seed must be non-negative")
    if donors_per_condition < 2:
        raise ValueError("donors_per_condition must be at least 2")
    if cells_per_subtype_per_donor < 1:
        raise ValueError("cells_per_subtype_per_donor must be at least 1")
    if cd4_cells_per_donor < 1:
        raise ValueError("cd4_cells_per_donor must be at least 1")

    rng = np.random.default_rng(seed)
    genes = tuple(
        dict.fromkeys((*MARKER_GENES, *HOUSEKEEPING_GENES, *MITO_GENES, *BACKGROUND_GENES))
    )
    gene_index = {gene: index for index, gene in enumerate(genes)}

    donor_effects: dict[str, tuple[float, float]] = {}
    for condition in ("A", "B"):
        library_effect = rng.normal(0.0, 0.16, size=donors_per_condition)
        exhaustion_effect = rng.normal(0.0, 0.10, size=donors_per_condition)
        # Center each condition independently so donor heterogeneity does not
        # accidentally create a condition effect in the disclosed ground truth.
        library_effect -= library_effect.mean()
        exhaustion_effect -= exhaustion_effect.mean()
        for donor_number in range(1, donors_per_condition + 1):
            donor = f"{condition}_donor_{donor_number:02d}"
            donor_effects[donor] = (
                float(library_effect[donor_number - 1]),
                float(exhaustion_effect[donor_number - 1]),
            )

    rows: list[np.ndarray] = []
    records: list[dict[str, object]] = []
    cell_number = 0
    for condition in ("A", "B"):
        for donor_number in range(1, donors_per_condition + 1):
            donor = f"{condition}_donor_{donor_number:02d}"
            donor_library_effect, donor_exhaustion_effect = donor_effects[donor]
            populations = (
                *((subtype, cells_per_subtype_per_donor) for subtype in CD8_SUBTYPES),
                (CD4_DECOY, cd4_cells_per_donor),
            )
            for subtype, n_cells in populations:
                for _ in range(n_cells):
                    cell_number += 1
                    mean = _base_mean(genes, gene_index, subtype)
                    if condition == "B" and subtype != CD4_DECOY:
                        _add_condition_b_shift(mean, gene_index, subtype)

                    # A cell-level library factor plus a shared donor intercept
                    # produces visible donor effects across all genes.
                    cell_library_effect = rng.normal(0.0, 0.12)
                    mean *= np.exp(donor_library_effect + cell_library_effect)
                    if subtype != CD4_DECOY:
                        exhaustion_positions = [gene_index[gene] for gene in EXHAUSTION_GENES]
                        mean[exhaustion_positions] *= np.exp(donor_exhaustion_effect)

                    # Gamma-Poisson sampling gives overdispersed integer counts,
                    # a closer teaching analogue than independent Gaussian data.
                    dispersion = 3.0
                    poisson_rate = rng.gamma(shape=dispersion, scale=mean / dispersion)
                    counts = rng.poisson(poisson_rate).astype(np.int32)
                    rows.append(counts)
                    records.append(
                        {
                            "cell_id": f"sim_cell_{cell_number:05d}",
                            "condition": condition,
                            "donor": donor,
                            "cell_type": "CD4_T" if subtype == CD4_DECOY else "CD8_T",
                            "subtype": subtype,
                            "true_subtype": subtype,
                            "is_simulated": True,
                        }
                    )

    count_array = np.vstack(rows).astype(np.int32, copy=False)
    counts = sparse.csr_matrix(count_array)
    normalized = _normalise_log1p(counts)

    obs = pd.DataFrame.from_records(records).set_index("cell_id")
    for column in ("condition", "donor", "cell_type", "subtype", "true_subtype"):
        obs[column] = obs[column].astype("category")
    var = pd.DataFrame(index=pd.Index(genes, name="gene_symbol"))
    var["gene_symbol"] = var.index.astype(str)
    var["is_mito"] = var.index.str.startswith("MT-")
    var["is_exhaustion_panel"] = var.index.isin(EXHAUSTION_GENES)
    var["is_marker"] = var.index.isin(MARKER_GENES)

    adata = ad.AnnData(X=normalized, obs=obs, var=var)
    adata.layers["counts"] = counts
    adata.uns["is_simulated"] = True
    adata.uns["simulation_truth"] = {
        "headline_subtype": "terminally_exhausted",
        "condition_a": "A",
        "condition_b": "B",
        "donors_per_condition": int(donors_per_condition),
        "seed": int(seed),
        "warning": "Synthetic teaching data; not biological evidence.",
    }
    adata.uns["exhaustion_genes"] = np.asarray(EXHAUSTION_GENES, dtype=str)
    return adata


# Friendly aliases for notebooks and command-line callers.
make_demo_adata = generate_demo_adata
create_demo_adata = generate_demo_adata
generate_demo_data = generate_demo_adata


def write_demo_h5ad(
    path: str | Path,
    *,
    seed: int = 42,
    donors_per_condition: int = 6,
    cells_per_subtype_per_donor: int = 12,
    cd4_cells_per_donor: int = 6,
) -> Path:
    """Generate the teaching dataset and write it to a ``.h5ad`` file."""

    output_path = Path(path)
    if output_path.suffix.lower() != ".h5ad":
        raise ValueError(f"Demo output must use a .h5ad suffix: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    adata = generate_demo_adata(
        seed=seed,
        donors_per_condition=donors_per_condition,
        cells_per_subtype_per_donor=cells_per_subtype_per_donor,
        cd4_cells_per_donor=cd4_cells_per_donor,
    )
    adata.write_h5ad(output_path)
    return output_path


def demo_config(
    input_path: str | Path,
    output_dir: str | Path,
    *,
    seed: int = 42,
) -> AnalysisConfig:
    """Return the standard config for a generated demo dataset."""

    return AnalysisConfig(
        input_path=Path(input_path),
        output_dir=Path(output_dir),
        seed=seed,
        qc=QCConfig(min_genes=10, max_genes=500, max_mito_pct=20.0, min_cells_per_gene=1),
    )


def _base_mean(
    genes: tuple[str, ...],
    gene_index: dict[str, int],
    subtype: str,
) -> np.ndarray:
    mean = np.full(len(genes), 0.08, dtype=np.float64)
    _set(mean, gene_index, HOUSEKEEPING_GENES, 1.8)
    _set(mean, gene_index, MITO_GENES, 0.20)

    if subtype == CD4_DECOY:
        _add(mean, gene_index, ("CD4",), 4.5)
        _add(mean, gene_index, ("IL7R", "TCF7", "CCR7"), 1.6)
        _add(mean, gene_index, ("CD3D", "CD3E", "CD3G"), 1.0)
        return mean

    _add(mean, gene_index, ("CD8A",), 3.8)
    _add(mean, gene_index, ("CD8B",), 2.8)
    _set(mean, gene_index, ("CD4",), 0.02)
    _add(mean, gene_index, ("CD3D", "CD3E", "CD3G"), 1.0)

    if subtype == "naive_memory":
        _add(mean, gene_index, ("TCF7", "IL7R", "SELL", "CCR7"), 3.2)
        _add(mean, gene_index, EXHAUSTION_GENES, 0.08)
    elif subtype == "effector":
        _add(mean, gene_index, ("GZMB", "PRF1", "NKG7"), 3.4)
        _add(mean, gene_index, ("GZMK",), 0.8)
        _add(mean, gene_index, EXHAUSTION_GENES, 0.25)
    elif subtype == "effector_memory":
        _add(mean, gene_index, ("GZMK", "NKG7", "IL7R"), 3.0)
        _add(mean, gene_index, ("TCF7", "PRF1"), 0.9)
        _add(mean, gene_index, EXHAUSTION_GENES, 0.55)
    elif subtype == "terminally_exhausted":
        _add(mean, gene_index, ("GZMB", "PRF1", "NKG7"), 2.2)
        _add(mean, gene_index, ("TOX", "PDCD1", "HAVCR2", "ENTPD1", "LAYN"), 2.8)
        _add(mean, gene_index, ("LAG3", "TIGIT"), 2.3)
    else:  # pragma: no cover - protected by the module's fixed population list
        raise ValueError(f"Unknown simulated subtype: {subtype}")
    return mean


def _add_condition_b_shift(
    mean: np.ndarray,
    gene_index: dict[str, int],
    subtype: str,
) -> None:
    # Absolute additions make the disclosed ranking robust on both raw and
    # library-normalized scales.  The terminal shift is intentionally largest.
    shift = {
        "naive_memory": 0.05,
        "effector": 0.15,
        "effector_memory": 0.35,
        "terminally_exhausted": 10.0,
    }[subtype]
    _add(mean, gene_index, EXHAUSTION_GENES, shift)


def _set(
    values: np.ndarray,
    gene_index: dict[str, int],
    genes: tuple[str, ...],
    amount: float,
) -> None:
    values[[gene_index[gene] for gene in genes]] = amount


def _add(
    values: np.ndarray,
    gene_index: dict[str, int],
    genes: tuple[str, ...],
    amount: float,
) -> None:
    values[[gene_index[gene] for gene in genes]] += amount


def _normalise_log1p(counts: sparse.csr_matrix) -> sparse.csr_matrix:
    totals = np.asarray(counts.sum(axis=1)).ravel()
    if np.any(totals == 0):  # extraordinarily unlikely, but keep X finite for every seed
        raise RuntimeError("Simulation unexpectedly generated an all-zero cell")
    scales = 10_000.0 / totals
    normalized = counts.astype(np.float64).multiply(scales[:, None]).tocsr()
    normalized.data = np.log1p(normalized.data)
    return normalized


__all__ = [
    "BACKGROUND_GENES",
    "CD4_DECOY",
    "CD8_SUBTYPES",
    "EXHAUSTION_GENES",
    "MARKER_GENES",
    "create_demo_adata",
    "demo_config",
    "generate_demo_adata",
    "generate_demo_data",
    "make_demo_adata",
    "write_demo_h5ad",
]
