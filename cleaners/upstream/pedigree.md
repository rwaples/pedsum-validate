<!-- DRAFT for review, not sent. The CRAN package `pedigree` has no BugReports or URL field; the only contact is the maintainer address in its DESCRIPTION. Reproduced by cleaners/upstream_bugs.R. -->

Subject: pedigree 1.4.2: add.Inds() adds a parent twice when it is both dam and sire

`add.Inds()` adds one row per missing dam and one per missing sire, so an ID that is missing and appears in
both columns is added twice:

```r
a <- pedigree::add.Inds(data.frame(
  id = c("1", "2", "3", "4"), dam = c(NA, NA, "9", "1"), sire = c(NA, NA, "2", "9")
))
a$id
#> [1] "9" "9" "1" "2" "3" "4"
```

The rows come from `c(ndams, nsires)` without `unique()` across the two vectors. An individual cannot be
both dam and sire, so the input is wrong, but the duplicate row makes later steps fail on a duplicated ID
rather than on the actual conflict. `unique(c(ndams, nsires))`, perhaps with a warning naming IDs found in
both columns, would fix it.

R 4.5, pedigree 1.4.2 (CRAN).
