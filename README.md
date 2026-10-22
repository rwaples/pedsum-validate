# pedsum against published pedigree statistics

Runs pedsum on public pedigrees whose statistics have been published, and
compares pedsum's output with those values. The latest results are in
[`results/results.md`](results/results.md). Background on each source, and the
citations, are in [`docs/benchmark-pedigrees.md`](docs/benchmark-pedigrees.md).

## Run it

With [pixi](https://pixi.sh). `pixi.toml` pins
[pedsum](https://github.com/rwaples/pedsum) to a git commit, and adds
[`rdata`](https://pypi.org/project/rdata/) (R `.rda`/`.RData` files) and
[`openpyxl`](https://pypi.org/project/openpyxl/) (`.xlsx` files):

```bash
pixi run harness                      # all datasets
pixi run harness --only atlas,btped   # a subset
```

To check a local pedsum checkout instead, point `pixi.toml`'s `pedsum` entry
at it (`pedsum = { path = "../pedsum", editable = true }`) without
committing that change.

The script needs network access to `raw.githubusercontent.com`,
`ndownloader.figshare.com`, `downloads.sourceforge.net`,
`www.kinsources.net` and `datadryad.org`. It exits 1 if any check is FAIL or
ERROR.

Dryad file downloads need an API token. Log in to https://datadryad.org with
ORCID, create an API account on the *My account* page, and put its
credentials in a file only you can read:

```bash
install -m 600 /dev/null ~/.config/pedsum/dryad.env
# DRYAD_CLIENT_ID=<application id>
# DRYAD_CLIENT_SECRET=<secret>
set -a; . ~/.config/pedsum/dryad.env; set +a
pixi run harness
```

`dryad.py` exchanges them for a token on each run. Without them, the Dryad
datasets ERROR and the rest still run; once a file is in `.cache/`, no token
is needed. A full run takes about 90 seconds once the files are cached
(about 15 s of it is `effective-size` with every estimator, and about 25 s
the phantom-parent rerun of `ne_long_term_contributions`). The largest step is F from the Soay sheep's
6,740-row A⁻¹ (about 4.5 s; the run peaks at 0.9 GB there).

## What it does

For each dataset in [`cases.yaml`](cases.yaml), the script:

1. **Downloads** the file from its pinned URL into `.cache/`, and refuses it
   if its SHA-256 differs from the pinned value. Most files come from a pinned
   commit of the read-only CRAN mirror on GitHub or from Dryad; the others
   are a Figshare file, a SourceForge release tarball and a Kinsources
   export.
2. **Converts** it to pedsum input (`.work/<name>/input.tsv`):
   - Original IDs are mapped to integers in first-appearance order.
   - The dataset's missing-parent tokens (and R `NA`) become `-1`.
   - Sex is recoded.
   - The original ID and the reference-population flag are kept as extra
     columns.
   - `parent_overrides` corrects documented errors first, and an `ainv_list`
     source is turned back into a parent table.

   This step stands in for the `convert` subcommand proposed in rwaples/pedsum#6.
3. **Runs pedsum**: `pedsum validate`, then `summarize` and
   `effective-size` on the repaired output (`validate.tsv.gz`).
   - `effective-size` runs every estimator that can run. On a pedigree with
     any unknown sex it leaves out the three that need sex (`ne_sex_ratio`,
     `ne_variance_family_size`, `ne_hill_overlapping`).
   - Datasets with a reference population add `--reference-col reference`;
     only `ne_individual_delta_f` uses it.
   - Output goes to `.work/<name>/`, with the commands' output logged in
     `pedsum.log`.
4. **Compares** each check in `cases.yaml` with the published value, within
   that check's tolerance. Where the authors deposited per-individual values
   (`reference_values`), it also compares pedsum's value with theirs, id by
   id.
5. **Tabulates** pedsum's headline statistics and all eight Ne estimates for
   every dataset in `results/pedsum_all.tsv`, and in a second table in
   `results/results.md`, whether or not a published value exists. A
   non-numeric Ne cell names why there is no estimate:
   - `skipped: unknown sex`.
   - `missing_metadata:incomplete_parentage`: the pedigree has half-founders; see rwaples/pedsum#9.

   `ne_long_term_contributions_phantom_parents` reruns that estimator on
   `validate --fill-half-founders` output (in `.work/<name>/validate_filled/`
   and `effective_filled/`), which gives each half-founder's missing parent
   its own unrelated founder. It is the same value where there are no
   half-founders. Checks never read the filled pedigree, since filling raises
   the founder counts.
   - `no_estimate:<code>`: the estimator ran but found no estimate
     (`too_few_cohorts`, `no_positive_rate`, `reference_not_inbred`, ...).

## Reading the results

| Status | Meaning |
|---|---|
| PASS | pedsum's own output matches the published value. |
| DIFF | A known convention difference; the `note` column explains it. |
| GAP | pedsum does not report it. The published value is recorded for when it does. |
| FAIL / ERROR | A mismatch, or a run failure. Investigate. |

## Findings so far

[`differences.md`](differences.md) explains where the results differ from published values, and why.

- **Exact matches.**
  - purgeR atlas: total F (197.2809), max F (0.4277344), F of the last row, and
    the founder count.
  - GENLIB `genea140`: every published count (N, sexes, founders, nuclear
    families, full sibships, largest sibship, generation depth).
  - visPedigree `deep_ped`: N, founders and maximum generation, once the 3
    absent parents are added.
  - Equivalent complete generations (`ecg` in `annotated.tsv.gz`): the atlas
    sum (5500.627) and maximum (10.0639), and three named `deep_ped` animals.
  - The F of William Erasmus Darwin (0.06298828).
  - The F values of the Mrode example.
  - The founder counts of Boichard et al. (1997), table II, for both families
    of figure 2 and for each family alone.
  - `BTped`'s structure.
  - Per-individual F against the authors' own: the Soay sheep's ASReml A⁻¹
    (5,068 of 5,068 and 6,740 of 6,740), the black robin's `IndividualF`
    (1,348 of 1,348), and an independent recursion for the red squirrel and
    steelhead.
  - Every pedantics count published for the Soay sheep (Bérénos et al. 2014,
    Table 2) and the Seychelles warbler (Sparks et al., Table S3), except the
    half-sib pairs (below).
- **Ne and lineage statistics moved.** The Ne from individual ΔF, fe, fa and
  Ng checks (purgeR's four studbooks, `deep_ped`, Boichard et al. 1997 and
  the scrub-jay's founder contributions) now run in [pedigree-graph-validate](https://github.com/rwaples/pedigree-graph-validate),
  which reruns purgeR on the same pedigrees and keeps each published value as
  an INFO row. [`differences.md`](differences.md) sections 1 and 2 still
  explain how to read pedsum's `ne` and `ne_unrelated_founders`.
- **Missing sex.** `validate` keeps an individual with unknown sex that is not a
  parent, with sex 0 and a WARNING (pedsum ADR 0006, rwaples/pedsum#25). Before,
  it refused one, and 20 datasets here needed `--allow-missing-sex` for that
  alone, from 1 animal in dama to 4,691 in soay_ped2. Only black_robin still passes the
  flag, for 2 birds used as both mother and father. `effective-size` refuses
  unknown sex only for the three estimators that use it, so
  `ne_individual_delta_f` runs on these studbooks.
- **Rum red deer.** pedsum's F on the Figshare pedigree equals an independent
  tabular-method recomputation, but 50% of calves with both parents and a
  grandparent known are inbred, against 21.9% in Walling et al. (2011). That
  paper used an older pedigree and only calves born 1980–2010, so these checks
  are DIFF.
- **Kinsources "Ancien Régime".** N, parent-child ties (8,373) and maximum
  depth (11) match the statistics Kinsources' Puck software publishes. The
  component count differs because Puck also links spouses, and the sex counts
  differ by one each because pedsum infers the sex of two X-coded parents.
- **Dryad datasets.**
  - pedantics counts a half-sib pair that is also parent–offspring as a
    half-sib pair; pedsum labels it parent–offspring. The Soay and warbler
    half-sib counts differ by those pairs (DIFF).
  - Helgeland's 1,241 birds with two full ancestral generations needs the
    Sequoia dummy parents kept, unlike the deposited script.
  - The song sparrow deposit has no parent table; the harness rebuilds it
    from the A⁻¹. Its F differs from the deposited `f_coeff` by one ancestor
    link, and the published f summary matches neither (DIFF).
  - The scrub-jay's published A has the nadiv 2.17.2 `makeA()` bug, so its
    diagonal disagrees with pedsum's F for 179 of 678 birds (DIFF); pedsum's
    F is correct.
  - The arctic fox sheet's F and the steelhead paper's statistics describe
    fuller versions of their pedigrees, and the *Peromyscus* F apparently
    another version (root cause UNVERIFIED). These checks are DIFF.
- **Rounding in `summary.yaml`.** It rounds `max_F` and `mean_F` to 4 decimals.
  Exact comparisons therefore read `annotated.tsv.gz`.

## Adding a dataset

1. Add an entry under `datasets:` in `cases.yaml`: the URL pinned to a commit
   (or `dryad_file: <id>`, from `dryad.list_files(doi)`), its `sha256`, the column mapping, missing-parent tokens, and `sex_map`.
   - R files also need the `object` name.
   - Text files take `format: whitespace_table`, `csv`, `tsv` (which keeps
     empty fields) or `iur_txt` (Kinsources), gzipped or not. `names` gives
     the columns of a file with no header row, and `member` reads one file
     out of a tar or zip archive.
   - Excel files take `format: xlsx`, with an optional `sheet`.
   - A deposit with only a lower-triangle A⁻¹ list takes `format:
     ainv_list`; the parents are rebuilt by Henderson's rules.
   - `parent_overrides: {id: {mother: ..., father: ...}}` fixes a
     documented error that `validate` cannot repair; give the reason in a
     comment.
   - `reference_values` holds the authors' per-individual values: a column
     of the same file (`{column: F}`), or a separately pinned file (a table
     with `id_column` and `value_column`, an A⁻¹ as `ainv_rdata` or
     `ainv_list`, or an A matrix as `square_matrix_diagonal` with
     `subtract: 1`).
2. Add `checks:` entries. Each needs the published value, its `source`, a `via`
   (see the header of `cases.yaml`), and a `tol` for non-integer values.
   `reference:<name>:<agg>:<column>` compares with a `reference_values`
   entry; `where`, `subset` and `min_grandparents` narrow the rows, and
   `scale` and `offset` rescale the observed value.
3. Add the source and its citation to `docs/benchmark-pedigrees.md`.

Only public files belong here: anonymous downloads, or Dryad files, which
are public but need a free API token.
