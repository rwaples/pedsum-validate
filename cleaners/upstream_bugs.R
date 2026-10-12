# Minimal reproductions of the suspected bugs in other packages that pedsum#7
# lists. Each prints whether the bug reproduces at the pinned versions
# (cleaners/install.R). Nothing here has been reported upstream.
#
# Run: pixi run -e r cleaners-bugs

suppressPackageStartupMessages({
  library(kinship2)
  library(pedigree)
  library(nadiv)
})

attempt <- function(expr) tryCatch(expr, error = function(e) e)
report <- function(name, version, reproduced, observed) {
  cat(sprintf("%-40s %-22s reproduced=%s\n    %s\n", name, version, reproduced, observed))
}
ver <- function(pkg) paste(pkg, as.character(packageVersion(pkg)))

# 1. kinship2::fixParents guards the father-sex repair with sex[mindex]
#    (mothers) instead of sex[findex]. The repair is skipped exactly when every
#    mother is recorded male, so a female father then survives.
f <- kinship2::fixParents(id = 1:3, dadid = c(0, 0, 2), momid = c(0, 0, 1), sex = c(1, 2, 2))
report(
  "kinship2 fixParents father-sex guard", ver("kinship2"),
  f$sex[f$id == 2] != 1,
  sprintf("mother 1 recorded male, father 2 recorded female -> fixParents sexes %s (father 2 left female)",
          paste(f$sex, collapse = ","))
)

# 2. kinship2::fixParents with character IDs gives the parents it adds the
#    code 0, while its missid (and pedigree()'s default) is "".
f <- kinship2::fixParents(id = c("a", "b"), dadid = c(NA, "x"), momid = c(NA, "a"), sex = c(2, 1))
p <- attempt(kinship2::pedigree(id = f$id, dadid = f$dadid, momid = f$momid, sex = f$sex))
report(
  "kinship2 fixParents added-parent code", ver("kinship2"),
  inherits(p, "error"),
  sprintf("added row x has parents %s/%s; pedigree() with defaults: %s",
          f$momid[f$id == "x"], f$dadid[f$id == "x"], if (inherits(p, "error")) conditionMessage(p) else "ok")
)

# 3. kinship2::fixParents adds a missing parent used as both mother and father twice.
f <- kinship2::fixParents(id = 1:3, dadid = c(0, 9, 0), momid = c(0, 1, 9), sex = c(2, 1, 2))
report(
  "kinship2 fixParents both-role parent", ver("kinship2"),
  sum(f$id == 9) > 1,
  sprintf("missing 9 is the father of 2 and the mother of 3 -> %d rows with id 9", sum(f$id == 9))
)

# 4. pedigree::add.Inds adds a missing parent used as both dam and sire twice.
a <- pedigree::add.Inds(data.frame(id = c("1", "2", "3", "4"), dam = c(NA, NA, "9", "1"), sire = c(NA, NA, "2", "9")))
report(
  "pedigree add.Inds both-role parent", ver("pedigree"),
  sum(a$id == "9") > 1,
  sprintf("missing 9 is the dam of 3 and the sire of 4 -> %d rows with id 9", sum(a$id == "9"))
)

# 5. nadiv::prepPed finds only cycles made entirely of dam links or of sire
#    links; a cycle mixing the two comes back as a "prepared" pedigree.
ped <- data.frame(
  ID = c("20", "21", "10", "11", "12"),
  Dam = c(NA, NA, "12", "10", "21"),
  Sire = c(NA, NA, "20", "20", "11")
)
printed <- utils::capture.output(r <- attempt(nadiv::prepPed(ped)), type = "message")
report(
  "nadiv prepPed mixed cycle", ver("nadiv"),
  !inherits(r, "error"),
  sprintf("10 -(dam)-> 12 -(sire)-> 11 -(dam)-> 10: prepPed %s; stderr: %s",
          if (inherits(r, "error")) paste("errors:", conditionMessage(r)) else paste("returns", nrow(r), "rows"),
          paste(trimws(printed), collapse = " "))
)
dam_only <- data.frame(ID = c("20", "10", "11"), Dam = c(NA, "11", "10"), Sire = c(NA, "20", "20"))
r2 <- attempt(nadiv::prepPed(dam_only))
cat(sprintf("    control, dam-only cycle 10 <-> 11: %s\n",
            if (inherits(r2, "error")) paste("errors:", trimws(conditionMessage(r2))) else "returns a pedigree"))
