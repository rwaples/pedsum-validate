# Where pedsum's results differ from published values

Notes on the [harness results](results/results.md) as of commit `9bcc9d0`
(pedsum 0.14.0 with unreleased changes, pedigree-graph 0.12.1). Every count
and every F value checked matches exactly. The differences below all come
from convention: what is computed, over which individuals, and how it is
reported.

## 1. Ne from individual ΔF: `ne` is 13–20% above purgeR's published value

This is the one difference that matters in practice.

| Studbook | pedsum `ne` (exponent 1/t) | `ne_unrelated_founders` (1/(t−1)) | purgeR / Heredity 2021 | `ne` ÷ published |
|---|---|---|---|---|
| atlas | 15.79 | 14.01 | 14.01041 | 1.13 |
| dama | 12.63 | 11.10 | 11.09927 | 1.14 |
| dorcas | 45.66 | 39.32 | 39.32125 | 1.16 |
| arrui | 4.59 | 3.84 | 3.83865 | 1.20 |

All values are over purgeR's reference population (`target == 1`, passed with
`effective-size --reference-col`).

- **The inputs agree.** F and equivalent complete generations (t) match purgeR
  exactly.
- **The exponent differs.** pedsum's headline `ne` uses
  ΔFᵢ = 1 − (1 − Fᵢ)^(1/t). purgeR uses 1/(t − 1) (`purgeR/R/Ne.R:44`).
  pedigree-graph's docstring cites the 1/t form as Gutiérrez et al. (2008),
  eq. 2, and describes `ne_unrelated_founders` as its own diagnostic for
  pedigrees whose founders really were unrelated. TODO: confirm the 1/t form
  against the paper.
- **The gap grows as pedigrees get shallower.** Subtracting 1 from t matters
  more when t is small, so arrui (the shallowest) differs most.
- **Comparing with purgeR or the Heredity paper:** read
  `ne_unrelated_founders`, not `ne`. A 13–20% gap between pedsum's `ne` and a
  purgeR value is this convention, not an error.

## 2. The reference population moves Ne as much as the formula

- **Default reference.** Without `--reference-col`, `ne_individual_delta_f`
  averages over the last observed depth. For atlas that gives 18.41 (the 1/t
  form), against 15.79 over purgeR's reference animals: a 17% swing from that
  choice alone.
- **Practice.** Published Ne values almost always name their reference group,
  so comparisons should pass `--reference-col`.

## 3. Ne over all rows: rows with t ≤ 1 (minor, about 2%)

- **Values.** For atlas over every row, purgeR gives 8.18 and pedigree-graph
  gives 8.03, both with 1/(t − 1).
- **Cause.** purgeR keeps individuals with t ≤ 1 and gives them ΔF = 0;
  pedigree-graph leaves them out.
- **Where it matters.** Only for averages over a whole pedigree that includes
  shallow rows. The harness reports this check as DIFF.

## Reporting conventions, not disagreements

- **Generation numbering.** GENLIB ("18 generations") and visPedigree
  (`MaxGen` 13) count founders as generation 1. pedsum's `max_depth` counts
  them as 0, so the harness adds 1 before comparing.
- **Rounding.**
  - `summary.yaml` rounds `max_F` and `mean_F` to 4 decimals (atlas max F
    shows as 0.4277, against 0.4277344).
  - `effective_size.yaml` rounds Ne to 4 decimals.
  - Exact comparisons read `annotated.tsv.gz`, or use a tolerance of 1e-4.
- **Missing sex.**
  - `validate` refuses any individual with unknown sex that never bred. That
    affects dama (1), arrui (1), dorcas (7) and `deep_ped` (521 rows) unless
    `--allow-missing-sex` is given.
  - This is input policy (see issue #7), not a difference in any computed
    value. With the flag, every check on those pedigrees matches.

## Not yet comparable

pedsum does not compute these yet, so differences may still turn up here:

- founder equivalents (fe)
- effective number of ancestors (fa)
- founder genome equivalents (fg)
- mean kinship
- complete generations

See `docs/missing-statistics.md`. One is already predictable. In dorcas,
contributions from founders with only one known parent sum to 0.938. Using
them as they are gives fe = 15.20; rescaling them to sum to 1 gives purgeR's
13.39. These were computed with a scratch script during the survey, not with
pedsum.
