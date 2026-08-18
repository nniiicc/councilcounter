# Data Dictionary — councilcounter

A longitudinal panel of municipal elected officials: who held every council seat and the
mayoralty in 64 cities across 12 states, 2019–2026, with a source URL attached to every name.

Counts as of 2026-08-18: 64 cities, 1,050 persons, 405 cycles, 2,005 tenures, 66 gaps,
5,657 panel rows (5,591 sourced / 43 unrecoverable / 23 vacant), 99.2% of knowable
seat-years sourced.

## Provenance chain

```
raw/{city_id}.json   ← written by per-city research agents; THE source of truth
      │  python3 ingest.py   (idempotent; owns person identity and FK resolution)
      ▼
councilcounter.db    ← derived; rebuildable at any time; not committed
      │  schema.sql  (DDL: 7 tables, 3 views)
      ▼
panel view           ← the flat deliverable, one row per (city, year, seat)
```

Two invariants are enforced at the schema level: `tenures.source_url` and `gaps.attempted`
are `NOT NULL`. **No URL, no row** — every name in the panel is traceable to the document it
was read from, and every failure records what was tried.

A third principle is structural: the data model holds only **evidentiary** fields — things
that change how much you believe a row. Everything describing *how* data was found (ladder
rungs, tool calls, search counts) lives in `run_log`, which is not part of the panel.

---

## Table: `cities` — one row per municipality (64 rows)

| Column | Type | Null | Meaning |
|---|---|---|---|
| `city_id` | INTEGER PK | no | Stable ID, 1–64; matches `raw/{city_id}.json` |
| `city` | TEXT | no | Census-style name (`Auburn city`, `Gloucester Township`) |
| `state` | TEXT | no | Full state name |
| `fips` | TEXT | yes | Census place FIPS code |
| `gov_form` | TEXT | yes | `mayor-council` \| `council-manager` \| `township` (observed; schema also allows `commission`) |
| `seat_count` | INTEGER | yes | **Full voting members of the governing body.** A separately-elected mayor counts iff charter/statute gives them a full vote as a member; tie-break-only mayors and non-member executives do not; council-selected mayors occupy a counted seat; titles (vice mayor, president) are not seats. Restructured cities carry the end-of-panel (2026) count — history in `stagger_pattern`. Normalized 2026-08-18 against charter/statute text; per-city audit in `registry-corrections.md`. |
| `seat_scheme` | TEXT | yes | `at-large` \| `ward` \| `position-numbered` \| `mixed` |
| `term_length` | INTEGER | yes | Years per term |
| `stagger_pattern` | TEXT | yes | Free text: which seats are elected in which cycles. Also carries mid-panel restructuring history (Homewood 2025, Ojai/Yuba City districting, New Brunswick expansion). |
| `mayor_selection` | TEXT | no | `elected` (separate citywide race) \| `council-selected` \| free text for the one no-mayor city (Amherst MA) |
| `election_month` | TEXT | yes | Free text (`November odd years (August odd-year primary)`) |
| `archive_url` | TEXT | yes | Corrected working archive URL from the input census |
| `notes` | TEXT | yes | Free text |

Unique on `(city, state)`. Two cities are named Bristol (TN and VA).

## Table: `persons` — one row per person per city (1,050 rows)

| Column | Type | Null | Meaning |
|---|---|---|---|
| `person_id` | INTEGER PK | no | |
| `name_canonical` | TEXT | no | Preferred full form |
| `name_variants` | TEXT (JSON array) | yes | All observed forms, e.g. `["Peggy McQuaid", "Peggy (Margaret) McQuaid", "Margaret McQuaid"]` |
| `first_name_sourced` | INTEGER (0/1) | no | 0 when only a surname was ever sourced (minutes give surnames only). Currently 1 for all but one person. |

**Identity is city-scoped**: `ingest.py` resolves names within a city only. The same human
serving in two cities would get two `person_id`s — cross-city person linkage is deliberately
not attempted. Two people are never merged on surname alone.

## Table: `cycles` — one row per *expected* election cycle (405 rows)

The unit of work: a cycle exists whether or not its results were found.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `cycle_id` | INTEGER PK | no | |
| `city_id` | INTEGER FK | no | |
| `election_date` | TEXT (ISO) | no | Unique per city |
| `seats_up` | INTEGER | yes | Seats contested in this cycle |
| `status` | TEXT | no | `sourced` (372) \| `flagged` (32: found but with a caveat, e.g. results located late or partially) \| `unrecoverable` (1) |
| `source_url` | TEXT | yes | Results document |

Blast radius (`seats_up × years to next cycle`) is **computed** by the `cycle_cost` view,
never stored.

## Table: `tenures` — the substantive output (2,005 rows)

One row per person per seat per continuous span.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `tenure_id` | INTEGER PK | no | |
| `city_id`, `person_id` | INTEGER FK | no | |
| `seat_label` | TEXT | no | `Ward 3`, `Position 5`, `District 2`, `At-Large`, `Mayor`, `Vice Mayor`, `Council President`, `Mayor Pro Tem`, … |
| `role` | TEXT | no | `council_member` (1,420) \| `vice_mayor` (310) \| `mayor` (242) \| `alderman` (33). Schema also allows `commissioner`, `selectman` (unused). |
| `start_date` | TEXT (ISO) | no | Day precision where known, else `YYYY-01-01`. Spans from 2015 appear because a term that began pre-2019 still covers panel years. |
| `end_date` | TEXT (ISO) | yes | NULL = ongoing as of collection |
| `entry_mode` | TEXT | yes | `elected` (1,506) \| `appointed` (398) \| `succeeded` (18: moved up into the office, pairs with an `elevated` exit elsewhere) \| `unknown` (83) |
| `exit_mode` | TEXT | yes | `term_end` (1,127) \| `ongoing` (572) \| `resigned` (156) \| `defeated` (82) \| `elevated` (31: vacated by taking another office — not a resignation) \| `unknown` (24) \| `died` (10) \| `recalled` (3) |
| `source_url` | TEXT | **no** | **Provenance, enforced. No URL, no row.** |
| `retrieval_method` | TEXT | no | `minutes_rollcall` (494) \| `newspaper` (345) \| `audit_report` (306) \| `other` (299) \| `county_canvass` (295) \| `state_portal` (197) \| `public_notice` (58) \| `trade_press` (8) \| `municipal_league` (3) |
| `confidence` | TEXT | no | See Confidence below |
| `cycle_id` | INTEGER FK | yes | The election that seated this tenure; NULL for appointments |

**Leadership rows are additive.** A council member serving as vice mayor / council president
/ mayor pro tem gets a *separate* `vice_mayor` tenure row alongside their seat row (382 such
overlaps). To count bodies or people, count distinct `person_id`s — not rows.

**Confidence**: `high` (1,632) = official election record or audit report naming the person
for the specific cycle; `medium` (328) = single secondary source, or minutes roll call giving
surname only; `low` (45) = inferred by continuity or elimination rather than a dated record.
Continuity inference ("held it in 2018 and 2022, so presumably 2020") is always `low` — it is
the most common route to a confident-looking wrong answer. Low-confidence rows are **included
and flagged, never excluded**.

## Table: `gaps` — attempted and not sourced (66 rows)

Seat-years that cannot live in `tenures` (no person, no URL). `attempted` carries the
provenance of the negative result — what separates "the record is unreachable" from "nobody
checked."

| Column | Type | Null | Meaning |
|---|---|---|---|
| `gap_id` | INTEGER PK | no | |
| `city_id` | INTEGER FK | no | |
| `year` | INTEGER | no | |
| `seat_label` | TEXT | no | |
| `reason` | TEXT | no | `vacant` (23) \| `other` (18) \| `no_archive` (9) \| `budget_cap` (7) \| `missing_cycle` (6) \| `scanned_pdf` (3). Schema also allows `robots_blocked`, `homonym_unresolved`. |
| `attempted` | TEXT | **no** | What was tried and how it failed. **Required.** |
| `notes` | TEXT | yes | |

`vacant` is **not a failure**: the seat was lawfully empty and we know it, often to the day.
The panel reports it as its own status and the coverage view excludes it from the
denominator — a seat nobody held is a complete finding, not a failed search.

Unique on `(city_id, year, seat_label)`; duplicate findings are merged by concatenating
their `attempted` trails.

## Table: `run_log` — process state, not data (655 rows)

Exists so "where did I stop" is a query. Nothing in it is a fact about municipal government.

| Column | Type | Null | Meaning |
|---|---|---|---|
| `entry_id` | INTEGER PK | no | |
| `city_id`, `cycle_id` | INTEGER FK | yes | `cycle_id` NULL for city-level work |
| `step` | TEXT | no | `registry` (77) \| `cycle_calendar` (65) \| `cycle_retrieval` (127) \| `midterm_check` (87) \| `escalation` (97) \| `validation` (138) \| `export` (64) |
| `rung` | INTEGER | yes | Escalation-ladder rung 1–7; only meaningful when `step='escalation'`. Deliberately not stored on `cycles` — rung numbers change meaning if the ladder is reordered. |
| `outcome` | TEXT | no | `success` (570) \| `blocked` (48) \| `not_found` (34) \| `budget_cap` (3) |
| `tool_calls`, `searches` | INTEGER | yes | Budget tracking |
| `detail` | TEXT | yes | Free text; carries re-run flags (e.g. Montclair after Nov 2026) |
| `logged_at` | TEXT | no | Defaults to `datetime('now')` |

## Table: `years`

Single-column spine, seeded 2019–2026. Joins explode tenure spans into seat-years.

---

## View: `panel` — the deliverable

One row per (city, year, seat) — spans exploded against `years`, gaps unioned in so the
panel is complete rather than silently short.

| Column | From | Notes |
|---|---|---|
| `city`, `state` | cities | |
| `year` | years / gaps | 2019–2026 |
| `seat_label` | tenures / gaps | |
| `role` | tenures | NULL on gap rows |
| `person` | persons.name_canonical | NULL on gap rows |
| `entry_mode`, `exit_mode` | tenures | NULL on gap rows |
| `source_url`, `retrieval_method`, `confidence` | tenures | NULL on gap rows |
| `status` | derived | `sourced` \| `unrecoverable` \| `vacant` |

Interpretation rules:
- **Two people in one seat in one year → two rows for that cell.** Correct, not a defect —
  it means turnover (resignation, appointment, special election) inside that year.
- A person with a leadership title contributes rows under both their seat and the title.
- A tenure ongoing at collection time (`end_date` NULL) fills every year through 2026.

## View: `cycle_cost`

Per cycle: `blast_radius_seat_years = seats_up × years until the next cycle` (falling back
to years remaining in the panel). Escalation triage: what a missing cycle costs.

## View: `coverage`

Per city: `seat_years_sourced`, `seat_years_unrecoverable`, `seat_years_vacant`,
`low_confidence_rows`, and `pct_sourced = sourced / (sourced + unrecoverable)`. Vacant
seat-years are excluded from the denominator.

---

## Raw research files: `raw/{city_id}.json`

The real source of truth; the DB is derived. Back these up before letting anything edit one.

| Key | Contents |
|---|---|
| `city_id`, `city`, `state` | Identity (state may be full name or abbreviation; the DB normalizes) |
| `profile` | `gov_form`, `seat_count`, `seat_scheme`, `term_length`, `stagger_pattern`, `mayor_selection`, `election_month`, `profile_source_url` |
| `cycles[]` | `election_date`, `seats_up`, `status`, `source_url` |
| `tenures[]` | `person`, `name_variants`, `first_name_sourced`, `seat_label`, `role`, `start_date`, `end_date`, `entry_mode`, `exit_mode`, `source_url`, `retrieval_method`, `confidence`, `election_date` (resolved to `cycle_id` at ingest) |
| `gaps[]` | `year`, `seat_label`, `reason`, `attempted`, `notes` |
| `run_log[]` | `step`, `rung`, `outcome`, `tool_calls`, `searches`, `detail` |
| `totals` | `tool_calls`, `searches` for the city's research run |

Ingest behaviors worth knowing when reading the data:
- **Caveat diversion**: a gap row whose seat-year is already sourced is treated as an
  annotation and diverted to `run_log`, so the panel never emits a contradictory second row.
- **Composite gap labels** (`"Ward 1 / Ward 2"`) are split into one gap per seat.
- Re-ingest is idempotent per city: the city's rows are cleared and rebuilt, orphaned
  persons pruned.

## Known limitations

- `pct_sourced` is computed at year granularity in the `coverage` view; `ingest.py` reports
  the stricter day-level coverage and warns on uncovered seat-years.
- Montclair NJ carries an unexpired at-large term on the November 2026 ballot — re-run that
  city after certification.
- Amherst MA has no mayor; its `mayor_selection` is explanatory text, not an enum value.
- The panel does not claim to be verified. The method catches most errors, not all —
  spot-check quoted roster text against `source_url` before load-bearing use.
