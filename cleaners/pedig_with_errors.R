# Export optiSel::PedigWithErrors and optiSel::prePed's repair of it, both as
# id, mother, father, sex, birth_year, to .work/cleaners/PedigWithErrors/ (the
# data stay out of git). pedig_with_errors.py then runs pedsum on the export.
#
# Run: pixi run -e r cleaners-pwe-r

suppressPackageStartupMessages(library(optiSel))

args <- commandArgs(trailingOnly = FALSE)
here <- dirname(normalizePath(sub("^--file=", "", args[grep("^--file=", args)])))
out <- file.path(dirname(here), ".work", "cleaners", "PedigWithErrors")
dir.create(out, recursive = TRUE, showWarnings = FALSE)

write <- function(id, mother, father, sex, born, name) {
  sex <- ifelse(is.na(sex), NA, ifelse(sex == "male", "M", ifelse(sex == "female", "F", NA)))
  d <- data.frame(id = id, mother = mother, father = father, sex = sex, birth_year = born)
  utils::write.table(d, file.path(out, name), sep = "\t", quote = FALSE, row.names = FALSE, na = "NA")
}

data(PedigWithErrors)
d <- PedigWithErrors
write(d$Indiv, d$Dam, d$Sire, d$Sex, d$Born, "input.tsv")

printed <- utils::capture.output(p <- prePed(d), type = "output")
writeLines(printed, file.path(out, "prePed.messages.txt"))
write(p$Indiv, p$Dam, p$Sire, p$Sex, p$Born, "prePed.tsv")
cat("optiSel", as.character(packageVersion("optiSel")), "prePed:", nrow(d), "rows in,", nrow(p), "rows out\n")
cat(printed, sep = "\n")
