"""Tabulate what each program did to each fixture: cleaners/results/comparison.md.

Reads the run records (results/r.tsv, results/pedsum.tsv) and each program's
normalized output, diffs the output against the fixture, and writes one cell
per fixture and program:

- ``E``: refused or crashed (an R error; pedsum BLOCKED, or a crash).
- ``W``: returned a pedigree with a warning (pedsum: a finding in validate.log, or a WARNING).
- ``M``: returned a pedigree and printed a message.
- ``S``: returned a changed pedigree and said nothing.
- ``ok``: returned the pedigree unchanged and said nothing.

followed by the changes: ``+id`` rows added, ``-id`` rows removed, duplicate rows removed or kept,
``id:m/f`` parent links changed (to mother/father), ``id:sex`` sex changed, and
``CYCLE`` when the output still contains a cycle. Parents written ``0`` in the
fixture count as missing for the diff, so ``zero_missing`` shows a link change
only where a program kept ``0`` as an ID or added a row for it.

Run: pixi run cleaners-compare (after cleaners-r and cleaners-pedsum)
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
FIXTURES = HERE / "fixtures"
RESULTS = HERE / "results"

Ped = dict[str, tuple[str, str, str]]  # id -> (mother, father, sex)


def read_rows(path: Path) -> list[dict[str, str]]:
    """Rows of a TSV as dicts."""
    with path.open() as fh:
        return list(csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE))


def load_ped(path: Path, *, zero_is_missing: bool = False) -> tuple[Ped, list[str]]:
    """The pedigree keyed by id, and every id in row order (duplicates kept).

    Sex is M, F, ``-`` (a program with no sex) or U for anything else.
    """
    ped: Ped = {}
    order = []
    for r in read_rows(path):
        sex = r["sex"] if r["sex"] in ("M", "F", "-") else "U"
        mother, father = r["mother"], r["father"]
        if zero_is_missing:
            mother, father = ("NA" if v == "0" else v for v in (mother, father))
        ped.setdefault(r["id"], (mother, father, sex))
        order.append(r["id"])
    return ped, order


def has_cycle(ped: Ped) -> bool:
    """Whether any individual is its own ancestor."""
    state: dict[str, int] = {}

    def visit(i: str) -> bool:
        state[i] = 1
        for p in ped[i][:2]:
            if p != "NA" and p in ped and (state.get(p) == 1 or (p not in state and visit(p))):
                return True
        state[i] = 2
        return False

    return any(i not in state and visit(i) for i in ped)


def changes(inp: Ped, inp_order: list[str], out: Ped, out_order: list[str]) -> list[str]:
    """What the program changed: rows added and removed, duplicates, parent links, sexes, cycles left."""
    parts = [f"+{i}" for i in out if i not in inp]
    parts += [f"-{i}" for i in inp if i not in out]
    # Copies removed of an ID that survives; an ID removed entirely already shows as -id.
    n_in, n_out = Counter(inp_order), Counter(out_order)
    dup_removed = sum(n_in[i] - n_out[i] for i in n_in if n_in[i] > 1 and n_out[i] >= 1)
    if dup_removed:
        parts.append(f"{dup_removed} dup row(s) removed")
    dup_out = len(out_order) - len(n_out)
    if dup_out:
        parts.append(f"{dup_out} dup row(s) kept")
    for i in inp:
        if i not in out:
            continue
        (m0, f0, s0), (m1, f1, s1) = inp[i], out[i]
        if (m0, f0) != (m1, f1):
            parts.append(f"{i}:{m1}/{f1}")
        if s1 != "-" and s0 != s1:
            parts.append(f"{i}:{s0}>{s1}")
    if "NA" in out:
        parts.append("id NA kept")
    if has_cycle(out):
        parts.append("CYCLE")
    return parts


def signal(rec: dict[str, str], changed: bool) -> str:
    """How the program reported its run: E, W, M, S or ok."""
    if rec["outcome"] in ("error", "blocked"):
        return "E"
    if rec["program"].startswith("pedsum"):
        return "W" if rec["failed_checks"] or rec["warnings"] else "S" if changed else "ok"
    if rec["warnings"]:
        return "W"
    if rec["messages"] or rec["printed"]:
        return "M"
    return "S" if changed else "ok"


def main() -> None:
    """Write results/comparison.md."""
    records = read_rows(RESULTS / "r.tsv") + read_rows(RESULTS / "pedsum.tsv")
    fixtures = read_rows(HERE / "fixtures.tsv")
    programs = list(dict.fromkeys(r["program"] for r in records))
    cells: dict[tuple[str, str], str] = {}
    details: list[str] = []
    for rec in records:
        name, prog = rec["fixture"], rec["program"]
        inp, inp_order = load_ped(FIXTURES / f"{name}.tsv", zero_is_missing=True)
        out_path = RESULTS / prog / f"{name}.tsv"
        diff: list[str] = []
        if out_path.exists() and rec["outcome"] not in ("error", "blocked"):
            out, order = load_ped(out_path)
            diff = changes(inp, inp_order, out, order)
        sig = signal(rec, bool(diff))
        cells[name, prog] = " ".join([sig, *diff])
        said = {
            k: rec.get(k, "")
            for k in ("error", "warnings", "messages", "printed", "blocked", "failed_checks", "dropped")
            if rec.get(k)
        }
        output = "; ".join(f"{k}: {v}" for k, v in said.items()).replace("|", "\\|")  # a | would split the cell
        details.append(f"| {name} | {prog} | {cells[name, prog]} | {output} |")

    lines = [
        "# Pedigree cleaners compared on the fixtures",
        "",
        "Generated by `cleaners/compare.py`; see its docstring for the cell legend. Fixtures: `cleaners/fixtures.tsv`.",
        "",
        "| fixture | " + " | ".join(programs) + " |",
        "|---|" + "---|" * len(programs),
    ]
    lines += [
        f"| {f['name']} | " + " | ".join(cells.get((f["name"], p), "") for p in programs) + " |" for f in fixtures
    ]
    lines += ["", "## What each program said", "", "| fixture | program | cell | output |", "|---|---|---|---|"]
    order = {f["name"]: k for k, f in enumerate(fixtures)}
    lines += sorted(details, key=lambda ln: order[ln.split(" | ")[0][2:]])
    (RESULTS / "comparison.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {RESULTS / 'comparison.md'} ({len(fixtures)} fixtures x {len(programs)} programs)")


if __name__ == "__main__":
    main()
