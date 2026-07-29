from __future__ import annotations

import numpy as np
from scipy import sparse

from tcell_exhaustion.demo import CD8_SUBTYPES, EXHAUSTION_GENES, generate_demo_adata


def test_demo_is_balanced_deterministic_and_audibly_simulated():
    first = generate_demo_adata(seed=7, cells_per_subtype_per_donor=4, cd4_cells_per_donor=2)
    second = generate_demo_adata(seed=7, cells_per_subtype_per_donor=4, cd4_cells_per_donor=2)

    assert first.uns["is_simulated"] is True
    assert first.obs["is_simulated"].all()
    assert sparse.isspmatrix_csr(first.layers["counts"])
    assert np.issubdtype(first.layers["counts"].dtype, np.integer)
    assert (first.layers["counts"] != second.layers["counts"]).nnz == 0
    assert set(EXHAUSTION_GENES).issubset(first.var_names)

    donor_counts = first.obs.groupby("condition", observed=True)["donor"].nunique()
    assert donor_counts.to_dict() == {"A": 6, "B": 6}
    cd8 = first.obs[first.obs["cell_type"] == "CD8_T"]
    per_donor = cd8.groupby(["condition", "donor", "subtype"], observed=True).size()
    assert set(per_donor) == {4}
    assert set(cd8["subtype"].astype("object")) == set(CD8_SUBTYPES)


def test_terminally_exhausted_has_strongest_condition_b_exhaustion_shift():
    adata = generate_demo_adata(seed=11, cells_per_subtype_per_donor=8, cd4_cells_per_donor=2)
    counts = adata.layers["counts"][:, adata.var_names.isin(EXHAUSTION_GENES)].toarray()
    panel_mean = counts.mean(axis=1)

    deltas = {}
    for subtype in CD8_SUBTYPES:
        subtype_mask = np.asarray(adata.obs["subtype"] == subtype)
        a_mask = subtype_mask & np.asarray(adata.obs["condition"] == "A")
        b_mask = subtype_mask & np.asarray(adata.obs["condition"] == "B")
        deltas[subtype] = float(panel_mean[b_mask].mean() - panel_mean[a_mask].mean())

    assert max(deltas, key=deltas.get) == "terminally_exhausted"
    assert deltas["terminally_exhausted"] > 2 * deltas["effector_memory"]
