# Pedigree cleaners compared

[pedsum#7](https://github.com/rwaples/pedsum/issues/7) asks how `pedsum validate`'s repairs compare with
the pedigree-cleaning functions of the R packages the benchmark pedigrees come from. Its comparison table
was read from source code. This directory runs every cleaner on the same fixtures and records what each one
did.

## Run it

```
pixi run python cleaners/make_fixtures.py   # cleaners/fixtures/, one pedigree per problem
pixi run -e r cleaners-r                     # R cleaners  -> results/r.tsv, results/<program>/
pixi run cleaners-pedsum                     # pedsum      -> results/pedsum.tsv, results/pedsum-<mode>/
pixi run cleaners-compare                    #             -> results/comparison.md
pixi run -e r cleaners-pwe-r && pixi run cleaners-pwe   # optiSel::PedigWithErrors -> results/PedigWithErrors.md
pixi run -e r cleaners-bugs                  # suspected bugs in the R packages
```

The `r` environment (`pixi.toml`, feature `r`) takes R 4.5 and the heavy dependencies from conda-forge.
`install.R` adds the CRAN-only packages to `.r-lib/` from the Posit snapshot of 2026-10-01: nadiv 2.18.0,
nprcgenekeepr 2.0.0, pedigreemm 0.3-5, pedtools 2.11.0, purgeR 1.8.3, visPedigree 1.10.1, with
optiSel 2.1.0 from the CRAN archive (CRAN archived optiSel on 2026-09-17). kinship2 1.9.6.2 comes from
conda-forge. pedsum is the commit pinned in `pixi.toml`.

## Fixtures

Each fixture is a five-person core (founders 1 F and 2 M, their children 3 F and 4 M, and 5, the child of
3 and 4) with one defect added; `fixtures.tsv` lists them. Missing values are `NA` except in
`zero_missing`. Each program gets the fixture in its own documented input form (column order, sex codes);
`run_r.R` holds the adapters. Two programs have a second variant: `visPedigree-tidyped-selfing`
(`selfing = TRUE`), and `nprcgenekeepr-qcStudbook-nobirth` (birth dates blanked, because a cycle forces a
parent born after its child, and the parent-age check would otherwise stop every cycle fixture first).
`pedtools-as.ped-addMissingFounders` is `as.ped(addMissingFounders = TRUE)`. pedsum runs in six modes:
plain, `--drop-offending`, `--allow-missing-sex`, `--no-sex-check`, and the two options
[pedsum ADR 0006](https://github.com/rwaples/pedsum/blob/main/docs/adr/0006-validate-repairs-compared-with-r-cleaners.md)
added after this comparison, `--missing-parent-token 0` and `--break-cycles`.

The comparison first ran against pedsum 542ef12, and its findings led to ADR 0006
([pedsum#25](https://github.com/rwaples/pedsum/issues/25)). `results/` is now the run against ebcf00c, which
implements the ADR; the table below says where pedsum's cells changed.

## Results

`results/comparison.md` has one cell per fixture and program, and below it everything each program
printed. Codes: `E` refused, `W` warned, `M` printed a message, `S` changed the pedigree silently, `ok`
unchanged; then `+id` row added, `-id` row removed, `dup row(s) removed`, `id:m/f` parents changed,
`id:F>M` sex changed, `reordered` rows in a different order, `CYCLE` output still has a cycle.

### Where the issue's table was wrong or incomplete

Running the code confirmed most of the issue's table. These cells changed (pedsum's as of 542ef12):

| Problem | Program | Issue said | Observed |
|---|---|---|---|
| Duplicate ID | pedsum `--drop-offending` | droppable | Removed **every** row with that ID, so an exact copy deleted the individual and cleared its children's links (`dup_exact`: `-4 5:3/NA`). Since ADR 0006 an exact copy collapses in every mode (`W 1 dup row(s) removed`). |
| Cycle | pedsum `--drop-offending` | drops the cycle | Drops only the cycle members (strongly connected component); descendants stay, with the link into the cycle cleared. |
| Cycle | optiSel `prePed` | parents set to NA | Clears **both** parents of one member per loop, including a parent outside the loop (`cycle2_mixed`: father 20 dropped too). Keeps every individual. |
| Cycle | purgeR `ped_sort` | no check | Crashes: `node stack overflow`. |
| Cycle | nprcgenekeepr | W only | W only without birth dates; with birth dates the parent-age check stops first (E). |
| Own parent | pedigreemm | E (validity) | `editPed` crashes (`node stack overflow`) before the validity check. |
| Mother = father | visPedigree `selfing=TRUE` | allowed | Allowed only when that parent's sex is NA or `monoecious`; a recorded M/F is still E. |
| Both mother and father, sex recorded | pedsum | E | Not E. `sex_role_consistency` is `keep_or_drop`: plain `validate` writes the pedigree with the contradiction and exits 1. |
| Both mother and father | kinship2 `fixParents` | S made female | `fixParents` flips the sex, then `pedigree()` refuses (`Id not male, but is a father`). |
| Missing sex (a parent) | kinship2 `pedigree()` | coded unknown | Refuses an unsexed parent (`Id not female, but is a mother`). |
| Missing-parent code `0` | kinship2 | NA, missid (0 or "") | With character IDs `missid` defaults to `""`, so `0` is an ID and `pedigree()` refuses. |
| Missing-parent code `0` | pedsum `--drop-offending` | E | Dropped the founders whose parents are `0` (`zero_missing`: `-1 -2`), since `0` is read as one parent in both roles. Since ADR 0006 an absent parent `0` BLOCKs in every mode, and `--missing-parent-token 0` reads it as missing (`ok`). |
| ID type | pedsum | integers required | String IDs are accepted (pedsum#16). |
| Parent born after offspring | pedsum | E, droppable | `keep_or_drop`: plain `validate` writes the pedigree and exits 1; `--drop-offending` removes the child. |
| Missing ID | pedtools, pedigreemm, nprcgenekeepr | – | Keep a row with ID `NA` as an individual named `NA`. visPedigree and nadiv drop it with a warning. pedsum refuses, also under `--drop-offending`. |
| Parents listed after offspring | pedtools `as.ped` | S sort (`reorder=TRUE`) | `as.ped(addMissingFounders = TRUE)` keeps the input order; only `ped()` sorts. |

### What changed in pedsum (ADR 0006)

- **Unsexed non-parent** (`missing_sex_nonparent`): every R cleaner accepts it. pedsum alone refused it
  without `--allow-missing-sex`; it now keeps it with sex 0 and a WARNING (`W` in every mode).
- **Exact duplicate rows** (`dup_exact`): visPedigree, optiSel and nprcgenekeepr remove the copy (with a
  warning, a message, or silently), and now so does pedsum, with a `duplicate_rows` finding. The others
  refuse; so does pedsum for an ID on rows that differ.
- **Recorded sex contradicting the role** (`sex_contradicts_role`): pedsum still overrides it, as optiSel,
  nprcgenekeepr and kinship2 `fixParents` do, but reports each override (`S` became `W`).
- **Cycles**: pedsum, visPedigree, pedtools, kinship2 (in `kindepth()`) and purgeR `ped_rename` refuse;
  optiSel cuts parent links and keeps going; nadiv (mixed cycles) and nprcgenekeepr return the cycle.
  pedsum `--break-cycles` clears a self-link (`own_parent`) and, in a cycle, each link to a parent born
  after the child (`cycle2_mixed`, `cycle2_dam_only`); `cycle3_mixed`, whose members share a birth year,
  still BLOCKs.
- **Missing-parent code `0`** (`zero_missing`): pedsum blocks unless `--missing-parent-token 0` is given,
  and then reads `0` as missing, as optiSel, visPedigree, nadiv, pedtools and purgeR do by default.

### optiSel::PedigWithErrors

`results/PedigWithErrors.md`, with parents compared as written. prePed keeps all 10,863 rows, adds 2
founders, clears 5 parent links (4 to break two loops, plus one father written `0`, which it reads as
missing) and changes 1 sex. Every single pedsum mode BLOCKs, on the father written `0`, on the cycles, or
on both, so the file also runs with combined options. With `--missing-parent-token 0 --drop-offending`
pedsum removes 7 rows (cycle members, the self-loop and children born before a parent) and adds 2
founders. With `--missing-parent-token 0 --break-cycles` it keeps every row, as prePed does, and clears 3
links: the father written `0`, a mother born 28 years after her child, and the self-link; adding
`--drop-offending` then removes only the 2 children born before a parent. The results have 2,444
founders after prePed and 2,442 after each pedsum run.

At 542ef12, before ADR 0006, `--drop-offending` alone ran: it also removed 7 rows but added 3 founders,
one of them an individual named `0` for that father.

### Suspected bugs in other packages

`upstream_bugs.R` reproduces all five at the pinned versions. None has been reported upstream; draft
reports are in `upstream/` (nadiv's as a comment on
[nadiv#34](https://github.com/matthewwolak/nadiv/issues/34), which reports the same `numPed` error with no
cause found).

1. kinship2 `fixParents`: the father-sex repair is guarded by `sex[mindex]` instead of `sex[findex]`; it is
   skipped when every mother is recorded male, leaving a female father.
2. kinship2 `fixParents`: with character IDs the parents it adds get code `0` while `missid` is `""`, so
   `pedigree()` with defaults then refuses its output.
3. kinship2 `fixParents`: a missing parent used as both mother and father is added twice.
4. pedigree `add.Inds`: a missing parent used as both dam and sire is added twice.
5. nadiv `prepPed`: a cycle that mixes dam and sire links returns as a prepared pedigree, after an internal
   `numPed` error is printed and swallowed.
