<!-- DRAFT for review, not filed. Target: https://github.com/mayoverse/kinship2/issues (DESCRIPTION has no BugReports field). One issue covering three fixParents() bugs; split if the maintainers prefer. Reproduced by cleaners/upstream_bugs.R. -->

# `fixParents()`: three problems with the parents it adds or fixes

kinship2 1.9.6.2 (CRAN), R 4.5. Each example is self-contained.

## 1. The father-sex repair is guarded by the mothers' sex

```r
f <- kinship2::fixParents(id = 1:3, dadid = c(0, 0, 2), momid = c(0, 0, 1), sex = c(1, 2, 2))
f$sex
#> [1] 2 2 2
```

Individual 1 is recorded male and used as a mother; individual 2 is recorded female and used as a father.
`fixParents()` makes 1 female, but leaves 2 female, so `pedigree()` on the result fails with
"Id not male, but is a father: 2".

The father block tests the mothers:

```r
if (any(sex[mindex] != 1)) {
    dadnotmale <- unique((id[findex])[sex[findex] != 1])
    sex[id %in% dadnotmale] <- 1
}
```

The guard is almost always TRUE, so the bug shows only when every mother is recorded male. The guard should
be `any(sex[findex] != 1)`. (`findex` and `mindex` also include 0 for missing parents, which `sex[0]` drops
silently.)

## 2. With character IDs, added parents get `0` while `missid` is `""`

```r
f <- kinship2::fixParents(id = c("a", "b"), dadid = c(NA, "x"), momid = c(NA, "a"), sex = c(2, 1))
f[f$id == "x", ]
#>   id momid dadid sex
#> 3  x     0     0   1
kinship2::pedigree(id = f$id, dadid = f$dadid, momid = f$momid, sex = f$sex)
#> Error: Value of 'dadid' not found in the id list 0
```

For non-numeric IDs `fixParents()` sets `missid <- ""`, but the rows it adds use `rep(0, ...)` for their
parents. `pedigree()` with its default `missid` then reads `"0"` as an ID. Using `missid` for the added
rows' parents would keep the output consistent with the input's convention.

## 3. A missing parent used as both mother and father is added twice

```r
f <- kinship2::fixParents(id = 1:3, dadid = c(0, 9, 0), momid = c(0, 1, 9), sex = c(2, 1, 2))
sum(f$id == 9)
#> [1] 2
```

9 is the father of 2 and the mother of 3, and has no row. `fixParents()` adds one row for 9 as a missing
father and another as a missing mother, so `pedigree()` then fails with "Duplicate subject id: 9", which
hides the real problem (one individual in both roles). Adding each missing ID once, and reporting the
role conflict, would give a clearer error.
