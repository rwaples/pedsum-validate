# Run each R package's pedigree cleaner on every fixture and record what it did.
#
# For each fixture and program this writes the cleaned pedigree, normalized to
# id, mother, father, sex (sex M/F/U, or "-" when the program has no sex;
# missing NA), to cleaners/results/<program>/<fixture>.tsv when the program
# returned one, and one row to cleaners/results/r.tsv: whether it errored, and
# every error, warning, message and line it printed.
#
# Each adapter passes the fixture to the package in that package's documented
# input form (column order, sex codes) and keeps the fixture's missing-parent
# token, so the zero_missing fixture hands every package a literal "0".
#
# Run: pixi run -e r cleaners-r

suppressPackageStartupMessages({
  library(optiSel)
  library(visPedigree)
  library(nadiv)
  library(kinship2)
  library(purgeR)
  library(pedtools)
  library(pedigreemm)
  library(nprcgenekeepr)
})

args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
fixtures_dir <- file.path(here, "fixtures")
results_dir <- file.path(here, "results")

read_fixture <- function(path) {
  utils::read.delim(path, colClasses = "character", na.strings = "NA")
}

sex_word <- function(s) ifelse(is.na(s), NA_character_, ifelse(s == "M", "male", "female"))
sex_num <- function(s, unknown) ifelse(is.na(s), unknown, ifelse(s == "M", 1L, 2L))

norm_sex <- function(s) {
  s <- tolower(as.character(s))
  out <- rep("U", length(s))
  out[s %in% c("m", "male", "1")] <- "M"
  out[s %in% c("f", "female", "2")] <- "F"
  out
}

norm_parent <- function(p, missing = character()) {
  p <- as.character(p)
  p[p %in% missing] <- NA_character_
  p
}

result <- function(id, mother, father, sex) {
  data.frame(
    id = as.character(id), mother = as.character(mother), father = as.character(father),
    sex = sex, stringsAsFactors = FALSE
  )
}

# name -> function(fixture data.frame) -> normalized data.frame
programs <- list(
  "optiSel-prePed" = function(x) {
    p <- optiSel::prePed(data.frame(
      Indiv = x$id, Sire = x$father, Dam = x$mother, Sex = sex_word(x$sex),
      Born = as.numeric(x$birth_year), stringsAsFactors = FALSE
    ))
    result(p$Indiv, norm_parent(p$Dam, "0"), norm_parent(p$Sire, "0"), norm_sex(p$Sex))
  },
  "visPedigree-tidyped" = function(x) {
    p <- visPedigree::tidyped(data.frame(
      Ind = x$id, Sire = x$father, Dam = x$mother, Sex = sex_word(x$sex), stringsAsFactors = FALSE
    ))
    result(p$Ind, p$Dam, p$Sire, norm_sex(p$Sex))
  },
  "visPedigree-tidyped-selfing" = function(x) {
    p <- visPedigree::tidyped(
      data.frame(Ind = x$id, Sire = x$father, Dam = x$mother, Sex = sex_word(x$sex), stringsAsFactors = FALSE),
      selfing = TRUE
    )
    result(p$Ind, p$Dam, p$Sire, norm_sex(p$Sex))
  },
  "nadiv-prepPed" = function(x) {
    p <- nadiv::prepPed(
      data.frame(ID = x$id, Dam = x$mother, Sire = x$father, sex = x$sex, stringsAsFactors = FALSE),
      gender = "sex"
    )
    result(p$ID, norm_parent(p$Dam, c("0", "*")), norm_parent(p$Sire, c("0", "*")), norm_sex(p$sex))
  },
  "kinship2-pedigree" = function(x) {
    p <- kinship2::pedigree(id = x$id, dadid = x$father, momid = x$mother, sex = sex_num(x$sex, 3L))
    kinship2::kindepth(p) # pedigree() does not look for loops; kindepth() (used by kinship()) does
    idx <- function(i) kinship2_ids(p, i)
    result(p$id, idx(p$mindex), idx(p$findex), norm_sex(p$sex))
  },
  "kinship2-fixParents" = function(x) {
    f <- kinship2::fixParents(id = x$id, dadid = x$father, momid = x$mother, sex = sex_num(x$sex, 3L))
    # fixParents gives the parents it adds the code 0 even when its missid is ""
    # (character IDs), so pedigree() must be told 0 is missing.
    p <- kinship2::pedigree(id = f$id, dadid = f$dadid, momid = f$momid, sex = f$sex, missid = "0")
    kinship2::kindepth(p)
    idx <- function(i) kinship2_ids(p, i)
    result(p$id, idx(p$mindex), idx(p$findex), norm_sex(p$sex))
  },
  "purgeR-ped_rename" = function(x) {
    p <- purgeR::ped_rename(
      data.frame(id = x$id, dam = x$mother, sire = x$father, sex = x$sex, stringsAsFactors = FALSE),
      keep_names = TRUE
    )
    purgeR_back(p)
  },
  "purgeR-ped_sort" = function(x) {
    p <- purgeR::ped_sort(
      data.frame(id = x$id, dam = x$mother, sire = x$father, sex = x$sex, stringsAsFactors = FALSE),
      keep_names = TRUE
    )
    purgeR_back(p)
  },
  "pedtools-ped" = function(x) {
    p <- pedtools::ped(
      id = x$id, fid = ifelse(is.na(x$father), "0", x$father), mid = ifelse(is.na(x$mother), "0", x$mother),
      sex = sex_num(x$sex, 0L)
    )
    pedtools_back(p)
  },
  "pedtools-as.ped-addMissingFounders" = function(x) {
    p <- pedtools::as.ped(
      data.frame(id = x$id, fid = x$father, mid = x$mother, sex = sex_num(x$sex, 0L), stringsAsFactors = FALSE),
      addMissingFounders = TRUE
    )
    pedtools_back(p)
  },
  "pedigreemm-editPed" = function(x) {
    e <- pedigreemm::editPed(sire = x$father, dam = x$mother, label = x$id)
    pedigreemm::pedigree(sire = e$sire, dam = e$dam, label = e$label) # its validity check
    result(e$label, e$dam, e$sire, rep("-", nrow(e)))
  },
  "nprcgenekeepr-qcStudbook" = function(x) nprc(x, birth = TRUE),
  # Without birth dates, so the parent-age check cannot stop a cycle fixture
  # (a cycle always has a parent born after its child) before the cycle check.
  "nprcgenekeepr-qcStudbook-nobirth" = function(x) nprc(x, birth = FALSE)
)

nprc <- function(x, birth) {
  sb <- data.frame(
    id = x$id, sire = x$father, dam = x$mother,
    sex = factor(ifelse(is.na(x$sex), "U", x$sex), levels = c("M", "F", "U")),
    birth = as.Date(if (birth) ifelse(is.na(x$birth_year), NA, paste0(x$birth_year, "-01-01")) else NA),
    stringsAsFactors = FALSE
  )
  p <- nprcgenekeepr::qcStudbook(sb)
  result(p$id, p$dam, p$sire, norm_sex(p$sex))
}

kinship2_ids <- function(p, i) {
  out <- rep(NA_character_, length(i)) # index 0 is a missing parent
  out[i > 0] <- as.character(p$id[i[i > 0]])
  out
}

purgeR_back <- function(p) {
  # IDs are renumbered 1..N; keep_names = TRUE keeps the input ID in `names`.
  back <- function(v) ifelse(v == 0, NA_character_, as.character(p$names)[match(v, p$id)])
  result(p$names, back(p$dam), back(p$sire), norm_sex(p$sex))
}

pedtools_back <- function(p) {
  peds <- if (pedtools::is.pedList(p)) p else list(p)
  d <- do.call(rbind, lapply(peds, function(q) as.data.frame(q)))
  result(d$id, norm_parent(d$mid, "0"), norm_parent(d$fid, "0"), norm_sex(d$sex))
}

# tempdir() differs per session (nprcgenekeepr names a file in it); write it as <tempdir> so reruns match.
flatten <- function(v) {
  v <- gsub(tempdir(), "<tempdir>", trimws(v[nzchar(trimws(v))]), fixed = TRUE)
  paste(unique(gsub("[\t\n]+", " ", v)), collapse = " | ")
}

run_one <- function(fun, x) {
  warns <- character()
  msgs <- character()
  err <- NA_character_
  out <- NULL
  # Direct writes to stderr (e.g. a package's try() printing a caught error).
  stderr_lines <- character()
  errcon <- textConnection("stderr_lines", "w", local = TRUE)
  sink(errcon, type = "message")
  printed <- utils::capture.output(
    out <- withCallingHandlers(
      tryCatch(
        {
          setTimeLimit(elapsed = 60, transient = TRUE)
          on.exit(setTimeLimit(elapsed = Inf), add = TRUE)
          fun(x)
        },
        error = function(e) {
          err <<- conditionMessage(e)
          NULL
        }
      ),
      warning = function(w) {
        warns <<- c(warns, conditionMessage(w))
        invokeRestart("muffleWarning")
      },
      message = function(m) {
        msgs <<- c(msgs, conditionMessage(m))
        invokeRestart("muffleMessage")
      }
    ),
    type = "output"
  )
  sink(type = "message")
  close(errcon)
  list(
    out = out, err = err, warns = flatten(warns), msgs = flatten(msgs),
    printed = flatten(c(printed, stderr_lines))
  )
}

options(expressions = 5000)
fixture_paths <- sort(list.files(fixtures_dir, pattern = "\\.tsv$", full.names = TRUE))
records <- list()
for (prog in names(programs)) {
  dest <- file.path(results_dir, prog)
  unlink(dest, recursive = TRUE)
  dir.create(dest, recursive = TRUE, showWarnings = FALSE)
  for (path in fixture_paths) {
    name <- sub("\\.tsv$", "", basename(path))
    r <- run_one(programs[[prog]], read_fixture(path))
    if (!is.null(r$out)) {
      utils::write.table(r$out, file.path(dest, paste0(name, ".tsv")),
        sep = "\t", quote = FALSE, row.names = FALSE, na = "NA"
      )
    }
    records[[length(records) + 1]] <- data.frame(
      fixture = name, program = prog,
      outcome = if (is.null(r$out)) "error" else "ok",
      n_out = if (is.null(r$out)) NA_integer_ else nrow(r$out),
      error = if (is.na(r$err)) NA_character_ else flatten(r$err), warnings = r$warns, messages = r$msgs, printed = r$printed,
      stringsAsFactors = FALSE
    )
  }
}
rec <- do.call(rbind, records)
utils::write.table(rec, file.path(results_dir, "r.tsv"), sep = "\t", quote = FALSE, row.names = FALSE, na = "")
cat("wrote", nrow(rec), "R cleaner runs to", file.path(results_dir, "r.tsv"), "\n")
