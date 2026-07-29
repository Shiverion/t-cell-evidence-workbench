# Real-data checklist

The code is ready for a real `.h5ad` file, but the real analysis cannot be completed honestly until
the dataset and its data dictionary are available.

## Before the first run

- Confirm the license, de-identification status, and allowed use. Do not send PHI/PII to external
  services.
- Read how samples were collected and what the condition labels mean biologically.
- Identify the independent replicate: donor, animal, sample, or another documented unit.
- Confirm whether donors appear in both conditions (paired/repeated) or are nested in one condition.
- Confirm raw non-negative integer counts exist in a named AnnData layer.
- Confirm gene symbols are unique and not unconverted Ensembl IDs.
- Check that `CD8A, CD8B, CD4, PDCD1, HAVCR2, LAG3, TOX, TIGIT, ENTPD1` and subtype markers exist.
- Cross-tab condition × donor × batch/tissue. A perfectly confounded design cannot be repaired by a
  more sophisticated p-value.
- Lock QC thresholds and condition A/B semantics before looking at the condition result.

## Configure and inspect

Copy `configs/real-data.example.yaml`, then run:

```powershell
uv run tcell-triage inspect --config configs/my-real-data.yaml
```

Interpret the branch:

- `donor_aware`: at least the configured minimum donors exist in each condition; full reviewer is
  allowed.
- `exploratory_no_donor`: no reliable donor column; do not call hits verified.
- `marker_fallback`: only one condition; keep the result descriptive because defining and testing
  exhaustion with overlapping genes is circular.
- `blocked`: fix the data/config. Never bypass a raw-count or required-gene error by guessing.

## Run and audit

```powershell
uv run tcell-triage run --config configs/my-real-data.yaml --evidence evidence/literature_evidence.csv
```

Then:

1. Compare the RNA gate with any expert-provided cell-type annotation.
2. Check cells retained per donor and condition; differential filtering can bias results.
3. Inspect cluster-level marker scores before accepting labels.
4. Read donor points on the violin, not only cell distributions.
5. Confirm the headline rule was applied without manual subtype swapping.
6. Inspect low-count and outlier pseudobulk samples.
7. Review all 30 reviewer rows, including direction reversals and not-testable hits.
8. Re-open every PubMed/Open Targets source in the correct species/tissue/disease context.
9. Ask a computational biologist to audit the design and a domain scientist to audit the claim.
10. Rewrite the report in your own words and preserve the limitations.

## Claim template

> Within the analyzed CD8+ population, **[subtype]** had the largest estimated condition-B versus
> condition-A exhaustion-score shift (**Δ=...**, **donor-level FDR=...**, **n=.../... donors**).
> The direction/FDR criterion **[did/did not]** hold across all registered resolutions. The leading
> pseudobulk drivers were **[...]**. These results are computationally **corroborated/prioritized**,
> not experimentally validated, and remain limited by **[...]**.

If no subtype passes the rule, say so. A reproducible null result is a valid project outcome.

