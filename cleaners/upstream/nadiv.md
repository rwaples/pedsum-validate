<!-- DRAFT for review, not posted. Target: a comment on https://github.com/matthewwolak/nadiv/issues/34 ("issue with prepPed", open), which reports the same numPed() error with no cause found. Reproduced by cleaners/upstream_bugs.R. -->

A pedigree loop that mixes dam and sire links produces this error. `prepPed()` detects loops made only of
dams or only of sires, but not mixed ones, so the topological sort leaves an individual before its dam and
the internal `numPed()` call fails.

nadiv 2.18.0, R 4.5:

```r
ped <- data.frame(
  ID   = c("20", "21", "10", "11", "12"),
  Dam  = c(NA,   NA,   "12", "10", "21"),
  Sire = c(NA,   NA,   "20", "20", "11")
)
# 10 -(dam)-> 12 -(sire)-> 11 -(dam)-> 10
out <- nadiv::prepPed(ped)
#> Error in numPed(ped_fixed_ord[, 1:3]) :
#>   Offspring appearing before their dams: first use the 'prepPed' function
nrow(out)
#> [1] 5
```

In 2.18.0 the error is printed but caught, and `prepPed()` returns the pedigree with the loop still in it.
A loop through dams only is reported clearly:

```r
nadiv::prepPed(data.frame(ID = c("20", "10", "11"), Dam = c(NA, "11", "10"), Sire = c(NA, "20", "20")))
#> Error: Problem: infinite pedigree loop involving individual10and dam/female ancestors
```

A check over both parent columns together (for example, a topological sort over the dam and sire edges at
once) would report the mixed case the same way.
