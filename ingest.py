"""Ingest per-city research JSON into the councilcounter panel database.

Research agents write one JSON file per city to ``raw/{city_id}.json``. This script
loads those files into the schema defined in ``schema.sql``, resolving foreign keys
and person identity centrally so that concurrent writers never have to.

Ingest is idempotent: re-running for a city deletes that city's derived rows and
rewrites them, so a re-researched city can simply be dropped in and reloaded.

Usage::

    python3 ingest.py                 # ingest every file in raw/
    python3 ingest.py raw/53.json     # ingest specific files
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import date
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent / "councilcounter.db"
RAW_DIR = Path(__file__).parent / "raw"
PANEL_YEARS = range(2019, 2027)

PROFILE_FIELDS = (
    "gov_form",
    "seat_count",
    "seat_scheme",
    "term_length",
    "stagger_pattern",
    "mayor_selection",
    "election_month",
)


class ValidationError(Exception):
    """A record violates a provenance or referential rule and must not be loaded."""


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    """Open the panel database with foreign keys and WAL enabled.

    Resolves ``DB_PATH`` at call time rather than binding it as a default, so tests
    can point the module at a throwaway database.
    """
    con = sqlite3.connect(db_path or DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    con.execute("PRAGMA synchronous = NORMAL")
    return con


def validate(payload: dict[str, Any]) -> list[str]:
    """Return a list of fatal problems with a city payload.

    Enforces the two rules the schema also enforces, but with a filename and index
    attached so the failure is diagnosable before it reaches SQLite: every tenure
    carries a source URL, and every gap carries an attempted-and-failed trail.
    """
    problems: list[str] = []
    if not payload.get("city_id"):
        problems.append("missing city_id")
    for i, tenure in enumerate(payload.get("tenures", [])):
        if not tenure.get("source_url"):
            problems.append(f"tenures[{i}] ({tenure.get('person')!r}): no source_url")
        if not tenure.get("person"):
            problems.append(f"tenures[{i}]: no person name")
        if not tenure.get("start_date"):
            problems.append(f"tenures[{i}] ({tenure.get('person')!r}): no start_date")
    for i, gap in enumerate(payload.get("gaps", [])):
        if not gap.get("attempted"):
            problems.append(f"gaps[{i}] (year {gap.get('year')}): no attempted trail")
    return problems


def clear_city(con: sqlite3.Connection, city_id: int) -> None:
    """Remove a city's derived rows so it can be re-ingested cleanly.

    Deletion order respects the foreign keys: tenures reference cycles, and run_log
    references both. Persons are left alone and garbage-collected separately, since
    person_id is shared across the table.
    """
    con.execute("DELETE FROM tenures WHERE city_id = ?", (city_id,))
    con.execute("DELETE FROM gaps WHERE city_id = ?", (city_id,))
    con.execute("DELETE FROM run_log WHERE city_id = ?", (city_id,))
    con.execute("DELETE FROM cycles WHERE city_id = ?", (city_id,))


def prune_orphan_persons(con: sqlite3.Connection) -> int:
    """Delete persons no longer referenced by any tenure. Returns the count."""
    cur = con.execute(
        "DELETE FROM persons WHERE person_id NOT IN (SELECT person_id FROM tenures)"
    )
    return cur.rowcount


def resolve_person(
    con: sqlite3.Connection,
    cache: dict[tuple[int, str], int],
    city_id: int,
    name: str,
    variants: list[str] | None,
    first_name_sourced: int,
) -> int:
    """Return a person_id for a name, creating the row if needed.

    Identity is scoped to the city. Two people with the same name in different
    cities get separate rows: a wrongly merged person is a silent data error, while
    a split person is visible and correctable. This is the same reasoning behind the
    schema's refusal to match on surname alone.
    """
    key = (city_id, name)
    if key in cache:
        return cache[key]
    cur = con.execute(
        "INSERT INTO persons (name_canonical, name_variants, first_name_sourced) "
        "VALUES (?, ?, ?)",
        (name, json.dumps(variants) if variants else None, int(first_name_sourced)),
    )
    person_id = int(cur.lastrowid)
    cache[key] = person_id
    return person_id


def update_profile(con: sqlite3.Connection, city_id: int, profile: dict[str, Any]) -> None:
    """Write the researched government-form fields onto the city row."""
    fields = {k: profile.get(k) for k in PROFILE_FIELDS if profile.get(k) is not None}
    if not fields:
        return
    assignments = ", ".join(f"{k} = ?" for k in fields)
    con.execute(
        f"UPDATE cities SET {assignments} WHERE city_id = ?",
        (*fields.values(), city_id),
    )
    if profile.get("profile_source_url"):
        con.execute(
            "UPDATE cities SET notes = COALESCE(notes || ' | ', '') || ? "
            "WHERE city_id = ?",
            (f"profile_source: {profile['profile_source_url']}", city_id),
        )


def ingest_city(con: sqlite3.Connection, path: Path) -> dict[str, int]:
    """Load one city's research JSON. Returns per-table row counts."""
    payload = json.loads(path.read_text())
    problems = validate(payload)
    if problems:
        raise ValidationError(f"{path.name}: " + "; ".join(problems))

    city_id = int(payload["city_id"])
    row = con.execute(
        "SELECT city, state FROM cities WHERE city_id = ?", (city_id,)
    ).fetchone()
    if row is None:
        raise ValidationError(f"{path.name}: city_id {city_id} is not in cities")

    clear_city(con, city_id)
    update_profile(con, city_id, payload.get("profile", {}))

    cycle_ids: dict[str, int] = {}
    for cycle in payload.get("cycles", []):
        cur = con.execute(
            "INSERT INTO cycles (city_id, election_date, seats_up, status, source_url) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                city_id,
                cycle["election_date"],
                cycle.get("seats_up"),
                cycle["status"],
                cycle.get("source_url"),
            ),
        )
        cycle_ids[cycle["election_date"]] = int(cur.lastrowid)

    person_cache: dict[tuple[int, str], int] = {}
    for tenure in payload.get("tenures", []):
        person_id = resolve_person(
            con,
            person_cache,
            city_id,
            tenure["person"],
            tenure.get("name_variants"),
            tenure.get("first_name_sourced", 1),
        )
        con.execute(
            "INSERT INTO tenures (city_id, person_id, seat_label, role, start_date, "
            "end_date, entry_mode, exit_mode, source_url, retrieval_method, "
            "confidence, cycle_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                city_id,
                person_id,
                tenure["seat_label"],
                tenure["role"],
                tenure["start_date"],
                tenure.get("end_date"),
                tenure.get("entry_mode"),
                tenure.get("exit_mode"),
                tenure["source_url"],
                tenure["retrieval_method"],
                tenure["confidence"],
                cycle_ids.get(tenure.get("election_date") or ""),
            ),
        )

    sourced = sourced_seat_years(con, city_id)
    diverted = 0
    for gap in merge_duplicate_gaps(payload.get("gaps", [])):
        if int(gap["year"]) not in PANEL_YEARS:
            # A gap outside the panel's year range describes a cycle that had to be
            # retrieved to anchor terms, not a seat-year being delivered. The panel
            # view unions gaps in without a year filter, so leaving it here would add
            # a row for a year the deliverable does not cover.
            con.execute(
                "INSERT INTO run_log (city_id, step, outcome, detail) "
                "VALUES (?, 'cycle_retrieval', 'blocked', ?)",
                (
                    city_id,
                    f"out-of-range gap {gap['seat_label']} {gap['year']} "
                    f"[{gap['reason']}]: {gap['attempted']}",
                ),
            )
            diverted += 1
            continue
        if is_caveat(gap, sourced):
            # The seat-year already has a sourced tenure, so this is a caveat about
            # a known holder, not an unsourced cell. Writing it to `gaps` would make
            # the panel emit both 'sourced' and 'unrecoverable' for one cell and
            # understate coverage. The substantive uncertainty is already carried by
            # the tenure's `confidence`; the trail belongs in the run log.
            con.execute(
                "INSERT INTO run_log (city_id, step, outcome, detail) "
                "VALUES (?, 'validation', 'success', ?)",
                (
                    city_id,
                    f"caveat on sourced seat-year {gap['seat_label']} {gap['year']} "
                    f"[{gap['reason']}]: {gap['attempted']} {gap.get('notes') or ''}",
                ),
            )
            diverted += 1
            continue
        con.execute(
            "INSERT OR REPLACE INTO gaps (city_id, year, seat_label, reason, "
            "attempted, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (
                city_id,
                gap["year"],
                gap["seat_label"],
                gap["reason"],
                gap["attempted"],
                gap.get("notes"),
            ),
        )

    for entry in payload.get("run_log", []):
        con.execute(
            "INSERT INTO run_log (city_id, cycle_id, step, rung, outcome, tool_calls, "
            "searches, detail) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                city_id,
                cycle_ids.get(entry.get("election_date") or ""),
                entry["step"],
                entry.get("rung"),
                entry["outcome"],
                entry.get("tool_calls"),
                entry.get("searches"),
                entry.get("detail"),
            ),
        )

    counts = {
        "cycles": len(payload.get("cycles", [])),
        "tenures": len(payload.get("tenures", [])),
        "gaps": len(payload.get("gaps", [])) - diverted,
        "run_log": len(payload.get("run_log", [])),
    }
    if diverted:
        counts["caveats_diverted"] = diverted
    return counts


def is_caveat(gap: dict[str, Any], sourced: set[tuple[str, int]]) -> bool:
    """True when a gap row annotates seat-years that are already sourced.

    Researchers sometimes file a note against a composite label such as
    ``"Mayor / Deputy Mayor"`` when the caveat spans two seats that each have their
    own tenure rows. Splitting on the separator lets those resolve; a label whose
    parts are all sourced for that year is a caveat, not an unsourced cell, and
    writing it to `gaps` would emit a contradictory second panel row and invent a
    seat that never existed.
    """
    year = int(gap["year"])
    parts = [p.strip() for p in gap["seat_label"].split("/") if p.strip()]
    return bool(parts) and all((part, year) in sourced for part in parts)


def merge_duplicate_gaps(gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Combine gap rows that share a ``(year, seat_label)`` key.

    ``gaps`` is UNIQUE on ``(city_id, year, seat_label)``, so two rows for one
    seat-year would silently overwrite each other on insert. A researcher recording
    both a vacancy interval and a seat-label ambiguity for the same cell means both
    trails matter, so the ``attempted`` text is concatenated rather than replaced.
    """
    merged: dict[tuple[int, str], dict[str, Any]] = {}
    for gap in gaps:
        key = (int(gap["year"]), gap["seat_label"])
        if key not in merged:
            merged[key] = dict(gap)
            continue
        prior = merged[key]
        prior["attempted"] = f"{prior['attempted']} || {gap['attempted']}"
        notes = [n for n in (prior.get("notes"), gap.get("notes")) if n]
        prior["notes"] = " || ".join(notes) or None
        if prior["reason"] != gap["reason"]:
            # A dated vacancy is a structural fact about the seat; anything else
            # filed against the same cell is commentary on it, and the concatenated
            # `attempted` text preserves that. Never let a note demote a vacancy.
            reasons = {prior["reason"], gap["reason"]}
            prior["reason"] = "vacant" if "vacant" in reasons else "other"
    return list(merged.values())


def sourced_seat_years(con: sqlite3.Connection, city_id: int) -> set[tuple[str, int]]:
    """Return every ``(seat_label, year)`` covered by tenures for the WHOLE year.

    Coverage is measured in days, not years. A tenure ending 2024-02-06 puts its seat
    into calendar 2024 but accounts for only five weeks of it; treating that as a
    covered seat-year would suppress a gap row for the eleven unsourced months and
    silently overstate coverage. Only a seat-year with a sourced holder on every day
    counts as covered, so a partially-sourced year keeps its gap and the panel emits
    both rows for that cell — which is the documented behaviour for a seat that
    changed hands mid-year.
    """
    spans: dict[str, list[tuple[date, date]]] = {}
    for row in con.execute(
        "SELECT seat_label, start_date, end_date FROM tenures WHERE city_id = ?",
        (city_id,),
    ):
        try:
            start = date.fromisoformat(row["start_date"][:10])
            end = (
                date.fromisoformat(row["end_date"][:10])
                if row["end_date"]
                else date(max(PANEL_YEARS), 12, 31)
            )
        except ValueError:
            continue
        spans.setdefault(row["seat_label"], []).append((start, end))

    covered: set[tuple[str, int]] = set()
    for seat, intervals in spans.items():
        for year in PANEL_YEARS:
            jan, dec = date(year, 1, 1), date(year, 12, 31)
            days = set()
            for start, end in intervals:
                lo, hi = max(start, jan), min(end, dec)
                if lo <= hi:
                    days.update(range(lo.toordinal(), hi.toordinal() + 1))
            if len(days) == dec.toordinal() - jan.toordinal() + 1:
                covered.add((seat, year))
    return covered


def report_holes(con: sqlite3.Connection, city_id: int) -> list[str]:
    """Return seat-years covered by neither a tenure nor a gap.

    A seat-year present in neither table is a hole in the deliverable rather than a
    documented negative result, and is the one failure the schema cannot catch.
    """
    seats = [
        r["seat_label"]
        for r in con.execute(
            "SELECT DISTINCT seat_label FROM tenures WHERE city_id = ? "
            "UNION SELECT DISTINCT seat_label FROM gaps WHERE city_id = ?",
            (city_id, city_id),
        )
    ]
    covered = {
        (r["seat_label"], r["year"])
        for r in con.execute(
            "SELECT seat_label, year FROM panel WHERE city = "
            "(SELECT city FROM cities WHERE city_id = ?) AND state = "
            "(SELECT state FROM cities WHERE city_id = ?)",
            (city_id, city_id),
        )
    }
    return [
        f"{seat} {year}"
        for seat in seats
        for year in PANEL_YEARS
        if (seat, year) not in covered
    ]


def main(argv: list[str]) -> int:
    """Ingest the given raw files, or every file in ``raw/`` when none are given."""
    paths = [Path(a) for a in argv[1:]] or sorted(RAW_DIR.glob("*.json"))
    if not paths:
        print("no raw/*.json files to ingest")
        return 0

    con = connect()
    loaded, failed = 0, 0
    for path in paths:
        try:
            with con:
                counts = ingest_city(con, path)
            city = con.execute(
                "SELECT city, state FROM cities WHERE city_id = ?",
                (int(json.loads(path.read_text())["city_id"]),),
            ).fetchone()
            holes = report_holes(con, int(json.loads(path.read_text())["city_id"]))
            summary = ", ".join(f"{v} {k}" for k, v in counts.items())
            print(f"OK   {city['city']}, {city['state']}: {summary}")
            if holes:
                print(f"     WARNING {len(holes)} uncovered seat-years: {holes[:6]}")
            loaded += 1
        except (ValidationError, sqlite3.Error, KeyError, json.JSONDecodeError) as exc:
            print(f"FAIL {path.name}: {exc}")
            failed += 1

    pruned = prune_orphan_persons(con)
    con.commit()
    print(f"\n{loaded} loaded, {failed} failed, {pruned} orphan persons pruned")
    for row in con.execute("SELECT * FROM coverage ORDER BY pct_sourced"):
        print(
            f"  {row['city']}, {row['state']}: {row['pct_sourced']}% "
            f"({row['seat_years_sourced']} sourced, "
            f"{row['seat_years_unrecoverable']} unrecoverable, "
            f"{row['low_confidence_rows']} low-confidence)"
        )
    con.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
