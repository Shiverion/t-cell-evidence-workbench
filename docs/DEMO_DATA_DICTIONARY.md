# Demo data dictionary

`tcell-triage demo` writes `data/demo_tcells.h5ad`. The file is generated locally, deterministic
for a fixed seed, and ignored by Git because it can always be recreated.

## Scope and warning

The dataset is a **Gamma–Poisson simulation**, not a sample from a person, animal, disease, or
experiment. Its only purpose is to prove that the workflow recovers a known signal and to teach
how pseudoreplication changes conclusions.

Default size:

- 648 cells;
- 118 genes;
- conditions `A` and `B`;
- 6 independent donors per condition;
- 12 cells per donor × CD8 subtype;
- 6 CD4 decoy cells per donor.

## AnnData matrices

| Location | Meaning |
|---|---|
| `adata.layers['counts']` | Sparse, non-negative integer raw counts. This is the only matrix summed for pseudobulk. |
| `adata.X` | Library-size normalized and log1p-transformed values provided for convenient first inspection. The pipeline rebuilds its representation from raw counts. |
| `adata.obsm` | Empty before analysis; PCA and UMAP are added to the processed output. |

## Cell metadata (`adata.obs`)

| Column | Meaning |
|---|---|
| `condition` | `A` or `B`; donors are nested within a condition. |
| `donor` | `A_donor_01` … `B_donor_06`; the independent statistical unit. |
| `cell_type` | `CD8_T` for intended analysis cells or `CD4_T` for decoys. |
| `subtype` | Simulated generating state. The real pipeline overwrites its working copy with marker-derived labels. |
| `true_subtype` | Preserved generating state used only to test annotation recovery. Never available as truth in real data. |
| `is_simulated` | Always `True`. |

Cell IDs are deterministic strings such as `sim_cell_00001`.

## Gene metadata (`adata.var`)

| Column | Meaning |
|---|---|
| `gene_symbol` | Unique symbol matching `var_names`. |
| `is_mito` | Symbol starts with `MT-`; used for the mitochondrial QC fraction. |
| `is_exhaustion_panel` | One of `PDCD1, HAVCR2, LAG3, TOX, TIGIT, ENTPD1`. |
| `is_marker` | Used by a registered CD8/subtype panel. |

The file also contains housekeeping, mitochondrial, T-cell, and neutral `BG###` genes so
normalization, PCA, and control-gene binning have a realistic background.

## Injected ground truth

All CD8 states receive a small condition-B shift, but the six exhaustion genes receive by far the
largest addition in `terminally_exhausted`. Donor-specific library and exhaustion effects are
centered within each condition, then cell counts are sampled from an overdispersed Gamma–Poisson
distribution.

The required recovery test is therefore:

1. `terminally_exhausted` is the largest positive donor-score delta;
2. its donor-level subtype FDR is below 0.05;
3. it survives all four registered resolutions;
4. the six injected panel drivers survive PyDESeq2;
5. many naive cell-level background hits do not survive pseudobulk.

If a code change breaks one of those expectations, the integration test fails.

