# Handoff — Municipal Roster Panel, 64 cities, 2019–2026

Prepared at the end of a long design/piloting session. Read this first, then invoke the
`municipal-roster-panel` skill **by name** — do not rely on it auto-triggering.

**The method lives in the skill, not here.** The pipeline, the 12-state source registry, the
escalation ladder and the schema documentation are all in `municipal-roster-panel`. This document
carries only what the skill cannot: decisions made in conversation, measured baselines, open
items, and the things already ruled out.

---

## 1. Do these before any research

1. **Verify the device bridge with a real round trip.** Write a file to
   `/Users/nmweber/Desktop/councilcounter`, read it back, confirm the bytes match. Listing the
   directory only proves read access; the checkpoint needs writes.
   **As of this handoff the bridge was DOWN** — `device_list_dir` returned "The device this session
   is bound to is not connected to the bridge" on three attempts spanning several minutes. If it is
   still down, fall back to handing the `.db` back as a file each session and re-attaching it.
2. **Create the database** from `schema.sql` (attached, tested). It is empty and ready.
3. **Load the city list** from the census workbook (attached), not the user's original spreadsheet —
   see §3.
4. **Confirm the search budget behaviour** on the first batch (see §5, open item 6).

---

## 2. Decisions already made — do not re-litigate

| Decision | Value |
|---|---|
| Year range | **2019–2026**, with 2026 meaning "as of now." Today is August 2026; the November 2026 elections have not happened. Seats up in Nov 2026 stay with their current holders. |
| Effort cap | **60 tool calls per city**, then bank partial results and move on. Do not let the tail run. |
| Primary deliverable | **SQLite `.db`**. Produce an xlsx of the `panel` view only if asked. |
| Low-confidence rows | **Include and flag.** Do not exclude. |
| Provenance | **Every row.** `tenures.source_url` and `gaps.attempted` are `NOT NULL` — enforced at the schema level, verified by test. |
| Process metadata | Lives in `run_log` only. It was deliberately removed from `cycles` — ladder rung and blast radius describe the search, not the world. Blast radius is computed by the `cycle_cost` view. |
| Seat granularity | Ward / district / position identifiers wherever available. |

---

## 3. Input artifacts

**`City_Council_2019-2026_Feasibility_Census.xlsx`** — this is the canonical input, not the user's
original file. All 64 cities audited by live fetch. It contains:

- **40 corrected URLs.** The originals were stale, robots-blocked, or pointed at the wrong domain.
- **8 cities with no working archive found**: Franklin Twp NJ, Hartford SD, Howell Twp NJ,
  New Brunswick NJ, Odessa TX, Poquoson VA, Ripon CA, Shenandoah TX.
- **Two identity corrections**, both confirmed:
  - "Richmond city, Georgia" is **Richmond Hill, Bryan County** — no such incorporated city as
    "Richmond, GA" exists (Richmond County is consolidated Augusta).
  - "Franklin township, New Jersey" is **Gloucester County** — cross-confirmed against the NJ DCA
    mayors dataset (mayor John "Jake" Bruno). NJ has four Franklin Townships; the user should
    sanity-check this call.

**`schema.sql`** — runnable DDL. Creates 7 tables, 3 views, seeds `years` 2019–2026. Tested:
the `panel` view explodes spans correctly, unions gaps in, and both provenance constraints reject
rows that lack a source.

---

## 4. Measured baselines — use these to detect drift

From ~25 cities of piloting. If the run diverges sharply from these, something is wrong.

| Metric | Value |
|---|---|
| Tokens per city, 8-year span, **with** state registry | ~92k |
| Tokens per city **without** registry | ~107k |
| Tool calls per city with registry | ~57 |
| **WebSearches per city** | **~24** |
| Search cap | **200 per session** (see open item 6) |
| Expected seat-year yield, typical state | 85–100% |
| Expected yield, South Dakota | ~50–55% |
| Whole job | ~7.9M tokens, 9–11 sessions |

**Counter-intuitive but measured: small cities cost MORE than large ones and return less.**
El Paso (pop 680k) was the cheapest city in any pilot at 84k tokens with a perfect record;
Hartford SD (pop 3.3k) was the most expensive at 112k tokens and 102 tool calls for half a roster.
Budget accordingly — but do not skip them. A pilot deliberately targeting the *hardest* cities in
the corpus returned **81%**, against a predicted near-zero.

**A/B evidence for the registry**: Bothell, same city, same 8 years — 126,699 tokens and 122 tool
calls without it, 94,484 tokens and 63 calls with it. Identical 8/8 result. The baseline run
exhausted its search quota; the registry run used 27 searches.

---

## 5. Open items

> **STATUS AS OF 2026-08-17 — the run is complete (64/64 cities, 99.2%). Items 1-4 and 6 are
> RESOLVED; the resolutions are recorded below inline and in `registry-corrections.md` /
> the forked skill. Item 5 was never a task, only a warning, and it held.**
>
> 1. **RESOLVED — and neither hypothesis was right.** The El Paso minutes were live *and* the
>    resignation date was correct: **resignation is not vacancy.** Tex. Const. art. XVI §65 makes a
>    resign-to-run announcement an automatic resignation while §17 keeps the incumbent in office
>    "until their successors shall be duly qualified". Ordaz was chairing business on 17 Dec 2019.
>    This fired five times in El Paso alone and produced no vacant seat-year.
> 2. **RESOLVED per city, without the pre-pass.** Each agent settled its own calendar in Step A —
>    the pre-pass was unnecessary. TX: all seven differ, terms of 2/3/4 years, three cities voting
>    annually. AZ: mayor directly elected in six of seven, council-selected only in Sahuarita.
>    Ojai: **Measure L's defeat PRESERVED direct election** (it proposed abolishing it).
>    Greenfield: 4-year terms with half the council up every 2 years — the wording was never
>    contradictory. Alabama: 3 of 5 cities affected by the 2021 Act.
> 3. **RESOLVED — an OCR path now exists and works.** `pdftoppm -r 300 -png` + `tesseract --psm 4
>    -c preserve_interword_spaces=1`. It recovered five otherwise-lost cycles including an entire
>    county's run of summary PDFs. Watch orientation (some scans need 180° rotation, others are
>    destroyed by it) and glob `{prefix}-*.png`, not `-001`.
> 4. **RESOLVED — the ~50% South Dakota ceiling was not real.** Hartford's robots.txt is a genuine
>    blanket Disallow and was honoured, but it contains **no year-scoped rule**; the 2019/2020-vs-
>    2021/2023 asymmetry was tooling noise. The same file explicitly permits `archive.org_bot`, so
>    Wayback is the *compliant* route — and Wayback's CDX API, this project's first-listed dead
>    source, returns 8,000 rows to plain curl. **South Dakota finished at 98.1%, not 50-55%.**
> 6. **RESOLVED by measurement.** No cap was ever hit. The full run averaged **~7 searches per
>    city** against the ~24 predicted, because portal APIs and constructed URLs replaced search
>    almost entirely; several cities finished on 0-2 searches.
>
> **Two foundational "dead sources" in §6 below were also wrong:** Clarity Elections serves
> `robots.txt` as **HTTP 404** (no Disallow ever existed) and its JSON API is open; Wayback CDX
> works. Both had been ruled out before the run began. See `registry-corrections.md`.

### Original open items, as written at handoff

1. **El Paso, District 6, December 2019 — unresolved contradiction.** The elections arm has the
   seat vacant (Claudia Ordaz resigned ~Oct–Nov 2019 to run for the Texas House; successor Claudia
   Lizette Rodriguez seated Jan 2020). The minutes arm read the Dec 17 2019 council minutes and
   recorded "Claudia Ordaz Perez" as seated. Both cannot be true. Likely explanations: the minutes
   carry a stale member header rather than a live attendance roll, or the resignation date is wrong.
   **Resolve this first** — it is the only known contradiction in everything produced, and it is the
   test case for how arms should reconcile.

2. **Registry gaps to pre-resolve in one cheap pass (~150k tokens).** Each will otherwise be
   rediscovered per-city, repeatedly, across sessions:
   - **Texas** — election dates, term lengths and stagger for Castle Hills, Mission, Odessa,
     Victoria. Only El Paso is confirmed (November even years since 2018, 4-year terms).
   - **Arizona** — council size, term, stagger and mayor-selection for Show Low, Page, Cottonwood,
     Chino Valley. Official-site paths 404'd during registry building.
   - **California** — Ojai's mayor-selection method after Measure L (2022). Unresolved whether the
     mayor became directly elected or stayed council-selected.
   - **Massachusetts** — Greenfield's council election cadence. The city's own wording ("four-year
     terms… elected biannually") is internally ambiguous.
   - **Alabama** — whether Fairhope, Homewood and Selma shifted from an August 2024 to an
     August 2025 election under the 2021 Act (which extended the prior term to five years).
     Mobile is confirmed exempt; Auburn is confirmed unaffected.

3. **No OCR path.** Tucson's 2019 minutes and all 45 of Yuba City's 2019 minutes PDFs are image
   scans with no extractable text. If a flagged cycle for those cities reaches Rung 6, the ladder
   terminates. Needs building if it comes up.

4. **South Dakota crawl policy — the user has not answered.** Hartford's 2019 and 2020 council
   packets are public documents fenced by a robots directive; its 2021 and 2023 packets fetch fine.
   This caps SD at ~50% and affects 6 cities. **Default to respecting robots.txt** unless the user
   says otherwise. Do not decide this unilaterally.

5. **Massachusetts — Amherst before December 2018 is a category error**, not a data gap. The town
   had no Town Council; it had open Town Meeting plus a 5-member Select Board. The 13-member
   council was created by a charter adopted March 2018, first elected Nov 2018. If the panel is
   ever extended earlier, do not map "council seat" backwards.

6. **The 200-search cap may be per-session or per-agent — unknown.** Subagents reported it as
   "200/session." If it is genuinely per-session across all concurrent agents, batches are ~5 cities.
   If per-agent, throughput is far higher and the session count drops. **Measure this on batch one
   before planning the rest of the run.**

---

## 6. Do not rediscover these

All confirmed dead in this session. The state registry in the skill has the full detail; these are
the ones that cost the most time.

- **`web.archive.org` — proxy-blocked (403).** Do not build any step on Wayback. Its APIs are also
  unreachable: `archive.org/wayback/available` returns persistent 429, `archive.org/cdx` 404s, and
  the Memento aggregator fails robots.
- **`ballotpedia.org` — robots-blocked to direct fetch in every state tested.** Search snippets
  only; retrying occasionally succeeds.
- **`results.enr.clarityelections.com` — robots-blocked in every state tested** (NJ, GA, TX, AZ).
  It carries the richest municipal data of anything found. Election IDs are non-sequential.
- **JavaScript results portals return nothing**: `enr.elections.virginia.gov`,
  `results.sos.ga.gov`, `results.arizona.vote`.
- **Massachusetts `electionstats.state.ma.us` contains zero municipal races** — despite the
  Secretary of State's own guidance pointing there.
- **Virginia's `results.elections.virginia.gov` serves only `2022 November General`.** Thirteen
  election folders spanning 2014–2025 were tested; everything else 404s, before and after. It is an
  orphaned migration snapshot, not a range.
- **Virginia towns have no standalone locality page.** Tazewell's races are nested inside
  `TAZEWELL_COUNTY`. Look up towns by their containing county or you will conclude the record is
  missing.
- **`{city}.suiteonemedia.com` is Show-Low-specific**, not an Arizona pattern. Confirmed 404 for
  Cottonwood, Page, Sahuarita.
- **Searching for a roster by year does not work.** `<city> <state> council members 2019` returns
  the present-day roster page in every case tested. Search for the *election* that seated the body.

---

## 7. Session protocol

- **Batch by state, not alphabetically.** The registry is per-state, so grouping keeps the relevant
  entry in context and avoids reloading.
- **Write to the `.db` continuously**, not at the end. A session that dies mid-batch should lose
  minutes of work, not hours.
- **Log every step to `run_log`** including failures. "Where did I stop" must be a query, not a
  reconstruction.
- **Do not skip the mid-term appointment check** (skill Step 5). It is the known failure mode of the
  registry approach: a registry-assisted run silently missed a Bothell appointment that the slower
  baseline caught, and Oak Harbor had **four** appointed members invisible in election results.
  Dearborn Heights had two mayoral successions in the window, neither in any election record.
- **Watch for summarizer fabrication.** The page-fetching layer was observed inventing first names
  for a document containing only surnames — and the invented names were *correct*, which makes the
  failure invisible by inspection. Spot-check quoted roster text against source.
- **At session end**, report: seat-years sourced / unrecoverable / not attempted, cities below 70%,
  flagged cycles still unrecovered with their `cycle_cost`, and count of `low` confidence rows.

---

## 8. Corpus at a glance

64 cities, 12 states: California 7, New Jersey 7, Washington 7, Texas 7, Arizona 7,
South Dakota 6, Virginia 6, Alabama 5, Tennessee 5, Massachusetts 3, Georgia 3, Michigan 1.

All 12 have fetch-verified registry entries in the skill. Highest confidence: Washington and
Michigan (both validated end-to-end against known rosters). Hardest: South Dakota.
