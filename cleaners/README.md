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
`pedtools-as.ped-addMissingFounders` is `as.ped(addMissingFounders = TRUE)`. pedsum runs in four modes:
plain, `--drop-offending`, `--allow-missing-sex` and `--no-sex-check`.

## Results

`results/comparison.md` has one cell per fixture and program, and below it everything each program
printed. Codes: `E` refused, `W` warned, `M` printed a message, `S` changed the pedigree silently, `ok`
unchanged; then `+id` row added, `-id` row removed, `id:m/f` parents changed, `id:F>M` sex changed, `CYCLE`
output still has a cycle.

### Where the issue's table was wrong or incomplete

Running the code confirmed most of the issue's table. These cells changed:

| Problem | Program | Issue said | Observed |
|---|---|---|---|
| Duplicate ID | pedsum `--drop-offending` | droppable | Removes **every** row with that ID, so an exact copy deletes the individual and clears its children's links (`dup_exact`: `-4 5:3/NA`). |
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
| Missing-parent code `0` | pedsum `--drop-offending` | E | Drops the founders whose parents are `0` (`zero_missing`: `-1 -2`), since `0` is read as one parent in both roles. |
| ID type | pedsum | integers required | String IDs are accepted (pedsum#16). |
| Parent born after offspring | pedsum | E, droppable | `keep_or_drop`: plain `validate` writes the pedigree and exits 1; `--drop-offending` removes the child. |
| Missing ID | pedtools, pedigreemm, nprcgenekeepr | – | Keep a row with ID `NA` as an individual named `NA`. visPedigree and nadiv drop it with a warning. pedsum refuses, also under `--drop-offending`. |

### What only pedsum does

- **Unsexed non-parent** (`missing_sex_nonparent`): every R cleaner accepts it; pedsum alone refuses it
  without `--allow-missing-sex`. This matches the published-pedigree evidence in the issue's comment.
- **Exact duplicate rows**: visPedigree, optiSel and nprcgenekeepr remove the copy (with a warning, a
  message, or silently); every other program refuses, as pedsum does.
- **Cycles**: pedsum, visPedigree, pedtools, kinship2 (in `kindepth()`) and purgeR `ped_rename` refuse;
  optiSel cuts parent links and keeps going; nadiv (mixed cycles) and nprcgenekeepr return the cycle.

### optiSel::PedigWithErrors

`results/PedigWithErrors.md`. prePed keeps all 10,863 rows, adds 2 founders, clears 4 parent links (two
loops) and changes 1 sex. Plain pedsum BLOCKs on the cycles; `--drop-offending` removes 7 rows (cycle
members, the self-loop and children born before a parent) and adds 3 founders. One of the 3 is ID `0`:
the dataset has one father written `0`, which prePed reads as missing and pedsum reads as an individual.

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
