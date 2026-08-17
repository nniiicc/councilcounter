# Canonical Research Brief

The shared body of every per-city research agent prompt. Paste this in, then append a
**state registry block** (from the skill's `references/state-registry.md`, amended by
`registry-corrections.md`) and a **city block** naming the county, the mayor-selection
method, and any known traps.

Derived from the skill's method plus what batch 1 measured. Update it when a batch teaches
something general — that is cheaper than 56 agents rediscovering it.

---

## CORE METHOD

Nobody publishes "the 2019 roster." Everybody publishes election results. Searching
`<city> <state> council members 2019` returns the PRESENT-DAY roster page — the year is
effectively ignored. **Do not do it.** Find the elections that seated the body and roll them
forward through their terms.

**Step A — Cycle calendar.** Work out which years the city holds elections and which seats
are up in each. Reach back far enough that every term overlapping 2019 is covered. A town
electing in November of even years has no 2019 or 2023 cycle at all — those years are
holdovers, which is a structural fact, not a gap.

**Step B — Retrieve cycles by CONSTRUCTING URLs from the registry**, not by searching for
them. This is what keeps the job inside the search quota; batch 1 averaged 10 searches per
city because most cycles cost zero.

**Step C — MID-TERM CHECK. MANDATORY.** Do not skip it because the election record looked
clean — that is exactly when appointments hide. Election results show only the elected
skeleton; appointments, resignations, deaths, recalls and resign-to-run vacancies never
appear in them. Batch 1 found mid-term changes in **every single city**, up to eleven in one.
Run explicit searches for `<city> <state> council appoints <year>`, `<city> council member
resigns`, `<city> council vacancy`. Record every change with its effective date.

**The structural tell is worth more than any search:** an off-cycle race, or a seat appearing
on two consecutive ballots, means an *unexpired term* — which means somebody left early. That
single observation cracked open three cities in batch 1.

**Step D — Escalate any cycle you could not source, against THAT CYCLE, never the whole
city.** Ladder, in order:

1. State / county election portal, retrying alternate year-path formats
2. County clerk / registrar / auditor canvass PDF
3. **County filing-period incumbent lists and cities-and-towns rosters** — see below — plus
   municipal league, trade press, and the state audit agency
4. Local newspaper — highest-yield rung in practice; search the paper by name, pace retries
5. Statutory public notices (council proceedings name attendees; portals often default to a
   trailing 12-month window)
6. Minutes roll call — a meeting shortly after the seating date; establishes *composition*,
   then resolve identities against the election record. Minutes give surnames only, no wards,
   and no mayor in council-manager cities. **Search for the document, not the portal**
7. Budgets, ordinances with signature blocks, audit reports, board rosters

Stop as soon as the cycle is fully sourced.

---

## RETRIEVAL TECHNIQUES — established by batch 1, use before improvising

**WebFetch cannot parse PDFs, but it saves the binary to disk anyway.** It will report a
municipal PDF as corrupted or empty; the file is there. Run `pdftotext -layout` on it (or
`pypdf`). Four agents discovered this independently and it rescued cycles in five cities.
Local extraction also yields genuinely verbatim text, which removes the summarizer from the
trust path entirely. **Never accept "unreadable binary" as absence.**

**curl succeeds where WebFetch fails, and vice versa.** They do not fail on the same hosts.
When one is blocked, try the other with a full browser user agent before concluding the host
is closed. A fetchable *site search* on a local outlet (`?s=<query>`) is often worth more
than a search engine — one city ran on 5 searches that way with its official source dead.

**County filing-period incumbent lists are the best small-town source found so far.** County
election offices publish incumbent lists and cities-and-towns rosters as PDFs — these are
**not canvasses**. Their Remarks fields carry *appointment and resignation dates*, which is
precisely the mid-term data election results structurally cannot contain. Two-thirds of one
town's entire yield came from three such documents. Try these before the newspaper rungs.

**A 403 from a local paper is not the end.** Syndication mirrors of the same article
(yahoo.com and similar) often fetch cleanly when the origin blocks you.

**A 404 on a search-indexed document is a BLOCK, not an absence.** So is a 403. Record it as
blocked and move on; do not conclude the record does not exist.

---

## VALIDATION — before recording anything

- **No URL, no name.** The cell stays empty instead.
- **VERBATIM CHECK.** The page-summarizing layer invents plausible content. In batch 1 it
  fabricated an appointee who is a councilmember in a *different city*, invented vote totals
  twice, and misattributed a neighbouring town's clerk. It has also supplied first names for
  a document containing only surnames — and the invented names were **correct**, which makes
  the failure invisible by inspection. Re-source anything a summary asserts; prefer locally
  extracted text.
- **Seat count sanity.** Does the number of seats match the form of government? Council size
  is **not constant** across a panel — cities add, drop and redistrict seats mid-window.
- **Continuity.** A person appearing, vanishing and reappearing usually signals a missed
  appointment, not two separate tenures. Occasionally it is genuine — prove which.
- **Winning is not holding.** A ballot winner gets a tenure row **only if a source shows them
  seated** — sworn in, on a roll call, or on a roster. Batch 1 found a winner disqualified
  before taking office who would otherwise have been credited four years.
- **Never merge two people on surname alone.** One city had a Brent Hatch and a Gentry Hatch
  in adjacent cycles. Record every observed name form in `name_variants`; real cases include
  `Claudia Ordaz`/`Claudia Ordaz Perez`, `Cissy`/`Cecilia`, and a name change mid-tenure.
- **Mayor determination.** In council-manager cities the mayor is chosen **by the council from
  among its members** and never appears on a ballot. Election results alone will not give you
  the mayor, and getting this wrong produces a confident, complete-looking roster with the
  wrong person as mayor. Find the January reorganization meeting.

**Confidence:** `high` = official election record or audit report naming the person for that
specific cycle. `medium` = single secondary source (news, trade press), or minutes roll call
giving surname only. `low` = inferred by continuity or elimination rather than a dated record
naming them. Continuity inference — "they held it in 2016 and 2024, so presumably 2020" — is
**always `low`** and must be flagged. It is the most common route to a confident-looking
wrong answer.

---

## KNOWN DEAD — do not spend budget rediscovering

`web.archive.org` proxy-blocked (403); `archive.org/wayback/available` 429s, `/cdx` 404s.
`results.enr.clarityelections.com` robots-blocked in every state tested. JavaScript results
portals return nothing to a fetcher. `ballotpedia.org` is listed as robots-blocked to direct
fetch, **but fetched fine by curl in batch 1** — re-test rather than assuming.

**Registry entries can go dead.** Michigan was rated HIGH and "validated end-to-end"; its
county host now returns 403 to everything including `/robots.txt`. An entry records when it
was verified, not that it still works. Treat every entry as a lead to re-verify, and if the
primary source is gone, say so plainly and route around it rather than reporting the city as
unrecoverable.

---

## WHAT TO RECORD

Cover **every seat for every year 2019-2026**. A seat-year appearing in neither `tenures` nor
`gaps` is a hole in the deliverable. Where a seat changed hands mid-year, emit **two tenure
rows** — that is correct, not a duplicate.

**Track the internal presiding officer** — deputy mayor, mayor pro tem, council president,
council chair, whatever the city calls it — as its own seat with `role: "vice_mayor"` and one
**stable** `seat_label` across all years. The holder simultaneously holds their ordinary
council seat; both get rows. In council-selected-mayor cities this office carries real power,
and in several cities it is the charter path to acting mayor.

### `gaps` is not a notes field

It has exactly three legitimate uses, and only the first two are failures:

| Situation | Where it goes |
|---|---|
| Seat-year whose holder could not be sourced | `gaps`, with `reason` and a required `attempted` trail |
| Seat-year lawfully **vacant**, dated from a source | `gaps` with **`reason: "vacant"`** — a complete finding, not a failure; it does not count against coverage |
| A caveat about a seat-year that IS sourced (soft boundary date, ambiguous handover, scope note) | **NOT a gap.** The tenure's `confidence` already carries the uncertainty. Put the trail in `run_log` |

A caveat filed as a gap makes the panel emit two contradictory rows for one cell and
understates coverage. `ingest.py` detects and diverts these, but filing them correctly is
better. Never file a gap for a year outside 2019-2026.

---

## EFFORT CAP

**60 tool calls.** On reaching it, bank what you have and write the file — do not let the tail
run. An honest `unrecoverable` with a documented trail is a valid research output. A guessed
roster is not.

**Small cities cost MORE than large ones and return less.** The cheapest city in batch 1 was
its largest; the two most expensive were a town of 600 and a city whose official source was
dead. Do not treat a small city as hopeless, but do watch the cap.

---

## OUTPUT

Write `/Users/nmweber/Desktop/councilcounter/raw/{city_id}.json` **as you go** — once after
the cycle calendar, then after each phase — so an interruption costs minutes rather than the
whole city.

```json
{
  "city_id": 0, "city": "", "state": "",
  "profile": {"gov_form": "mayor-council|council-manager|commission|township", "seat_count": 0,
    "seat_scheme": "at-large|ward|position-numbered|mixed", "term_length": 4,
    "stagger_pattern": "which seats in which cycles", "mayor_selection": "elected|council-selected",
    "election_month": "", "profile_source_url": ""},
  "cycles": [{"election_date": "YYYY-MM-DD", "seats_up": 0,
    "status": "sourced|flagged|unrecoverable", "source_url": "url or null"}],
  "tenures": [{"person": "", "name_variants": [], "first_name_sourced": 1,
    "seat_label": "Ward 3|Position 5|District 2|At-Large|Mayor|<presiding officer title>",
    "role": "mayor|vice_mayor|council_member|alderman|commissioner|selectman",
    "start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD or null if ongoing",
    "entry_mode": "elected|appointed|succeeded|unknown",
    "exit_mode": "term_end|resigned|recalled|died|defeated|ongoing|unknown",
    "source_url": "REQUIRED",
    "retrieval_method": "state_portal|county_canvass|trade_press|audit_report|newspaper|public_notice|minutes_rollcall|municipal_league|other",
    "confidence": "high|medium|low", "election_date": "cycle that seated them, or null"}],
  "gaps": [{"year": 2019, "seat_label": "",
    "reason": "missing_cycle|robots_blocked|scanned_pdf|no_archive|homonym_unresolved|budget_cap|vacant|other",
    "attempted": "REQUIRED: what was tried and how it failed", "notes": ""}],
  "run_log": [{"step": "registry|cycle_calendar|cycle_retrieval|midterm_check|escalation|validation|export",
    "rung": null, "outcome": "success|blocked|not_found|budget_cap",
    "tool_calls": 0, "searches": 0, "detail": ""}],
  "totals": {"tool_calls": 0, "searches": 0}
}
```

**Final reply:** seat-years sourced / in gaps / known-vacant, count of low-confidence rows,
mid-term changes found and dated, any flagged cycle left unrecovered with its blast radius
(`seats_up × years to next cycle`), any contradiction left unresolved, any registry entry that
proved wrong or dead, and **your exact WebSearch count** — precise, not estimated.
