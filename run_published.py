"""Check pedsum against statistics published for public pedigrees.

Downloads each pedigree in ``cases.yaml`` from its pinned URL, verifies its
SHA-256, converts it to pedsum's input format, runs ``pedsum validate``,
``pedsum summarize`` and ``pedsum effective-size`` (every estimator that can
run), and compares the output with the published values.
Statistics the pedsum CLI does not expose yet are computed with the
``pedigree_graph`` API that pedsum depends on and labelled ``engine``;
statistics neither reports are listed as ``GAP``. Where the authors deposited
per-individual values (F, generation), pedsum's are compared with them id by id.

Usage (from the repo root)::

    pixi run harness
    pixi run harness --only atlas,genea140

Needs network access to raw.githubusercontent.com, figshare.com,
sourceforge.net, kinsources.net and datadryad.org (with a Dryad API token; see
``dryad.py``), plus the ``rdata`` package to read R ``.rda``/``.RData`` files
and ``openpyxl`` to read ``.xlsx`` files (``pip install rdata openpyxl``).
Writes ``results.md``, ``results.tsv`` and ``pedsum_all.tsv`` (pedsum's
headline statistics and every Ne estimate per dataset) to ``--out`` and exits 1 if any
check FAILs or ERRORs.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import math
import subprocess
import sys
import tarfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import scipy.linalg
import yaml
from pedigree_graph.effective_size import ALL_EFFECTIVE_SIZE_ESTIMATORS as ALL_ESTIMATORS

import dryad  # dryad.py, next to this script

HERE = Path(__file__).resolve().parent
# The estimators effective-size refuses on unknown sex (pedsum/cli.py _SEX_DEPENDENT_ESTIMATORS).
LTC_FILLED = "ne_long_term_contributions_phantom_parents"
SEX_ESTIMATORS = frozenset({"ne_sex_ratio", "ne_variance_family_size", "ne_hill_overlapping"})
# The pedsum CLI of the installed pedsum package (see pixi.toml).
PEDSUM = [sys.executable, "-c", "import sys; from pedsum.cli import main; sys.exit(main())"]


@dataclass
class Result:
    """One evaluated check."""

    dataset: str
    stat: str
    published: float
    observed: float | None
    status: str
    via: str
    gap: str
    source: str
    note: str


# ---------------------------------------------------------------------------
# Fetch and convert
# ---------------------------------------------------------------------------


def fetch(spec: dict[str, Any], cache: Path) -> Path:
    """Download the dataset's ``url`` or ``dryad_file`` into ``cache`` once and verify its SHA-256."""
    sha256 = spec["sha256"]
    if "dryad_file" in spec:
        source, name = f"Dryad file {spec['dryad_file']}", f"dryad-{spec['dryad_file']}"
    else:
        source, name = spec["url"], spec["url"].rsplit("/", 1)[-1]
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / f"{sha256[:12]}-{name}"
    if not path.exists():
        if "dryad_file" in spec:
            data = dryad.download(spec["dryad_file"])
        else:
            with urllib.request.urlopen(spec["url"], timeout=60) as resp:
                data = resp.read()
        path.write_bytes(data)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != sha256:
        path.unlink()
        raise RuntimeError(f"{source}: SHA-256 {digest} does not match the pinned {sha256}")
    return path


def _read_bytes(path: Path, spec: dict[str, Any]) -> bytes:
    """Bytes of the source file: ``member`` of a tar or zip archive if given, gunzipped if gzipped."""
    if "member" in spec and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            data = zf.read(spec["member"])
    elif "member" in spec:
        with tarfile.open(path) as tar:
            fh = tar.extractfile(spec["member"])
            if fh is None:
                raise ValueError(f"{path}: {spec['member']!r} is not a regular file")
            data = fh.read()
    else:
        data = path.read_bytes()
    if data[:2] == b"\x1f\x8b":
        data = gzip.decompress(data)
    return data


def _read_text(path: Path, spec: dict[str, Any]) -> str:
    return _read_bytes(path, spec).decode()


def load_table(path: Path, spec: dict[str, Any]) -> dict[str, list[str | None]]:
    """Read the source table into string columns (None for R NA)."""
    fmt = spec.get("format")
    if fmt in ("whitespace_table", "csv", "tsv"):
        # `names` gives the columns of a file without a header row; `#` lines are comments.
        lines = [ln for ln in _read_text(path, spec).splitlines() if ln.strip() and not ln.startswith("#")]
        if fmt == "whitespace_table":
            rows = [ln.split() for ln in lines]
        else:  # csv, or tsv: tab-separated, keeping the empty fields that whitespace_table collapses
            rows = list(csv.reader(lines, delimiter="\t" if fmt == "tsv" else ","))
        header, body = (spec["names"], rows) if "names" in spec else (rows[0], rows[1:])
        cols = {name: [r[i] for r in body] for i, name in enumerate(header)}
        return {k: [None if v == "NA" else v for v in vals] for k, vals in cols.items()}
    if fmt == "iur_txt":
        return _load_iur(_read_text(path, spec))
    if fmt == "xlsx":
        return _load_xlsx(path, spec)
    if fmt == "ainv_list":
        return _pedigree_from_ainv(_ainv_triplets(path, spec))
    import rdata  # optional dependency; only the .rda inputs need it

    frame = rdata.read_rda(path)[spec["object"]]
    out: dict[str, list[str | None]] = {}
    for name in frame.columns:
        values = frame[name].astype(object).tolist()
        out[str(name)] = [None if _is_na(v) else _as_token(v) for v in values]
    return out


def _load_xlsx(path: Path, spec: dict[str, Any]) -> dict[str, list[str | None]]:
    """One worksheet of an Excel workbook: ``sheet`` by name, else the first. Blank rows are skipped.

    A repeated header (such as the two allele columns of a marker) keeps its first column.
    """
    import openpyxl  # optional dependency; only the .xlsx inputs need it

    # Read from memory: openpyxl checks the file extension, which cached files lack.
    book = openpyxl.load_workbook(io.BytesIO(_read_bytes(path, spec)), read_only=True, data_only=True)
    sheet = book[spec["sheet"]] if "sheet" in spec else book.worksheets[0]
    rows = [r for r in sheet.iter_rows(values_only=True) if any(v is not None for v in r)]
    cols: dict[str, list[str | None]] = {}
    for i, name in enumerate(str(h) for h in rows[0]):
        if name not in cols:
            cols[name] = [None if i >= len(r) or r[i] is None or r[i] == "NA" else _as_token(r[i]) for r in rows[1:]]
    return cols


def _ainv_triplets(path: Path, spec: dict[str, Any]) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray]:
    """Lower-triangle triplets (0-based row, column, value) of an inverse relationship matrix, and the row ids.

    ``format: ainv_rdata`` reads ASReml-R ``asreml.Ainverse`` output saved as
    ``.RData`` (``object`` names the data frame; row ids are in its
    ``rowNames`` attribute). ``ainv_list`` reads a whitespace text list
    ``row column value`` after a header line; its rows are numbered 1..n and
    those numbers are the ids.
    """
    if spec.get("format") == "ainv_rdata":
        import rdata  # optional dependency

        parsed = rdata.parser.parse_file(path)
        frame = rdata.conversion.convert(parsed)[spec["object"]]
        node, names = parsed.object.value[0].attributes, None
        while node is not None and node.info.type.name == "LIST":
            if node.tag.value.value == b"rowNames":
                names = [x.value.decode() for x in node.value[0].value]
            node = node.value[1] if len(node.value) > 1 else None
        if names is None:
            raise ValueError(f"{path}: no rowNames attribute")
        r, c, v = (frame[k].to_numpy() for k in frame.columns[:3])
    else:
        lines = [ln.split() for ln in _read_text(path, spec).splitlines()[1:] if ln.strip()]
        r, c, v = (np.array([float(x[i]) for x in lines]) for i in range(3))
        names = [str(i) for i in range(1, int(r.max()) + 1)]
    return names, r.astype(np.int64) - 1, c.astype(np.int64) - 1, v.astype(np.float64)


def _f_from_ainv(triplets: tuple[list[str], np.ndarray, np.ndarray, np.ndarray]) -> dict[str, float]:
    """F = diag(A) - 1, with A the inverse of the given inverse relationship matrix.

    With A^-1 = L L^T (Cholesky), A = L^-T L^-1, so diag(A) is the column sums
    of squares of L^-1. On the 6,740-row Soay matrix this takes 4.5 s against
    8.7 s for a dense inverse, and agrees with it to 4e-14.
    """
    names, r, c, v = triplets
    n = len(names)
    ainv = np.zeros((n, n), order="F")
    ainv[r, c] = v
    ainv[c, r] = v
    low = scipy.linalg.cholesky(ainv, lower=True, overwrite_a=True)
    linv = scipy.linalg.solve_triangular(low, np.eye(n, order="F"), lower=True, overwrite_b=True)
    f = np.einsum("ij,ij->j", linv, linv) - 1.0
    return dict(zip(names, f.tolist(), strict=True))


def _pedigree_from_ainv(triplets: tuple[list[str], np.ndarray, np.ndarray, np.ndarray]) -> dict[str, list[str | None]]:
    """Recover the parents behind a Henderson inverse relationship matrix by peeling rows from the last.

    A^-1 = sum_i b_i c_i c_i^T, with c_i = e_i - (e_dam + e_sire)/2 over i's
    known parents. When every parent precedes its offspring, the off-diagonal
    entries left in row i after peeling the rows below it are i's parents,
    each equal to -b_i/2. The matrix is refused if that does not hold or
    anything is left over.

    A^-1 does not say which parent is the dam, so parents are split by
    2-colouring the mate graph. F does not depend on which parent is called
    the dam: the tabular method treats the two parents symmetrically.
    Returns columns ``id, mother, father``; sex is left to ``validate``,
    which infers it from the parents' roles.
    """
    names, r, c, v = triplets
    n = len(names)
    m: list[dict[int, float]] = [{} for _ in range(n)]
    for i, j, x in zip(r.tolist(), c.tolist(), v.tolist(), strict=True):
        m[i][j] = m[i].get(j, 0.0) + x
        if i != j:
            m[j][i] = m[j].get(i, 0.0) + x
    parents: list[list[int]] = [[] for _ in range(n)]
    for i in range(n - 1, -1, -1):
        b = m[i].get(i, 0.0)
        par = sorted(j for j, x in m[i].items() if j != i and abs(x) > 1e-8)
        if any(j > i for j in par) or len(par) > 2 or any(abs(m[i][j] + b / 2) > 1e-7 for j in par):
            raise ValueError(f"A-inverse row {names[i]!r} is not a parent-before-offspring Henderson row")
        parents[i] = par
        coef = {i: 1.0, **dict.fromkeys(par, -0.5)}
        for x, cx in coef.items():
            for y, cy in coef.items():
                m[x][y] = m[x].get(y, 0.0) - b * cx * cy
    if max((abs(x) for row in m for x in row.values()), default=0.0) > 1e-8:
        raise ValueError("A-inverse is not fully explained by the recovered parents")
    mates: dict[int, set[int]] = {}
    for par in parents:
        if len(par) == 2:
            mates.setdefault(par[0], set()).add(par[1])
            mates.setdefault(par[1], set()).add(par[0])
    colour: dict[int, int] = {}
    for start in mates:
        if start in colour:
            continue
        colour[start], stack = 0, [start]
        while stack:
            x = stack.pop()
            for y in mates[x]:
                if y not in colour:
                    colour[y] = 1 - colour[x]
                    stack.append(y)
                elif colour[y] == colour[x]:
                    raise ValueError(f"{names[x]} and {names[y]} are mates but must share a sex")
    mother: list[str | None] = []
    father: list[str | None] = []
    for par in parents:
        if len(par) == 2:
            d, s = par if colour[par[0]] == 0 else par[::-1]
        elif len(par) == 1:
            d, s = (par[0], None) if colour.get(par[0], 0) == 0 else (None, par[0])
        else:
            d = s = None
        mother.append(None if d is None else names[d])
        father.append(None if s is None else names[s])
    return {"id": list(names), "mother": mother, "father": father}


def load_reference(
    ref: dict[str, Any], table: dict[str, list[str | None]], id_column: str, cache: Path
) -> dict[str, float]:
    """One entry of a dataset's ``reference_values``: the authors' value for each original id.

    ``{column: NAME}`` reads a column of the dataset's own source table.
    Otherwise ``ref`` pins a file of its own (``url`` or ``dryad_file``, and
    ``sha256``): any table format, read as ``value_column`` keyed by
    ``id_column``; ``ainv_rdata`` or ``ainv_list``, F = diag(A) - 1 from an
    inverse relationship matrix; or ``square_matrix_diagonal``, the diagonal of
    a square matrix whose first line holds the ids. ``subtract`` is taken off
    every value (``subtract: 1`` turns an A diagonal into F). Values that are
    not numbers (NA, blank, ``x``) are skipped.
    """
    if "url" not in ref and "dryad_file" not in ref:
        keys, values = table[id_column], table[ref["column"]]
    else:
        path = fetch(ref, cache)
        fmt = ref.get("format")
        if fmt in ("ainv_rdata", "ainv_list"):
            return _f_from_ainv(_ainv_triplets(path, ref))
        if fmt == "square_matrix_diagonal":
            lines = _read_text(path, ref).splitlines()
            keys = lines[0].split()
            rows = [line.split() for line in lines[1 : len(keys) + 1]]
            if len(rows) != len(keys) or any(len(row) != len(keys) for row in rows):
                raise ValueError(f"{path}: not a square matrix of {len(keys)} ids")
            values = [row[k] for k, row in enumerate(rows)]
        else:
            other = load_table(path, ref)
            keys, values = other[ref["id_column"]], other[ref["value_column"]]
    shift = float(ref.get("subtract", 0))
    out: dict[str, float] = {}
    for key, raw in zip(keys, values, strict=True):
        if key is None:
            continue
        try:
            value = float(raw) - shift  # type: ignore[arg-type]
        except TypeError, ValueError:
            continue
        if key in out and out[key] != value:
            raise ValueError(f"reference id {key!r} has two values")
        out[key] = value
    return out


def _load_iur(text: str) -> dict[str, list[str | None]]:
    """Kinsources IUR text: an individuals table, then a unions table listing each union's children.

    Returns columns ``Id, Gender, FatherId, MotherId``; a parent id of ``0`` means unknown.
    """
    blocks = {b.split("\t", 2)[1]: b.splitlines()[1:] for b in text.split("\n\n") if b.startswith("Id\t")}
    individuals = [line.split("\t") for line in blocks["Name"]]
    parents: dict[str, tuple[str, str]] = {}
    for line in blocks["Status"]:
        _, _, father, mother, children, *_ = line.split("\t")
        for child in filter(None, children.split(";")):
            if child in parents:
                raise ValueError(f"IUR: individual {child} is a child of two unions")
            parents[child] = (father, mother)
    ids = [row[0] for row in individuals]
    return {
        "Id": ids,
        "Gender": [row[2] for row in individuals],
        "FatherId": [parents.get(i, (None, None))[0] for i in ids],
        "MotherId": [parents.get(i, (None, None))[1] for i in ids],
    }


def _is_na(value: object) -> bool:
    if value is None:
        return True
    try:
        return bool(value != value)  # NaN and pandas NA compare unequal to themselves
    except TypeError:
        return True  # pandas NA raises on bool()


def _as_token(value: object) -> str:
    """Render R integers stored as float (``12.0``) the way R prints them (``12``)."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def apply_parent_overrides(table: dict[str, list[str | None]], spec: dict[str, Any]) -> None:
    """Apply ``parent_overrides: {id: {mother: ..., father: ...}}`` in place; null means unknown.

    For documented errors in a source file that ``validate`` cannot repair,
    such as an individual listed as its own parent.
    """
    cols = spec["columns"]
    for orig, fix in spec.get("parent_overrides", {}).items():
        rows = [i for i, v in enumerate(table[cols["id"]]) if v == str(orig)]
        if len(rows) != 1:
            raise ValueError(f"parent_overrides: id {orig!r} matched {len(rows)} rows")
        for role in ("mother", "father"):
            if role in fix:
                table[cols[role]][rows[0]] = None if fix[role] is None else str(fix[role])


def convert(table: dict[str, list[str | None]], spec: dict[str, Any], out: Path) -> dict[str, int]:
    """Write pedsum's input TSV and return the original-id -> integer-id map.

    Ids are numbered in first-appearance order over the id column, then over
    parents that have no row of their own (``validate`` adds those as founders).
    Every token in ``missing_parent``, and R NA, means "no parent".
    """
    cols = spec["columns"]
    missing = set(spec.get("missing_parent", []))
    ids = table[cols["id"]]
    mothers = [None if v in missing else v for v in table[cols["mother"]]]
    fathers = [None if v in missing else v for v in table[cols["father"]]]

    id_map: dict[str, int] = {}
    for token in [*ids, *mothers, *fathers]:
        if token is not None and token not in id_map:
            id_map[token] = len(id_map) + 1

    sex_col = cols.get("sex")
    sex_map = {str(k): v for k, v in spec.get("sex_map", {}).items()}
    sexes = table[sex_col] if sex_col else [None] * len(ids)
    ref_col = spec.get("reference_column")
    refs = table[ref_col] if ref_col else [None] * len(ids)

    with out.open("w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["id", "sex", "mother", "father", "orig_id", "reference"])
        for i, token in enumerate(ids):
            if token is None:
                raise ValueError(f"row {i}: missing id")
            sex = sex_map.get(sexes[i], "") if sexes[i] is not None else ""
            ref = 1 if refs[i] in ("1", "1.0") else 0
            w.writerow(
                [
                    id_map[token],
                    sex,
                    -1 if mothers[i] is None else id_map[mothers[i]],
                    -1 if fathers[i] is None else id_map[fathers[i]],
                    token,
                    ref,
                ]
            )
    return id_map


# ---------------------------------------------------------------------------
# Run pedsum
# ---------------------------------------------------------------------------


def run_pedsum(args: list[str], log: Path) -> int:
    """Run one pedsum command, appending its output to ``log``."""
    proc = subprocess.run([*PEDSUM, *args], capture_output=True, text=True, check=False)
    with log.open("a") as fh:
        fh.write(f"$ pedsum {' '.join(args)}\n{proc.stdout}{proc.stderr}\n[exit {proc.returncode}]\n\n")
    return proc.returncode


# ---------------------------------------------------------------------------
# Observed values
# ---------------------------------------------------------------------------


class Observed:
    """Lazily computed observed values for one dataset."""

    def __init__(
        self,
        summary: dict[str, Any],
        annotated: pl.DataFrame,
        id_map: dict[str, int],
        effective: dict[str, Any] | None,
        reference: dict[str, dict[str, float]],
        ltc_filled: dict[str, Any] | None = None,
    ) -> None:
        """Hold one dataset's pedsum outputs, its id map and the authors' per-individual values.

        ``ltc_filled`` is the ``ne_long_term_contributions`` record on the
        pedigree with its half-founders filled by phantom parents; it feeds
        the overview only, never a check.
        """
        self.summary = summary
        self.annotated = annotated
        self.id_map = id_map
        self.effective = effective
        self.reference = reference
        self.ltc_filled = ltc_filled
        self._pg: Any = None

    def summary_value(self, path: str) -> float:
        """Scalar at a dotted path of summary.yaml."""
        node: Any = self.summary
        for key in path.split("."):
            node = node[key]
        return float(node)

    def _rows(self, check: dict[str, Any]) -> pl.DataFrame:
        """Rows of annotated.tsv.gz that a check aggregates over.

        ``min_grandparents: k`` keeps rows with both parents and at least k
        grandparents known; ``where: {column: value}`` keeps rows equal to the
        value on each column; ``subset: <name>`` keeps the rows whose original
        id has a value in ``reference_values[<name>]``.
        """
        frame = self.annotated
        k = check.get("min_grandparents")
        if k is not None:
            frame = frame.filter((pl.col("mother") >= 0) & (pl.col("father") >= 0) & (pl.col("n_grandparents") >= k))
        for column, value in (check.get("where") or {}).items():
            frame = frame.filter(pl.col(column) == value)
        if "subset" in check:
            ids = [self.id_map[i] for i in self.reference[check["subset"]]]
            frame = frame.filter(pl.col("id").is_in(ids))
        return frame

    def annotated_value(self, spec: str, check: dict[str, Any]) -> float:
        """``<sum|max|mean|frac_gt0|count|count_gt:<x>|of>:<column>`` of annotated.tsv.gz."""
        head, _, column = spec.rpartition(":")
        agg, _, arg = head.partition(":")
        frame = self._rows(check)
        values = frame[column]
        if agg == "sum":
            return float(values.sum())
        if agg == "max":
            return float(values.max())
        if agg == "mean":
            return float(values.mean())
        if agg == "frac_gt0":
            return float((values > 0).mean())
        if agg == "count":
            return float((values.cast(pl.Float64) != 0).sum())
        if agg == "count_gt":
            return float((values > float(arg)).sum())
        if agg == "of":
            return self._row_value(values.to_numpy(), frame["id"].to_numpy(), check.get("id"))
        raise ValueError(f"unknown annotated aggregate {agg!r}")

    def reference_value(self, spec: str, check: dict[str, Any]) -> float:
        """``<name>:<max_abs_diff|n_within|n_compared|sum_ref|sum_pedsum>:<column>``.

        Compares pedsum's ``column`` with ``reference_values[<name>]``, id by
        id, over the check's rows that have a reference value. ``n_within``
        counts those with |difference| <= ``match_tol`` (default 1e-6).
        """
        name, agg, column = spec.split(":")
        ref = self.reference[name]
        missing = [k for k in ref if k not in self.id_map]
        if missing:
            raise ValueError(f"{len(missing)} ids of reference {name!r} are not in the pedigree, e.g. {missing[0]!r}")
        frame = self._rows(check)
        ours = dict(zip(frame["id"].to_list(), frame[column].to_list(), strict=True))
        pairs = [(ours[i], v) for i, v in ((self.id_map[k], v) for k, v in ref.items()) if i in ours]
        if not pairs:
            raise ValueError(f"no rows to compare with reference {name!r}")
        ped, pub = np.array(pairs, dtype=np.float64).T
        diff = np.abs(ped - pub)
        if agg == "max_abs_diff":
            return float(diff.max())
        if agg == "n_within":
            return float((diff <= float(check.get("match_tol", 1e-6))).sum())
        if agg == "n_compared":
            return float(len(pairs))
        if agg == "sum_ref":
            return float(pub.sum())
        if agg == "sum_pedsum":
            return float(ped.sum())
        raise ValueError(f"unknown reference aggregate {agg!r}")

    def effective_value(self, path: str) -> float:
        """``<estimator>.<field>`` of effective_size.yaml."""
        if self.effective is None:
            raise ValueError("effective-size was not run for this dataset")
        estimator, _, field = path.partition(".")
        return float(self.effective["effective_size"][estimator][field])

    def _row_value(self, values: np.ndarray, row_ids: np.ndarray, orig_id: str | None) -> float:
        if orig_id is None:
            raise ValueError("this check needs an `id`")
        hits = np.flatnonzero(row_ids == self.id_map[orig_id])
        if hits.size != 1:
            raise ValueError(f"id {orig_id!r} matched {hits.size} rows")
        return float(values[hits[0]])

    def _graph(self) -> Any:
        if self._pg is None:
            from pedigree_graph import PedigreeGraph

            a = self.annotated
            self._pg = PedigreeGraph.from_arrays(
                ids=a["id"].to_numpy(),
                mother_ids=a["mother"].to_numpy(),
                father_ids=a["father"].to_numpy(),
            )
        return self._pg

    def engine_value(self, name: str) -> float:
        """Statistic computed with the pedigree_graph API (not exposed by the pedsum CLI)."""
        from pedigree_graph.effective_size import ne_individual_delta_f

        pg = self._graph()
        if name == "ne_idf_t1_all":
            ref = np.arange(len(self.annotated))
            return float(ne_individual_delta_f(pg, reference=ref).ne_unrelated_founders)
        raise ValueError(f"unknown engine statistic {name!r}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def evaluate(check: dict[str, Any], obs: Observed | None, error: str | None) -> Result:
    """Compare one published value with pedsum's."""
    via = check["via"]
    published = float(check["published"])
    base = dict(
        dataset=check["dataset"],
        stat=check["stat"],
        published=published,
        via=via,
        gap=check.get("gap", ""),
        source=str(check.get("source", "")),
        note=check.get("note", ""),
    )
    if via == "gap":
        return Result(observed=None, status="GAP", **base)
    if obs is None:
        return Result(observed=None, status="ERROR", **{**base, "note": error or ""})
    kind, _, arg = via.partition(":")
    try:
        if kind == "summary":
            observed = obs.summary_value(arg)
        elif kind == "annotated":
            observed = obs.annotated_value(arg, check)
        elif kind == "reference":
            observed = obs.reference_value(arg, check)
        elif kind == "effective":
            observed = obs.effective_value(arg)
        elif kind == "engine":
            observed = obs.engine_value(arg)
        else:
            raise ValueError(f"unknown via {via!r}")
    except Exception as exc:  # report and keep going
        return Result(observed=None, status="ERROR", **{**base, "note": f"{type(exc).__name__}: {exc}"})
    observed = observed * check.get("scale", 1) + check.get("offset", 0)
    tol = float(check.get("tol", 0))
    if math.isclose(observed, published, rel_tol=0, abs_tol=tol + 1e-12):
        status = "PASS"
    elif check.get("status_if_differs") == "expected_difference":
        status = "DIFF"
    else:
        status = "FAIL"
    if kind == "engine" and status == "PASS":
        status = "PASS (engine)"
    return Result(observed=observed, status=status, **base)


def run_dataset(name: str, spec: dict[str, Any], cache: Path, work: Path) -> tuple[Observed | None, str | None]:
    """Fetch, convert and summarize one dataset; return its observed values or an error."""
    ds = work / name
    ds.mkdir(parents=True, exist_ok=True)
    log = ds / "pedsum.log"
    log.write_text("")
    table = load_table(fetch(spec, cache), spec)
    apply_parent_overrides(table, spec)
    id_map = convert(table, spec, ds / "input.tsv")
    reference = {
        name: load_reference(ref, table, spec["columns"]["id"], cache)
        for name, ref in spec.get("reference_values", {}).items()
    }

    extra = ["--allow-missing-sex"] if spec.get("allow_missing_sex") else []
    run_pedsum(["validate", "--in", str(ds / "input.tsv"), "--out", str(ds / "validate"), *extra], log)
    fixed = ds / "validate" / "validate.tsv.gz"
    if not fixed.exists():
        return None, f"validate produced no fixed pedigree; see {log}"
    code = run_pedsum(["summarize", "--in", str(fixed), "--out", str(ds / "summary"), *extra], log)
    if code != 0:
        return None, f"summarize exited {code}; see {log}"
    summary = yaml.safe_load((ds / "summary" / "summary.yaml").read_text())
    annotated = pl.read_csv(ds / "summary" / "annotated.tsv.gz", separator="\t", infer_schema_length=None)

    # Every estimator that can run. The sex-based ones refuse unknown sex, so they are left out
    # (and show as not_requested) when any row's sex is unknown. Only Ne_iΔF uses --reference-col.
    # validate writes unknown sex as -1; read the column as text, since the other tokens' encoding varies (rwaples/pedsum#11).
    sex = pl.read_csv(fixed, separator="\t", columns=["sex"], schema_overrides={"sex": pl.String})["sex"]
    unknown_sex = bool((sex == "-1").any())
    estimators = [e for e in ALL_ESTIMATORS if not (unknown_sex and e in SEX_ESTIMATORS)]
    es_args = ["--estimators", ",".join(estimators)]
    if spec.get("reference_column"):
        es_args += ["--reference-col", "reference"]
    code = run_pedsum(["effective-size", "--in", str(fixed), "--out", str(ds / "effective"), *es_args, *extra], log)
    if code != 0:
        return None, f"effective-size exited {code}; see {log}"
    effective = yaml.safe_load((ds / "effective" / "effective_size.yaml").read_text())
    ltc_filled = _ltc_with_phantom_parents(ds, summary, effective, extra, log)
    return Observed(summary, annotated, id_map, effective, reference, ltc_filled), None


def _ltc_with_phantom_parents(
    ds: Path, summary: dict[str, Any], effective: dict[str, Any], extra: list[str], log: Path
) -> dict[str, Any]:
    """``ne_long_term_contributions`` with each half-founder's missing parent filled by a phantom founder.

    The estimator refuses any pedigree with a half-founder (rwaples/pedsum#9), so it reruns
    on ``validate --fill-half-founders`` output, kept in its own directories
    so every check still reads the unfilled pedigree. Without half-founders
    the fill changes nothing and the main record is reused.
    """
    if summary["pedigree"]["structure"]["size_structure"]["n_half_founders"] == 0:
        return effective["effective_size"]["ne_long_term_contributions"]
    run_pedsum(
        [
            "validate",
            "--in",
            str(ds / "input.tsv"),
            "--out",
            str(ds / "validate_filled"),
            "--fill-half-founders",
            *extra,
        ],
        log,
    )
    filled = ds / "validate_filled" / "validate.tsv.gz"
    if not filled.exists():
        return {"ne": None, "reason": "error", "code": "validate --fill-half-founders wrote no pedigree"}
    out = ds / "effective_filled"
    es = ["effective-size", "--in", str(filled), "--out", str(out), "--estimators", "ne_long_term_contributions"]
    code = run_pedsum([*es, *extra], log)
    if code != 0:
        return {"ne": None, "reason": "error", "code": f"effective-size exited {code}"}
    return yaml.safe_load((out / "effective_size.yaml").read_text())["effective_size"]["ne_long_term_contributions"]


def overview_row(name: str, obs: Observed) -> dict[str, Any]:
    """One dataset's headline pedsum statistics and every Ne estimate, for pedsum_all.tsv."""
    size = obs.summary["pedigree"]["structure"]["size_structure"]
    inbreeding = obs.summary["pedigree"]["relatedness"]["inbreeding"]
    founders = obs.summary["pedigree"]["founders"]["founder_contribution"]
    row: dict[str, Any] = {
        "dataset": name,
        "N": obs.summary["n_total"],
        "founders": size["n_founders"],
        "half_founders": size["n_half_founders"],
        "max_depth": size["max_depth"],
        "components": size["n_components"],
        "frac_inbred": inbreeding["frac_inbred"],
        "mean_F": inbreeding["mean_F"],
        "max_F": inbreeding["max_F"],
        "effective_founders_by_descendant_paths": founders.get("effective_founders_by_descendant_paths"),
    }
    estimates = obs.effective["effective_size"] if obs.effective else {}
    for est in ALL_ESTIMATORS:
        record = estimates.get(est, {})
        if record.get("ne") is not None:
            row[est] = record["ne"]
        elif record.get("reason") == "not_requested":
            row[est] = "skipped: unknown sex"
        else:
            row[est] = ":".join(x for x in (record.get("reason"), record.get("code")) if x)
    row["ne_individual_delta_f_unrelated_founders"] = estimates.get("ne_individual_delta_f", {}).get(
        "ne_unrelated_founders"
    )
    filled = obs.ltc_filled or {}
    row[LTC_FILLED] = (
        filled["ne"]
        if filled.get("ne") is not None
        else ":".join(x for x in (filled.get("reason"), filled.get("code")) if x)
    )
    return row


def _fmt(x: float | None) -> str:
    if x is None:
        return ""
    return f"{x:.0f}" if float(x).is_integer() else f"{x:.7g}"


def write_reports(results: list[Result], overview: list[dict[str, Any]], out: Path) -> None:
    """Write results.tsv, pedsum_all.tsv and results.md."""
    out.mkdir(parents=True, exist_ok=True)
    fields = ["dataset", "stat", "published", "observed", "status", "via", "gap", "source", "note"]
    with (out / "results.tsv").open("w", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(fields)
        for r in results:
            w.writerow(
                [_fmt(v) if k in ("published", "observed") else v for k, v in ((f, getattr(r, f)) for f in fields)]
            )
    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    lines = [
        "# pedsum against published pedigree statistics",
        "",
        "Generated by `run_published.py`. Statuses: "
        "PASS (pedsum CLI output matches), PASS (engine) (matches, but computed with the "
        "pedigree_graph API because pedsum does not report it yet), DIFF (known convention "
        "difference), GAP (not reported; the gap id refers to docs/missing-statistics.md), "
        "FAIL, ERROR.",
        "",
        "Totals: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())),
        "",
        "| Dataset | Statistic | Published | pedsum | Status | Gap | Source | Note |",
        "|---|---|---|---|---|---|---|---|",
    ]
    lines += [
        f"| {r.dataset} | {r.stat} | {_fmt(r.published)} | {_fmt(r.observed)} | {r.status} | {r.gap} | {r.source} | {r.note} |"
        for r in results
    ]
    if overview:
        cols = list(overview[0])
        with (out / "pedsum_all.tsv").open("w", newline="") as fh:
            w = csv.writer(fh, delimiter="\t", lineterminator="\n")
            w.writerow(cols)
            w.writerows([["" if row[c] is None else row[c] for c in cols] for row in overview])
        ltc = ALL_ESTIMATORS.index("ne_long_term_contributions") + 1
        estimators = [*ALL_ESTIMATORS[:ltc], LTC_FILLED, *ALL_ESTIMATORS[ltc:]]
        shown = ["dataset", "N", "founders", "half_founders", "max_depth", "frac_inbred", "mean_F", *estimators]
        lines += [
            "",
            "## pedsum on every dataset",
            "",
            "Headline `summarize` statistics and all eight `effective-size` estimators, whether or not a "
            "published value exists. A non-numeric Ne cell gives the reason there is no estimate. "
            f"`{LTC_FILLED}` reruns `ne_long_term_contributions` after `validate --fill-half-founders`. "
            "All columns are in `pedsum_all.tsv`.",
            "",
            "| " + " | ".join(shown) + " |",
            "|" + "---|" * len(shown),
        ]
        lines += ["| " + " | ".join("" if row[c] is None else str(row[c]) for c in shown) + " |" for row in overview]
    (out / "results.md").write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--cases", type=Path, default=HERE / "cases.yaml")
    p.add_argument("--cache", type=Path, default=HERE / ".cache", help="downloaded source files")
    p.add_argument("--work", type=Path, default=HERE / ".work", help="converted inputs and pedsum outputs")
    p.add_argument("--out", type=Path, default=HERE / "results", help="where results.md/.tsv are written")
    p.add_argument("--only", default="", help="comma-separated dataset names")
    args = p.parse_args(argv)

    cases = yaml.safe_load(args.cases.read_text())
    wanted = [s for s in args.only.split(",") if s] or list(cases["datasets"])
    results: list[Result] = []
    overview: list[dict[str, Any]] = []
    for name in wanted:
        print(f"[{name}] running", file=sys.stderr)
        try:
            obs, error = run_dataset(name, cases["datasets"][name], args.cache, args.work)
        except Exception as exc:  # one broken dataset should not hide the others
            obs, error = None, f"{type(exc).__name__}: {exc}"
        results += [evaluate(c, obs, error) for c in cases["checks"] if c["dataset"] == name]
        if obs is not None:
            overview.append(overview_row(name, obs))

    write_reports(results, overview, args.out)
    width = max(len(r.stat) for r in results)
    dwidth = max(len(r.dataset) for r in results)
    for r in results:
        print(
            f"{r.status:14} {r.dataset:{dwidth}} {r.stat:{width}}  published={_fmt(r.published):>10}  pedsum={_fmt(r.observed):>10}"
        )
    print(f"wrote {args.out / 'results.md'}", file=sys.stderr)
    return 1 if any(r.status in ("FAIL", "ERROR") for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
