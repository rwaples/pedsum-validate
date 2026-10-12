# Install the CRAN-only pedigree cleaners into R_LIBS_USER (.r-lib/) at the
# versions pinned below. conda-forge supplies everything else (pixi.toml,
# feature r). Run through `pixi run -e r r-setup`; a second run installs nothing.

snapshot <- "https://packagemanager.posit.co/cran/2026-10-01"

# CRAN versions the comparison was run against. optiSel was archived on
# 2026-09-17, so it comes from the CRAN archive instead of the snapshot.
pinned <- c(
  nadiv = "2.18.0",
  nprcgenekeepr = "2.0.0",
  optiSolve = "1.0.1",
  pedigree = "1.4.2",
  pedigreemm = "0.3-5",
  pedmut = "0.9.1",
  pedtools = "2.11.0",
  purgeR = "1.8.3",
  visPedigree = "1.10.1",
  optiSel = "2.1.0"
)
archive <- c(
  optiSel = "https://cran.r-project.org/src/contrib/Archive/optiSel/optiSel_2.1.0.tar.gz"
)

lib <- Sys.getenv("R_LIBS_USER")
if (!nzchar(lib)) stop("R_LIBS_USER is unset; run through `pixi run -e r`")
dir.create(lib, showWarnings = FALSE, recursive = TRUE)
.libPaths(c(lib, .libPaths()))

installed_version <- function(pkg) {
  tryCatch(as.character(packageVersion(pkg, lib.loc = lib)), error = function(e) NA_character_)
}
at_pin <- function(pkg) {
  v <- installed_version(pkg)
  !is.na(v) && package_version(v) == package_version(pinned[[pkg]])
}
need <- names(pinned)[!vapply(names(pinned), at_pin, logical(1))]

from_snapshot <- setdiff(need, names(archive))
if (length(from_snapshot)) {
  install.packages(
    from_snapshot,
    lib = lib, repos = snapshot, type = "source",
    dependencies = c("Depends", "Imports", "LinkingTo"), Ncpus = 4
  )
}
for (pkg in intersect(need, names(archive))) {
  install.packages(archive[[pkg]], lib = lib, repos = NULL, type = "source")
}

got <- vapply(names(pinned), installed_version, character(1))
bad <- names(pinned)[!vapply(names(pinned), at_pin, logical(1))]
if (length(bad)) {
  stop("not at the pinned version: ", paste0(bad, " (", got[bad], " != ", pinned[bad], ")", collapse = ", "))
}
cat("R cleaners installed:", paste0(names(got), " ", got, collapse = ", "), "\n")
cat("kinship2 (conda-forge):", as.character(packageVersion("kinship2")), "\n")
