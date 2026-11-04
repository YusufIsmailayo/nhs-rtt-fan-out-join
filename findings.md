# Findings: fan-out join, NHS RTT incomplete pathways, August 2026

Generated from the notebook outputs in `data/gold/`. Reconciliation gate:
**53 of 53 checks pass** (`data/gold/00_reconciliation/reconciliation.csv`).

## By treatment function: correct grain vs fan-out (≥20% main-ICB lookup)

Sorted by gap (fan-out minus correct, percentage points).

| tf_name | pathways_correct | pathways_fanout | denominator_inflation | pct_over_18_correct | pct_over_18_fanout | gap_points |
|---|---|---|---|---|---|---|
| General Internal Medicine Service | 28,907 | 30,794 | ×1.065 | 25.82% | 26.51% | +0.69 |
| Neurology Service | 205,335 | 238,179 | ×1.160 | 37.63% | 38.02% | +0.39 |
| Trauma and Orthopaedic Service | 843,419 | 967,860 | ×1.148 | 38.90% | 39.28% | +0.38 |
| Ear Nose and Throat Service | 589,316 | 651,818 | ×1.106 | 43.23% | 43.57% | +0.33 |
| Cardiology Service | 360,799 | 401,432 | ×1.113 | 32.11% | 32.42% | +0.31 |
| Oral Surgery Service | 315,652 | 345,911 | ×1.096 | 46.18% | 46.34% | +0.15 |
| Gastroenterology Service | 357,430 | 390,239 | ×1.092 | 30.32% | 30.46% | +0.14 |
| Other - Paediatric Services | 321,302 | 349,997 | ×1.089 | 34.03% | 34.15% | +0.12 |
| General Surgery Service | 384,427 | 429,402 | ×1.117 | 36.82% | 36.93% | +0.10 |
| Other - Medical Services | 620,378 | 676,118 | ×1.090 | 29.89% | 29.95% | +0.06 |
| Other - Surgical Services | 473,107 | 528,513 | ×1.117 | 33.10% | 33.12% | +0.01 |
| Urology Service | 366,130 | 409,851 | ×1.119 | 35.15% | 35.15% | +0.01 |
| Gynaecology Service | 585,378 | 646,342 | ×1.104 | 40.39% | 40.29% | -0.10 |
| Plastic Surgery Service | 108,674 | 121,489 | ×1.118 | 40.53% | 40.42% | -0.12 |
| Other - Mental Health Services | 3,347 | 3,372 | ×1.007 | 18.05% | 17.91% | -0.13 |
| Elderly Medicine Service | 27,386 | 29,146 | ×1.064 | 15.68% | 15.39% | -0.29 |
| Neurosurgical Service | 53,980 | 60,169 | ×1.115 | 38.04% | 37.66% | -0.37 |
| Respiratory Medicine Service | 182,132 | 201,861 | ×1.108 | 25.83% | 25.36% | -0.48 |
| Rheumatology Service | 118,118 | 131,108 | ×1.110 | 29.61% | 29.13% | -0.48 |
| Other - Other Services | 158,987 | 195,269 | ×1.228 | 23.55% | 22.86% | -0.69 |
| Ophthalmology Service | 622,784 | 742,735 | ×1.193 | 27.76% | 27.04% | -0.72 |
| Cardiothoracic Surgery Service | 8,551 | 9,998 | ×1.169 | 26.07% | 25.33% | -0.74 |
| Dermatology Service | 422,625 | 490,311 | ×1.160 | 30.96% | 30.21% | -0.75 |

## Rank changes (league table of % over 18 weeks, worst = 1)

| tf_name | rank_correct | rank_fanout |
|---|---|---|
| Neurosurgical Service | 6 | 7 |
| Neurology Service | 7 | 6 |
| Dermatology Service | 13 | 14 |
| Gastroenterology Service | 14 | 13 |
| Cardiothoracic Surgery Service | 18 | 20 |
| General Internal Medicine Service | 20 | 18 |

## Three lookups compared

| lookup | rows | england_pathways | inflation | england_pct_over_18 | max_abs_tf_gap_points |
|---|---|---|---|---|---|
| none (correct grain) | 501,422 | 7,158,164 | ×1.000 | 34.79% | 0.00 |
| main ICBs (>= 20% of trust list) | 564,592 | 8,051,914 | ×1.125 | 34.71% | 0.75 |
| every ICB the trust serves | 15,845,245 | 240,286,507 | ×33.568 | 35.71% | 2.47 |

## Threshold sensitivity (what counts as a "main" ICB)

| threshold | providers_repeated | providers_dropped | england_inflation | england_pct_over_18 | min_tf_gap | max_tf_gap | tfs_moved_0_5_plus |
|---|---|---|---|---|---|---|---|
| 10% | 174.0 | 0.0 | ×1.351 | 34.36% | -2.48 | +4.05 | 10.0 |
| 15% | 122.0 | 0.0 | ×1.210 | 34.69% | -1.62 | +2.91 | 9.0 |
| 20% | 87.0 | 2.0 | ×1.125 | 34.71% | -0.75 | +0.69 | 5.0 |
| 25% | 63.0 | 4.0 | ×1.086 | 34.89% | -1.89 | +0.82 | 4.0 |
| 30% | 51.0 | 4.0 | ×1.073 | 34.90% | -1.89 | +0.86 | 4.0 |
| 40% | 15.0 | 10.0 | ×1.012 | 35.14% | -1.66 | +2.23 | 5.0 |
