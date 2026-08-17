# Output Schema

## Design principle

The panel must distinguish three states that are easy to conflate and expensive to confuse:

| State | Meaning |
|---|---|
| `sourced` | A name, with the URL it was read from |
| `unrecoverable` | Attempted, escalated, failed — with the trail recorded |
| `not_attempted` | Out of scope, or budget cap reached |

Collapsing these into a blank cell destroys the ability to tell a gap in the record from a gap in
the work.

## Tables

### `cities`
| Field | Notes |
|---|---|
| `city_id` | |
| `city`, `state`, `fips` | |
| `gov_form` | `mayor-council`, `council-manager`, `commission`, `township` |
| `seat_count` | Excluding mayor |
| `seat_scheme` | `at-large`, `ward`, `position-numbered`, `mixed` |
| `term_length_years` | |
| `stagger_pattern` | Which seats in which cycles |
| `mayor_selection` | `elected` or `council-selected` — drives whether elections give you the mayor |
| `election_month` | |

### `cycles`
One row per expected election cycle. **This is the unit of work.**

| Field | Notes |
|---|---|
| `cycle_id`, `city_id` | |
| `election_date` | |
| `seats_up` | |
| `status` | `sourced`, `flagged`, `unrecoverable` |
| `source_url` | |

Blast radius — what a missing cycle costs, `seats_up x years until the next cycle` — is **computed
at query time, not stored**. It is a scheduling input for deciding whether to escalate, and it is
derivable from `cycles` and `years`. Storing it would denormalize a value that goes stale whenever
a seat count is corrected.

### `tenures`
The substantive output. One row per person per seat per continuous span.

| Field | Notes |
|---|---|
| `tenure_id`, `city_id`, `person_id` | |
| `seat_label` | `Ward 3`, `Position 5`, `District 2`, `At-Large` |
| `role` | `mayor`, `vice_mayor`, `council_member`, `alderman` |
| `start_date`, `end_date` | `end_date` null if ongoing |
| `entry_mode` | `elected`, `appointed`, `succeeded`, `unknown` |
| `exit_mode` | `term_end`, `resigned`, `recalled`, `died`, `defeated`, `ongoing` |
| `source_url` | **Required.** No URL, no row. |
| `retrieval_method` | `state_portal`, `county_canvass`, `trade_press`, `audit_report`, `newspaper`, `public_notice`, `minutes_rollcall`, `other` |
| `confidence` | See below |

### `persons`
| Field | Notes |
|---|---|
| `person_id` | |
| `name_canonical` | |
| `name_variants` | JSON array — see below |
| `first_name_sourced` | Boolean. Minutes give surnames only. |

### `panel` (derived view)
One row per `(city, year, seat)` — the flat deliverable.

`city, state, year, seat_label, role, person_name, entry_mode, source_url, retrieval_method, confidence, status`

### `gaps`
| Field | Notes |
|---|---|
| `city_id`, `year`, `seat_label` | |
| `reason` | `missing_cycle`, `robots_blocked`, `scanned_pdf`, `no_archive`, `homonym_unresolved`, `budget_cap`, `vacant` |
| `attempted` | Free text: what was tried and how it failed. **Required** — this is the provenance of a negative result, and it is what separates "the record is not reachable" from "nobody checked." |
| `notes` | |

## `gaps` is not a notes field

It has exactly three uses, and only the first two are failures:

| Situation | Where it goes |
|---|---|
| Seat-year whose holder could not be sourced | `gaps`, with `reason` + required `attempted` |
| Seat-year lawfully **vacant**, dated from a source | `gaps` with **`reason: 'vacant'`** — a complete finding, not a failure. Report it as its own panel status and exclude it from the coverage denominator: a seat nobody held is not a failed search |
| A caveat about a seat-year that IS sourced — soft boundary date, ambiguous handover, scope note | **NOT a gap.** The tenure's `confidence` already carries it; put the trail in `run_log` |

A caveat filed as a gap makes the panel emit two contradictory rows for one cell and understates
coverage. Two further rules learned the hard way:

- **Never file a gap for a seat whose existence is unsourced.** One run left eight gap rows for a
  "Mayor Pro Tem" it could not confirm the city even designates — inventing a phantom seat and
  eight unrecoverable seat-years. If the office cannot be established, that is a `run_log` note.
- **Keep `seat_label` identical to the label used in `tenures`.** Descriptive labels
  (`"At-Large (Baydoun's vacated 2024-2027 seat)"`, `"Mayor / Deputy Mayor"`) do not match the real
  seat and each invents a phantom one spanning the whole panel. Detail belongs in `notes`.
- **Never file a gap for a year outside the panel range.**

## The run log — process state, kept out of the data model

Everything about *how* the data was found, as opposed to what it says, lives here. Nothing in this
table is a fact about municipal government, and nothing downstream should read it as one.

Its purpose is resumption: a 64-city panel takes multiple sessions, and this is what makes
"where did I stop" a query rather than a reconstruction.

### `run_log`
| Field | Notes |
|---|---|
| `entry_id` | |
| `city_id` | |
| `cycle_id` | Nullable — some work is city-level, not cycle-level |
| `step` | `registry`, `cycle_calendar`, `cycle_retrieval`, `midterm_check`, `escalation`, `validation` |
| `rung` | 1-7, nullable. Only meaningful for `escalation` steps. **Not stored on `cycles`** — ladder positions are an artifact of the current procedure and change meaning if the ladder is reordered. |
| `outcome` | `success`, `blocked`, `not_found`, `budget_cap` |
| `tool_calls`, `searches` | For budget tracking against the per-session search cap |
| `detail` | Free text |
| `logged_at` | |

### Why this is separate

The test: **does the field change how much you believe a row?**

- `tenures.source_url`, `tenures.retrieval_method`, `tenures.confidence`, `gaps.attempted` — **yes.**
  A name from a state canvass and a name from a hyperlocal blog carry different weight, and a
  documented failed search is different evidence from silence. These are evidentiary and stay in
  the data model.
- Which ladder rung happened to work, how many tool calls it took, what the blast radius was —
  **no.** These describe the search, not the finding. They belong here.

## Name variants

Real cases encountered: `Claudia Ordaz` / `Claudia Ordaz Perez`; `Cissy` / `Cecilia` Lizarraga;
`Melodie Selby` / `Melodie Williams` (name change mid-tenure); `Craig Stoker` / `Raymon C. Stoker`;
`Jon` / `John` Adams.

Store all observed forms. Never merge two people on surname alone — one city had a `Brent Hatch`
and a `Gentry Hatch` in adjacent cycles.

## Confidence

| Level | Criteria |
|---|---|
| `high` | Official election record or audit report naming the person for the specific cycle |
| `medium` | Single secondary source (news, trade press), or minutes roll call giving surname only |
| `low` | Inferred by continuity or elimination rather than a dated record naming them |

Continuity inference — "they held it in 2016 and 2024, so presumably 2020" — is `low`, always, and
must be flagged. It is the most common route to a confident-looking wrong answer.

## Reporting

Report:
- seat-years sourced / unrecoverable / not attempted
- cities below 70% coverage
- flagged cycles that terminated unrecovered, with blast radius
- count of `low` confidence rows

Do not claim the panel is verified. The method catches most errors, not all — expect 85-100%
seat-year yield in a typical state and ~50% in the worst.
