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
            for r in csv.DictReader(fh, delimiter="\t")
        ]


def read_tsv(path: Path) -> list[dict[str, str]]:
    """Rows of a TSV as dicts, or none when the file is absent."""
    if not path.exists():
        return []
    with path.open() as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def run(fixture: Path, mode: str) -> dict[str, str]:
    """Run validate on one fixture in one mode and record the outcome."""
    out = WORK / mode / fixture.stem
    shutil.rmtree(out, ignore_errors=True)
    cmd = ["pedsum", "validate", "--in", str(fixture), "--out", str(out), "--birth-year-col", "birth_year", "-q"]
    proc = subprocess.run([*cmd, *MODES[mode]], capture_output=True, text=True, check=False)
    blocked = [ln.strip()[2:] for ln in proc.stderr.splitlines() if ln.startswith("  - ")]
    fails = sorted({r["check"] for r in read_tsv(out / "validate.log")})
    dropped = sorted({r["id"] for r in read_tsv(out / "validate.dropped.tsv")}, key=lambda v: (len(v), v))
    rows = []
    if (out / "validate.tsv.gz").exists() and proc.returncode != 2:
        rows = normalize(out / "validate.tsv.gz")
        dest = RESULTS / f"pedsum-{mode}" / f"{fixture.stem}.tsv"
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["id", "mother", "father", "sex"], delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    return {
        "fixture": fixture.stem,
        "program": f"pedsum-{mode}",
        "exit": str(proc.returncode),
        "outcome": OUTCOME.get(proc.returncode, f"exit {proc.returncode}"),
        "n_out": str(len(rows)) if rows else "",
        "failed_checks": ",".join(fails),
        "blocked": " | ".join(blocked),
        "dropped": ",".join(dropped),
        "warnings": " | ".join(ln.split(": ", 1)[1] for ln in proc.stderr.splitlines() if " WARNING " in ln),
    }


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
