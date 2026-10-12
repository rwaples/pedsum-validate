"""Run ``pedsum validate`` on every fixture under each mode, and record what it did.

For each fixture and mode this writes the cleaned pedigree, normalized to
``id, mother, father, sex`` (sex M/F/U, missing NA), to
``cleaners/results/pedsum-<mode>/<fixture>.tsv`` when validate wrote one, and
one row to ``cleaners/results/pedsum.tsv``: exit code, outcome, the Checks that
FAILed, the BLOCKED lines, and the IDs ``--drop-offending`` removed.

Run: pixi run cleaners-pedsum
"""

from __future__ import annotations

import csv
import gzip
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
FIXTURES = HERE / "fixtures"
RESULTS = HERE / "results"
WORK = HERE.parent / ".work" / "cleaners"

MODES: dict[str, list[str]] = {
    "plain": [],
    "drop": ["--drop-offending"],
    "allow-missing-sex": ["--allow-missing-sex"],
    "no-sex-check": ["--no-sex-check"],
    # The options pedsum ADR 0006 added after the R cleaners' behaviour.
    "missing-parent-token-0": ["--missing-parent-token", "0"],
    "break-cycles": ["--break-cycles"],
}
OUTCOME = {0: "ok", 1: "fixed", 2: "blocked"}
SEX = {"1": "M", "2": "F", "0": "U", "-1": "U", "": "U"}


def missing(v: str) -> str:
    """NA for pedsum's missing-parent codes."""
    return "NA" if v in ("", "-1") else v


def normalize(path: Path) -> list[dict[str, str]]:
    """validate.tsv.gz as id, mother, father, sex (M/F/U)."""
    with gzip.open(path, "rt") as fh:
        return [
            {"id": r["id"], "mother": missing(r["mother"]), "father": missing(r["father"]), "sex": SEX[r["sex"]]}
            for r in csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE)
        ]


def read_tsv(path: Path) -> list[dict[str, str]]:
    """Rows of a TSV as dicts, or none when the file is absent."""
    if not path.exists():
        return []
    with path.open() as fh:
        return list(csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE))


def validate(inp: Path, out: Path, flags: list[str]) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Run ``pedsum validate`` into an emptied ``out``; its record, and the normalized pedigree it wrote.

    The outcome is ``error`` for an exit code validate does not use, and for exit
    1 without ``validate.tsv.gz``: an uncaught exception also exits 1.
    """
    shutil.rmtree(out, ignore_errors=True)
    cmd = ["pedsum", "validate", "--in", str(inp), "--out", str(out), "--birth-year-col", "birth_year", "-q"]
    proc = subprocess.run([*cmd, *flags], capture_output=True, text=True, check=False)
    wrote = proc.returncode in (0, 1) and (out / "validate.tsv.gz").exists()
    outcome = OUTCOME[proc.returncode] if wrote or proc.returncode == 2 else "error"
    rows = normalize(out / "validate.tsv.gz") if wrote else []
    blocked = [ln.strip()[2:] for ln in proc.stderr.splitlines() if ln.startswith("  - ")]
    record = {
        "exit": str(proc.returncode),
        "outcome": outcome,
        "n_out": str(len(rows)) if wrote else "",
        "failed_checks": ",".join(sorted({r["check"] for r in read_tsv(out / "validate.log")})),
        "blocked": " | ".join(blocked),
        "dropped": ",".join(
            sorted({r["id"] for r in read_tsv(out / "validate.dropped.tsv")}, key=lambda v: (len(v), v))
        ),
        "warnings": " | ".join(ln.split(": ", 1)[1] for ln in proc.stderr.splitlines() if " WARNING " in ln),
    }
    if outcome == "error":
        tail = " ".join(proc.stderr.split())[-300:]  # one line: the record is a TSV row
        record["warnings"] = " | ".join(filter(None, [record["warnings"], tail]))
    return record, rows


def run(fixture: Path, mode: str) -> dict[str, str]:
    """Run validate on one fixture in one mode, keep its pedigree, and return its record."""
    record, rows = validate(fixture, WORK / mode / fixture.stem, MODES[mode])
    if record["n_out"]:
        dest = RESULTS / f"pedsum-{mode}" / f"{fixture.stem}.tsv"
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["id", "mother", "father", "sex"], delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    return {"fixture": fixture.stem, "program": f"pedsum-{mode}", **record}


def main() -> int:
    """Run every fixture in every mode and write results/pedsum.tsv."""
    for mode in MODES:
        shutil.rmtree(RESULTS / f"pedsum-{mode}", ignore_errors=True)
    records = [run(f, mode) for mode in MODES for f in sorted(FIXTURES.glob("*.tsv"))]
    RESULTS.mkdir(exist_ok=True)
    with (RESULTS / "pedsum.tsv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(records[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(records)
    print(f"wrote {len(records)} pedsum runs to {RESULTS / 'pedsum.tsv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
