# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A **research data project**, not an application. The goal is a longitudinal panel of municipal
elected officials — who held every council seat and the mayoralty in **64 cities across 12 states,
2019–2026** — with a source URL attached to every name. There is no build, no test suite, and no
application code. The artifacts are a SQLite schema, a fetch-verified input census, and a handoff
document.

The work is executed by invoking the `municipal-roster-panel` skill **by name** (via the Skill
tool) — do not rely on it auto-triggering. **The method lives in the skill**: the pipeline, the
12-state source registry, and the 7-rung escalation ladder are all documented there, not here.

## Read before doing anything

[HANDOFF.md](HANDOFF.md) is the operating document. It carries what the skill cannot: decisions
already made (do not re-litigate them), measured cost baselines, open items, and — critically —
§6 "Do not rediscover these", a list of dead sources (Wayback, Ballotpedia, Clarity Elections,
several state JS portals) that each cost significant time to rule out.

## Files

| File | Role |
|---|---|
| `HANDOFF.md` | Session protocol, decisions, baselines, open items. Start here. |
| `registry-corrections.md` | Findings from live runs that correct the skill's state registry. **Read with HANDOFF.md** — the registry is read-only inside the skill, so corrections accumulate here and must be folded into agent prompts. |
| `schema.sql` | Runnable DDL. 7 tables, 3 views, seeds `years` 2019–2026. Tested. |
| `ingest.py` | Loads `raw/{city_id}.json` research files into the panel. Owns person identity, FK resolution, and the gap-vs-caveat rules. Idempotent per city. |
| `raw/*.json` | One research file per city, written by the research agents. The DB is derived from these, so they are the real source of truth — back them up before letting an agent edit one. |
| `councilcounter_input_cities.xlsx` | The canonical input — the feasibility census, all 64 cities audited by live fetch. HANDOFF.md refers to this file by its original name, `City_Council_2019-2026_Feasibility_Census.xlsx`; same workbook. Do **not** use the user's original city spreadsheet. |

The workbook's `Archive Census` sheet is the one to load: one row per city with a **working**
archive URL, platform, blocker type, and earliest year confirmed. 40 of the given URLs were stale
or wrong and were corrected (see the `URL Corrections` sheet); 8 cities have no working archive at
all.

## Setup

```bash
sqlite3 councilcounter.db < schema.sql
```

The `.db` is the primary deliverable and is **not** committed. Produce an xlsx of the `panel` view
only if asked.

Load research results (idempotent — re-run freely, per city or for everything):

```bash
python3 ingest.py
```

Watch its output for two warnings that the schema itself cannot catch: **uncovered seat-years**
(a cell present in neither `tenures` nor `gaps`, i.e. a hole in the deliverable) and
**caveats diverted** (gap rows that annotate an already-sourced seat-year and would otherwise
emit a contradictory second panel row).

Progress and resume state:

```bash
sqlite3 councilcounter.db "SELECT * FROM coverage ORDER BY pct_sourced;"
```

```bash
sqlite3 councilcounter.db "SELECT * FROM cycle_cost WHERE status='flagged' ORDER BY blast_radius_seat_years DESC;"
```

## Data model — the design rules that matter

Reading `schema.sql` shows the tables; these are the invariants behind them, which it does not.

- **Evidentiary fields only.** Anything describing *how* data was found lives in `run_log`, which
  is not part of the panel. Ladder rung and search cost describe the search, not the world — they
  were deliberately removed from `cycles`.
- **Provenance is enforced at the schema level.** `tenures.source_url` and `gaps.attempted` are
  `NOT NULL`. No URL, no row.
- **`cycles` is the unit of work** — one row per *expected* election cycle, whether or not it was
  found. A cycle is `sourced`, `flagged`, or `unrecoverable`.
- **`gaps` is not an error table.** It holds seat-years that were attempted and could not be
  sourced. They cannot live in `tenures` (no person, no URL), so they are unioned into the `panel`
  view — the panel is complete rather than silently short.
- **Nothing derived is stored.** Blast radius is computed by the `cycle_cost` view; span explosion
  into seat-years happens in the `panel` view.
- **Low-confidence rows are included and flagged**, never excluded.
- Two people holding one seat in one year correctly yields two `panel` rows for that cell.

## Working rules

- **Batch by state, not alphabetically.** The source registry is per-state; grouping keeps the
  relevant entry in context.
- **Write to the `.db` continuously**, not at the end. A session that dies mid-batch should lose
  minutes, not hours.
- **Log every step to `run_log`, including failures.** "Where did I stop" must be a query, not a
  reconstruction.
- **Cap effort at 60 tool calls per city**, then bank partial results and move on. Expect ~92k
  tokens and ~24 WebSearches per city with the registry.
- **Small cities cost more than large ones and return less.** This is measured, not a guess. Budget
  accordingly — but do not skip them.
- **Do not skip the mid-term appointment check.** It is the known failure mode of the registry
  approach: appointments never appear in election results, and a registry-assisted run silently
  missed one that the slower baseline caught.
- **Searching for a roster by year does not work.** `<city> <state> council members 2019` returns
  the present-day roster in every case tested. Search for the *election that seated the body*.
- **Spot-check quoted roster text against source.** The page-fetching layer was observed inventing
  first names for a document containing only surnames — and inventing them *correctly*, which makes
  the failure invisible by inspection.
- **Default to respecting robots.txt.** This caps South Dakota at ~50%; the user has not authorized
  otherwise, and this is not a call to make unilaterally.
