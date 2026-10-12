"""Write cleaners/fixtures/: one small pedigree per problem in pedsum#7's comparison table.

Every fixture is the five-person core below with one defect added, so each
cleaner sees a pedigree that is valid except for the problem under test.
Missing values are ``NA``, which every program reads as missing, except in
``zero_missing``, which tests ``0`` as the missing-parent code.

Run: pixi run python cleaners/make_fixtures.py
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).parent / "fixtures"
HEADER = ("id", "mother", "father", "sex", "birth_year")

# id, mother, father, sex, birth_year
CORE = [
    ("1", "NA", "NA", "F", "1990"),
    ("2", "NA", "NA", "M", "1990"),
    ("3", "1", "2", "F", "2000"),
    ("4", "1", "2", "M", "2000"),
    ("5", "3", "4", "F", "2010"),
]


def core(**rows: tuple[str, ...]) -> list[tuple[str, ...]]:
    """The core with the rows named ``r<id>`` replaced."""
    return [rows.get(f"r{r[0]}", r) for r in CORE]


# name -> (table row in pedsum#7, what the defect is, rows)
FIXTURES: dict[str, tuple[str, str, list[tuple[str, ...]]]] = {
    "clean": ("control", "no defect", core()),
    "parent_not_a_row": (
        "Parent referenced but not a row",
        "father 9 of id 5 has no row",
        core(r5=("5", "3", "9", "F", "2010")),
    ),
    "missing_parent_both_roles": (
        "Parent referenced but not a row",
        "9 has no row and is the mother of 6 and the father of 7",
        [*CORE, ("6", "9", "4", "F", "2010"), ("7", "3", "9", "M", "2010")],
    ),
    "dup_exact": ("Duplicate ID", "id 4 appears twice, identical rows", [*CORE, CORE[3]]),
    "dup_conflict": (
        "Duplicate ID",
        "id 4 appears twice, the second row with no parents",
        [*CORE, ("4", "NA", "NA", "M", "2000")],
    ),
    "dup_conflict_fewer_first": (
        "Duplicate ID",
        "id 4 appears twice, the first row with no parents (tells 'first row' from 'most parents')",
        [*CORE[:3], ("4", "NA", "NA", "M", "2000"), CORE[3], CORE[4]],
    ),
    # Founders 20 (M) and 21 (F) give every cycle member two parents, so a
    # program that rejects half-founders still has to look at the cycle.
    "cycle2_mixed": (
        "Cycle / own ancestor",
        "3 is the mother of 2, 2 is the father of 3",
        [*core(r2=("2", "3", "20", "M", "1990")), ("20", "NA", "NA", "M", "1980")],
    ),
    "cycle2_dam_only": (
        "Cycle / own ancestor",
        "1 and 3 are each other's mother; 4 and 5 descend from the cycle",
        [*core(r1=("1", "3", "20", "F", "1990")), ("20", "NA", "NA", "M", "1980")],
    ),
    "cycle3_mixed": (
        "Cycle / own ancestor",
        "separate 3-cycle 10 -(mother)-> 12 -(father)-> 11 -(mother)-> 10",
        [
            *CORE,
            ("20", "NA", "NA", "M", "1980"),
            ("21", "NA", "NA", "F", "1980"),
            ("10", "12", "20", "F", "1990"),
            ("11", "10", "20", "M", "1990"),
            ("12", "21", "11", "F", "1990"),
        ],
    ),
    "own_parent": ("Own parent", "id 5 is its own mother", core(r5=("5", "5", "4", "F", "2010"))),
    "mother_eq_father": (
        "Mother ID = father ID in the same row",
        "id 5 has mother 4 and father 4 (4 is male)",
        core(r5=("5", "4", "4", "F", "2010")),
    ),
    "both_roles_unsexed": (
        "Individual used as both mother and father",
        "unsexed 6 is the mother of 7 and the father of 8",
        [*CORE, ("6", "NA", "NA", "NA", "2000"), ("7", "6", "4", "F", "2010"), ("8", "3", "6", "M", "2010")],
    ),
    "both_roles_sexed": (
        "Individual used as both mother and father",
        "male 4 is the father of 5 and the mother of 6",
        [*CORE, ("6", "4", "2", "F", "2010")],
    ),
    "sex_contradicts_role": (
        "Recorded sex contradicts parent role",
        "2 is recorded female and is only ever a father",
        core(r2=("2", "NA", "NA", "F", "1990")),
    ),
    "missing_sex_parent": (
        "Missing sex",
        "mother 1 has no sex recorded",
        core(r1=("1", "NA", "NA", "NA", "1990")),
    ),
    "missing_sex_nonparent": (
        "Missing sex",
        "5, who has no offspring, has no sex recorded",
        core(r5=("5", "3", "4", "NA", "2010")),
    ),
    "one_parent_known": (
        "Only one parent known",
        "5 has a mother but no father",
        core(r5=("5", "3", "NA", "F", "2010")),
    ),
    "parents_after_offspring": ("Parents listed after offspring", "the core rows in reverse order", CORE[::-1]),
    "zero_missing": (
        "Missing-parent codes",
        "founders 1 and 2 have parents written 0; no row has id 0",
        core(r1=("1", "0", "0", "F", "1990"), r2=("2", "0", "0", "M", "1990")),
    ),
    "string_ids": (
        "ID type / renumbering",
        "IDs A1..A5",
        [tuple("A" + v if v not in ("NA",) and i < 3 else v for i, v in enumerate(r)) for r in CORE],
    ),
    "missing_id": ("Rows removed", "a sixth row has no id", [*CORE, ("NA", "3", "4", "M", "2010")]),
    "parent_born_after": (
        "Parent born after offspring",
        "3 is born 1980, before its parents (1990)",
        core(r3=("3", "1", "2", "F", "1980")),
    ),
    "young_parent": (
        "Parent born after offspring",
        "5 is born 2001, one year after its parents (2000)",
        core(r5=("5", "3", "4", "F", "2001")),
    ),
}


def main() -> None:
    """Write every fixture and fixtures.tsv."""
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.tsv"):
        old.unlink()
    index = ["name\ttable_row\tdefect"]
    for name, (row, defect, rows) in FIXTURES.items():
        lines = ["\t".join(HEADER), *("\t".join(r) for r in rows)]
        (OUT / f"{name}.tsv").write_text("\n".join(lines) + "\n")
        index.append(f"{name}\t{row}\t{defect}")
    (Path(__file__).parent / "fixtures.tsv").write_text("\n".join(index) + "\n")
    print(f"wrote {len(FIXTURES)} fixtures to {OUT}")


if __name__ == "__main__":
    main()
