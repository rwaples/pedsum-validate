# Where pedsum's results differ from published values

Notes on the [harness results](results/results.md) as of commit `b9ce76d`
with the Dryad datasets added (pedsum 0.14.0 with unreleased changes,
pedigree-graph 0.12.1). Every count and every F value computed on the same
pedigree as the published one matches exactly; the
[exact matches](#exact-per-individual-f-matches) below compare F bird by
bird. The differences come from convention (what is computed, over which
individuals, and how it is reported), from the published value describing a
different pedigree or a different definition, or, for the Florida scrub-jay
(section 9), from a bug in the software that produced the published value.

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
  - The 1/t form is Gutiérrez et al. (2008), eq. 2, p. 362:
    "ΔF_i = 1 − ᵗ√(1 − F_i), where t is the 'equivalent complete
    generations' [3,18] calculated for the pedigree of the individual as the
    sum over all known ancestors of the term of (½)^n". Eq. 1 (p. 361) is
    F_t = 1 − (1 − ΔF)^t, and §2.1 (p. 362) gives Ne = 1/(2ΔF̄) over the
    reference subpopulation.
  - The 1/(t − 1) form is Gutiérrez, Cervantes & Goyache (2009), *J Anim
    Breed Genet* 126(4):327–332. Its abstract says F(t) = 1 − (1 − ΔF)^t
    "should be more correctly written in real animal populations as
    F(t) = 1 - (1-DeltaF)(t-1)" (PubMed's plain text; the exponent is t − 1).
    purgeR cites both papers.
  - pedigree-graph's docstring cites eq. 2 correctly but describes
    `ne_unrelated_founders` as its own diagnostic. Its exponent is the 2009
    one.
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

## 4. Rum red deer: a different pedigree and a different subset

- **Values.** On the Figshare file, 50.2% of individuals with both parents
  and at least one grandparent known have F > 0 (mean F 0.01151). Walling et
  al. (2011) report 21.9% (mean F 0.00724). With all four grandparents known
  the figures are 70.5% against 42.1%.
- **F itself agrees.** An independent tabular-method recomputation on the same
  file matches pedsum's F for every individual.
- **Cause.** Walling used the 2011 pedigree and calves born 1980–2010 only.
  The Figshare file is the 2024 SNP-based (Sequoia) pedigree of Hewett et al.
  and has no birth-year column, so the subset cannot be rebuilt.

## 5. Kinsources "Ancien Régime": Puck's definitions

- **Components** 677 against Puck's 5. Puck links spouses as well as parents
  and children. Adding spouse ties gives 5.
- **Men and women** each one more than Puck. Two individuals coded X (unknown
  sex) are parents, and `validate` infers their sex from their role.
- **Mean depth** 2.36 in Puck. Puck does not define it; shortest-line depth
  + 1 gives 2.370 and complete generations + 1 gives 2.332.

## 6. pedantics half-sib pairs include pairs that are also parent–offspring

- **Values.** Soay sheep (Bérénos et al. 2014, Table 2): maternal half-sib
  pairs 13,367 against pedsum's 13,365 in Pedigree 1 and 19,564 against
  19,563 in Pedigree 2; paternal half-sib pairs 13,451 against 13,447 and
  48,138 against 48,120. Seychelles warbler (Sparks et al., Table S3): 1,669
  against 1,655 maternal and 2,454 against 2,435 paternal.
- **Cause.** pedantics counts every pair that shares a dam (or sire) and is
  not full-sib. pedsum's `relationship_pairs` gives each pair one label, its
  closest relationship. A pair that shares a dam, where one is also the
  other's sire, is FO there, not MHS. Soay Pedigree 1 has 2 such dam-sharing
  pairs and 4 sire-sharing ones, Pedigree 2 has 1 and 18, the warbler 14 and
  19.
- **The counts agree.** Half the sum of the per-individual
  `n_mat_half_sibs` and `n_pat_half_sibs` columns gives the warbler's 1,669
  and 2,454 exactly. Every other count in the two tables matches; their mean
  pairwise relatedness is gap C1.

## 7. Helgeland house sparrow: 1,241 needs the Sequoia dummy parents

- **Values.** Niskanen et al. (2020, Methods) "reduced the sample size to
  1,241 individuals" with at least two full ancestral generations. pedsum
  gives 1,241 genotyped birds with all four grandparents known.
- **Cause.** The deposited `pedigree.txt` has 3,556 rows, 440 of them
  Sequoia dummy parents. With the dummies kept as parents, the count is
  1,241. The deposited `Estimating_pedigree_F.R` removes them first, which
  gives 490.
- **Not comparable.** The deposit has no pedigree F to compare with.

## 8. Mandarte song sparrow: two pedigrees one link apart

- **The pedigree.** The deposit (Dryad `p7p1jb3`) has no parent table, so
  the harness rebuilds one from the fitness analysis's A⁻¹: 3,062 birds, 52
  without parents. pedsum's F equals F from that A⁻¹ to 3e-13. (The other
  deposit, `p9s04`, has no individual ids.)
- **The authors' f.** pedsum matches the deposited `f_coeff` for 1,883 of
  the 2,821 phenotyped birds. The other 938 are higher in pedsum, by up to
  0.088. Giving A⁻¹ row 173 (an unphenotyped bird with 21 offspring) no
  parents reproduces all 2,821, so `f_coeff` and the A⁻¹ come from pedigrees
  that differ in that one ancestor's link.
- **The published summary matches neither.** Wolak et al. (2018, Results):
  "mean f was 0.074 ± 0.052 (range 0.000–0.347, 7.4% zeroes)". The A⁻¹
  pedigree gives mean 0.0768, maximum 0.3574 and 6.8% zeros; the deposited
  `f_coeff` gives mean 0.0758, maximum 0.357 and 7.48% zeros. These checks
  are DIFF.

## 9. Florida scrub-jay: the published A has a nadiv bug

- **Values.** The authors' F is the diagonal of their relationship matrix
  minus 1 (`cr_ped_20230512_relatedness_matrix.txt`, built with nadiv
  2.17.2 `makeA()`). pedsum matches it for 499 of the 678 birds (largest
  difference 0.0625). It finds 126 inbred birds and a total F of 8.697,
  against 222 and 10.626 from the matrix.
- **Cause.** nadiv's NEWS for 2.18.0: a bug in `makeAinv()`, `makeGGAinv()`
  and `makeDiiF()` "caused coefficients of inbreeding (`f`) and Mendelian
  sampling variances (`dii`) to be ordered incorrectly", which "did cause
  matrices built directly from `dii` to be incorrect - namely the __A__
  matrix from `makeA()`". The fix is commit
  [`a410517`](https://github.com/matthewwolak/nadiv/commit/a410517bf76be2fbead3be746f3729dcbe488a04)
  (2024-05-17). 23 diagonal entries of the deposited matrix are below 1,
  which no valid A allows.
- **pedsum's F is correct.** An independent tabular A on the same pedigree
  gives pedsum's F for every bird. A scratch emulation of nadiv 2.17.2's
  `prepPed()` and `makeA()` reproduces 620 of the 678 deposited diagonal
  entries; why the other 58 differ is UNVERIFIED.
- **Founders.** The paper's 74 ancestors are the resident and translocated
  birds (`ANCESTOR = 1`); 39 of them have known parents in donor sites.
  pedsum counts the 106 rows with no known parent (89, plus the 17 parents
  of translocated birds that `validate` adds).

## 10. Brookfield Zoo *Peromyscus*: F from another pedigree version

- **Values.** The deposited `GEN` equals pedsum's depth on all 11,483 rows.
  The deposited F agrees with pedsum's within 1e-6 for 1,318 of the 11,482
  rows that have one, and within 1e-4 for 3,844. Its sum is 1,504.9558,
  against pedsum's 1,508.302.
- **Pattern.** F agrees through `GEN` 4. pedsum is then higher, by about
  3e-4 by `GEN` 20 in every line, and 3 families (23 rows) differ by up to
  0.224. The deposited F is truncated to 4 decimals.
- **Cause.** pedsum equals an independent recursion on the deposited
  `DAM`/`SIRE` for every row, so the authors' F was presumably computed on
  another version of the pedigree, then truncated. The root cause is
  UNVERIFIED.

## 11. Scandinavian arctic fox: F from parentage the sheet lacks

- **Values.** pedsum matches the sheet's F for 207 of its 247 animals. The
  sheet's F sums to 13.53125, pedsum's to 10.84375.
- **Cause.** 40 animals descend from sires whose ancestry is not in the
  sheet: offspring of Male3 × Fox20 have F = 0.125 in the sheet, but 0 from
  the parentage given. 4 animals have F > 0 with a parent coded 0.
- **A repair.** Fox5, an adult with no birth year or litter, is listed as
  the dam of her own litter (Male1 × Fox5). `parent_overrides` makes her a
  founder, since `summarize` refuses an individual that is its own parent.
- **Counts.** The abstract's 205 individuals and 5 founders describe the
  authors' pedigree. The sheet has 247 rows; `validate` adds 5 sires with no
  row, giving 252 individuals and 16 founders.

## 12. Steelhead: the deposit is a subset

- **Values.** The Dryad file has 6,173 fish, plus 4 sires without rows that
  `validate` adds (6,177), and its deepest fish are at depth 3. The abstract
  reports 6,602 fish over four generations, 15.7% of F4 with Δf > 0, and
  Ñe = 107.9.
- **Cause.** The deposit lacks 429 of the paper's fish and has no generation
  column, so none of these can be rebuilt. pedsum's F on the file equals an
  independent recursion.

## 13. Chatham Island black robin: founders by convention

- **Values.** Weiser counts 2 founders, the pair of the 1979–82 bottleneck.
  pedsum counts 6 rows with no known parent.
- **Cause.** Kennedy et al.'s DatasheetC traces the bottleneck male's
  ancestry to his grandparents. This is a convention; F matches the authors'
  for all 1,348 birds.

## Exact per-individual F matches

pedsum's F equals F computed by other software, or by an independent
recursion, for every individual of these pedigrees:

- **Soay sheep against ASReml.** F = diag(A) − 1 from the authors'
  `asreml.Ainverse` output: 5,068 of 5,068 (Pedigree 1) and 6,740 of 6,740
  (Pedigree 2), each within 1e-13.
- **Black robin.** 1,348 of 1,348 against Kennedy et al.'s `IndividualF`,
  and all 1,104 birds of Weiser et al.'s `DatasetS1`.
- **Kluane red squirrel and steelhead.** pedsum's F equals an independent
  tabular-method recursion on each file (sum of F 2.2229 and 12.84375).
  Neither paper publishes F, so these checks test pedsum only against that
  recursion.

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
  - This is input policy (see issue rwaples/pedsum#7), not a difference in any computed
    value. With the flag, every check on those pedigrees matches. ADR 0006 in pedsum drops
    the requirement for individuals that never bred (rwaples/pedsum#25).
- **Cleaning.** The R package that published a value may have cleaned the pedigree
  differently. [`cleaners/`](cleaners/README.md) runs eight R cleaners and pedsum on the
  same fixtures. The differences most likely to move a published count:
  - purgeR turns a parent with no row into "unknown"; pedsum adds a founder row, so
    founder and half-founder counts differ.
  - optiSel `prePed` breaks a cycle by clearing parents and keeps every individual; pedsum
    refuses a cycle, or removes its members under `--drop-offending`.
  - optiSel, visPedigree, nadiv, pedtools and purgeR read a parent written `0` as missing;
    pedsum reads it as an ID unless it is recoded.

## Not yet comparable

pedsum does not compute these yet, so differences may still turn up here:

- founder equivalents (fe), and the expected genetic contributions they
  are built from (the scrub-jay's 24% and 32%)
- effective number of ancestors (fa)
- founder genome equivalents (fg)
- mean kinship (the Soay sheep's and the warbler's mean pairwise
  relatedness)
- complete generations
- contributions of a founder group (the song sparrow's immigrant genetic
  group coefficient)

See `docs/missing-statistics.md`. One is already predictable. In dorcas,
contributions from founders with only one known parent sum to 0.938. Using
them as they are gives fe = 15.20; rescaling them to sum to 1 gives purgeR's
13.39. These were computed with a scratch script during the survey, not with
pedsum.
