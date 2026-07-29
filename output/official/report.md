# Official CD4+ T-cell Perturb-seq Candidate Triage

## Answer first

**SETDB1** had the highest worst-condition priority score (0.915) among genes that passed source QC in Rest, Stim8hr, and Stim48hr. This is a descriptive prioritization result, not experimental verification.

The final source-QC pass counts were Rest: 497, Stim8hr: 593, Stim48hr: 562. A **source-QC pass** means a row met the declared
on-target, off-target, cell-count, cross-donor, and cross-guide gates. A **reproducible candidate**
means it passed those source gates in all three conditions. Neither label means wet-lab validated,
causal, safe, or therapeutically useful.

## Data actually used

This run used four small official supplementary CSVs from [https://github.com/emdann/GWT_perturbseq_analysis_2025](https://github.com/emdann/GWT_perturbseq_analysis_2025) at
commit `848d62fc2b7027f7218d6fc5f5b0c37255dc94af`. It did **not** download or analyze the 22-million-cell matrices. The
source audit passed for 12 screen samples and
4 screen donors across Rest, Stim8hr, and Stim48hr.

## Top candidates within each condition

| culture_condition   |   rank_within_condition | gene     |   n_downstream |   crossdonor_min |   crossguide |   priority_score |
|:--------------------|------------------------:|:---------|---------------:|-----------------:|-------------:|-----------------:|
| Rest                |                       1 | SETDB1   |           2290 |            0.735 |        0.909 |            0.945 |
| Rest                |                       2 | PTEN     |           2928 |            0.756 |        0.860 |            0.924 |
| Rest                |                       3 | ARNT     |           2319 |            0.752 |        0.842 |            0.912 |
| Rest                |                       4 | PAXIP1   |           1070 |            0.764 |        0.900 |            0.910 |
| Rest                |                       5 | EHMT2    |           1428 |            0.714 |        0.862 |            0.896 |
| Rest                |                       6 | NFRKB    |           3019 |            0.720 |        0.808 |            0.890 |
| Rest                |                       7 | THRAP3   |           1199 |            0.620 |        0.936 |            0.889 |
| Rest                |                       8 | AHR      |           2789 |            0.618 |        0.874 |            0.887 |
| Rest                |                       9 | MED12    |           2842 |            0.715 |        0.779 |            0.873 |
| Rest                |                      10 | TAF13    |           2189 |            0.623 |        0.832 |            0.866 |
| Rest                |                      11 | ELAVL1   |           2163 |            0.570 |        0.874 |            0.861 |
| Rest                |                      12 | USP22    |           1782 |            0.633 |        0.808 |            0.854 |
| Rest                |                      13 | CCND2    |           1286 |            0.647 |        0.814 |            0.852 |
| Rest                |                      14 | KDM1A    |           2017 |            0.629 |        0.799 |            0.851 |
| Rest                |                      15 | UFM1     |           1669 |            0.610 |        0.817 |            0.847 |
| Stim48hr            |                       1 | ARNT     |           2946 |            0.715 |        0.881 |            0.942 |
| Stim48hr            |                       2 | TADA2B   |           5259 |            0.648 |        0.870 |            0.921 |
| Stim48hr            |                       3 | SETDB1   |           1183 |            0.764 |        0.910 |            0.917 |
| Stim48hr            |                       4 | KDM1A    |           2912 |            0.718 |        0.813 |            0.913 |
| Stim48hr            |                       5 | ARHGAP30 |           1483 |            0.646 |        0.913 |            0.910 |
| Stim48hr            |                       6 | AHR      |           1821 |            0.736 |        0.834 |            0.909 |
| Stim48hr            |                       7 | GATA3    |           1252 |            0.705 |        0.884 |            0.906 |
| Stim48hr            |                       8 | CREBBP   |           1956 |            0.663 |        0.841 |            0.903 |
| Stim48hr            |                       9 | RASAL3   |            985 |            0.641 |        0.973 |            0.895 |
| Stim48hr            |                      10 | DOLPP1   |           1505 |            0.597 |        0.915 |            0.888 |
| Stim48hr            |                      11 | TMX1     |           1959 |            0.627 |        0.841 |            0.888 |
| Stim48hr            |                      12 | PCGF1    |           1078 |            0.768 |        0.853 |            0.887 |
| Stim48hr            |                      13 | NFRKB    |           2519 |            0.691 |        0.776 |            0.885 |
| Stim48hr            |                      14 | MIPEP    |           2143 |            0.626 |        0.826 |            0.883 |
| Stim48hr            |                      15 | TFAM     |           2960 |            0.682 |        0.772 |            0.883 |
| Stim8hr             |                       1 | ARNT     |           2642 |            0.695 |        0.864 |            0.916 |
| Stim8hr             |                       2 | SETDB1   |           1308 |            0.796 |        0.907 |            0.915 |
| Stim8hr             |                       3 | AHR      |           1776 |            0.686 |        0.890 |            0.905 |
| Stim8hr             |                       4 | PLCG1    |           5032 |            0.688 |        0.822 |            0.901 |
| Stim8hr             |                       5 | KDM1A    |           2300 |            0.692 |        0.844 |            0.900 |
| Stim8hr             |                       6 | NFRKB    |           2891 |            0.669 |        0.836 |            0.893 |
| Stim8hr             |                       7 | EHMT2    |           1177 |            0.765 |        0.853 |            0.885 |
| Stim8hr             |                       8 | BHLHE40  |           1996 |            0.731 |        0.796 |            0.880 |
| Stim8hr             |                       9 | CBLB     |           1027 |            0.665 |        0.920 |            0.877 |
| Stim8hr             |                      10 | TRIP12   |           1829 |            0.667 |        0.834 |            0.877 |
| Stim8hr             |                      11 | MED12    |           4141 |            0.687 |        0.776 |            0.876 |
| Stim8hr             |                      12 | DOLPP1   |           2717 |            0.595 |        0.859 |            0.875 |
| Stim8hr             |                      13 | WAC      |           2475 |            0.650 |        0.809 |            0.871 |
| Stim8hr             |                      14 | CD28     |           1505 |            0.626 |        0.857 |            0.864 |
| Stim8hr             |                      15 | TFAM     |            817 |            0.697 |        0.891 |            0.864 |

## Candidates passing all three conditions

|   cross_condition_rank | gene   |   Rest_priority_score |   Stim8hr_priority_score |   Stim48hr_priority_score |   min_priority_score | worst_condition   |
|-----------------------:|:-------|----------------------:|-------------------------:|--------------------------:|---------------------:|:------------------|
|                      1 | SETDB1 |                 0.945 |                    0.915 |                     0.917 |                0.915 | Stim8hr           |
|                      2 | ARNT   |                 0.912 |                    0.916 |                     0.942 |                0.912 | Rest              |
|                      3 | AHR    |                 0.887 |                    0.905 |                     0.909 |                0.887 | Rest              |
|                      4 | NFRKB  |                 0.890 |                    0.893 |                     0.885 |                0.885 | Stim48hr          |
|                      5 | EHMT2  |                 0.896 |                    0.885 |                     0.862 |                0.862 | Stim48hr          |
|                      6 | KDM1A  |                 0.851 |                    0.900 |                     0.913 |                0.851 | Rest              |
|                      7 | GATA3  |                 0.841 |                    0.840 |                     0.906 |                0.840 | Stim8hr           |
|                      8 | TFAM   |                 0.826 |                    0.864 |                     0.883 |                0.826 | Rest              |
|                      9 | TAF13  |                 0.866 |                    0.846 |                     0.823 |                0.823 | Stim48hr          |
|                     10 | PAXIP1 |                 0.910 |                    0.833 |                     0.822 |                0.822 | Stim48hr          |
|                     11 | TADA1  |                 0.831 |                    0.806 |                     0.834 |                0.806 | Stim8hr           |
|                     12 | SGF29  |                 0.806 |                    0.860 |                     0.868 |                0.806 | Rest              |

The cross-condition score is the minimum of the three condition-specific priority scores. This
conservative aggregation rewards a strong weakest condition, but it is **not** a formal
condition-by-perturbation interaction test. Differences between conditions are descriptive.

## Arrayed IL10/IL21 follow-up

| perturbation   |   n_donors |   IL10_mean_delta |   IL10_median_delta |   IL21_mean_delta |   IL21_median_delta |
|:---------------|-----------:|------------------:|--------------------:|------------------:|--------------------:|
| ELOB           |          3 |            12.755 |               7.471 |            -0.110 |              -0.043 |
| MEN1           |          3 |            10.551 |               6.934 |             1.340 |               1.123 |
| NFKB2          |          5 |             4.579 |               2.370 |             1.800 |               1.497 |
| CYB5R4         |          5 |             3.835 |               2.760 |            -0.516 |              -0.380 |
| ATP2A2         |          5 |             1.857 |               1.080 |             5.262 |               4.620 |
| SGF29          |          6 |             1.194 |               1.005 |             3.440 |               2.260 |
| GATA3          |          3 |            -0.019 |               0.024 |             1.847 |               1.330 |
| KDM1A          |          5 |            -0.211 |              -0.160 |             0.186 |               0.320 |
| MED24          |          4 |            -0.276 |              -0.235 |            -1.192 |              -0.770 |

Each delta subtracts the mean of that donor's available NTC, NTC1, NTC2, and NTC3 measurements.
Only descriptive donor-level summaries are shown; no inferential p-values were calculated. The
official source file calls this an arrayed validation experiment, but this report uses the more
limited term **arrayed follow-up** and does not turn a descriptive delta into a validation claim.

## How the priority score should be read

- `n_downstream` is the authors' number of downstream discoveries at 10% FDR. It is sensitive to
  statistical power and cell count and is **not an effect size**.
- `crossdonor_min` and `crossguide` are correlations reported by the source authors. This
  lightweight workflow filters and ranks them; it does not independently recompute them.
- Each metric is percentile-ranked within condition. Their geometric mean is a triage heuristic,
  not a calibrated probability of biological truth.
- The polarization coefficient table is retained only as an official descriptive annotation. It
  is not an extra independent validation layer.

## Deliverables

See `tables/` for all decisions and scores, `figures/` for the four teaching figures,
`methods.md` for the exact contract, and `provenance/manifest.json` for pinned URLs and hashes.
