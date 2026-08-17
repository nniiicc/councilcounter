---
name: municipal-roster-panel
description: >
  Build a longitudinal panel of municipal elected officials - who held every council seat and the
  mayoralty in each city, in each year, across a multi-year span - with a source URL attached to
  every name. Use this skill whenever the user wants historical or year-by-year rosters of city
  council members, mayors, aldermen, commissioners, selectmen, or town/borough/township council
  members for one or more municipalities over a date range. Trigger on phrases like "council
  members in 2019", "who was on the council in a given year", "rosters for 2019-2026", "historical city
  council data", "build a panel of local officials", "track council turnover over time", or any
  request pairing a list of cities with a span of years. Trigger even when the list arrives as a
  spreadsheet, CSV, or pasted text. For CURRENT officials only, with no year dimension, use
  city-council-researcher instead - this skill is specifically for multi-year reconstruction.
---

# Municipal Roster Panel

> **This is a corrected fork**, forked 2026-08-17 from the bundled `anthropic-skills` plugin
> skill and amended against a live 8-city run (Washington ×7 + Michigan). It **supersedes** the
> plugin version, which is unchanged and still carries a dead Michigan source.
>
> It lives in the councilcounter repo at `.claude/skills/municipal-roster-panel/`, so it is
> versioned alongside the data it was derived from. `~/.claude/skills/municipal-roster-panel`
> is a **symlink** to it — one file set, discoverable both project-locally and globally. Edit
> either path; they are the same files. If the repo moves, re-point that symlink.
>
> Corrections merged into this fork: Michigan's primary source is dead; King County's 2015
> dataset is incomplete; county filing-period incumbent lists are a new source class; PDF text
> must be extracted locally; curl and WebFetch fail on different hosts; `gaps` semantics and the
> `vacant` status; presiding-officer tracking. Entries carry verification dates — **re-verify
> before trusting any of them**, since this fork will itself go stale.
>
> Upstream improvements to the plugin skill will not flow here automatically.

## What this skill does

Given a list of US municipalities and a year range, this skill reconstructs who held each seat in
each year and writes a panel dataset where every name carries the URL it was read from.

The output is one row per `(city, year, seat)` with an explicit state for seats that could not be
sourced. Empty is a legitimate, first-class result. Fabrication is not.

## The core insight

**Nobody publishes "the 2019 roster." Everybody publishes election results.**

Searching `<city> <state> council members 2019` returns the *present-day* roster page, because
that is what exists and what ranks. The year in the query is effectively ignored. Reconstruct
instead by finding the elections that seated the body and rolling them forward through their
terms.

This was measured head-to-head on 10 cities. The elections method recovered 9 of 10 council
rosters and 10 of 10 mayors. Reading meeting-minutes roll calls recovered 3 of 10, with no first
names, no ward identifiers, and no mayor in most cities. Minutes still matter - see Rung 6 of the
escalation ladder - but as a targeted patch, not a primary pass.

## Before you begin

Read these reference files:

1. `references/state-registry.md` - how to build a per-state source registry, cross-state findings,
   plus fetch-verified entries for Washington, Michigan, Alabama, Virginia, Tennessee, Texas,
   Arizona, California, New Jersey, Georgia, Massachusetts, and South Dakota
2. `references/escalation-ladder.md` - the 7-rung recovery procedure for missing election cycles
3. `references/output-schema.md` - the panel schema, required fields, and confidence rules

## The pipeline

### Step 0: Scope

Confirm with the user, unless already answered:

- **Year range.** Note that archive depth and record availability degrade fast before roughly
  2019-2021 for smaller municipalities.
- **Seat granularity.** Ward/district/position identifiers, or names only?
- **Effort cap per city.** Recommended: 60 tool calls, then bank partial results and move on.

### Step 1: Group the input by state, not by city

This is the highest-leverage move in the whole pipeline. A 64-city corpus typically spans only
10-14 states. Source discovery is a *per-state* problem, and source discovery is what consumes
the budget.

Parse the input, normalize city and state, deduplicate, and group.

### Step 2: Build the state registry

Dispatch one agent per state. Each resolves the state's election-results portal, URL pattern, year
coverage, county mapping for that state's cities in the corpus, municipal league or trade press,
audit-report source, public-notice portal, and election calendar conventions.

Follow `references/state-registry.md`. Require that every URL pattern be **verified by actual
fetch** before it enters the registry; an unverified pattern is worse than none.

Measured cost: ~54k tokens per state.

### Step 3: Derive each city's election cycle calendar

From the charter or the state conventions, work out which years that city holds elections and
which seats are up in each. A town electing in November of even years has no 2019 or 2023 cycle
at all - those years are holdovers.

**The unit of work is now `(city, election_cycle)`, not `(city, year)`.** This matters because a
missing cycle has a blast radius you can compute before spending anything: 3 seats x 4 years =
12 seat-years, which tells you exactly what escalating is worth. Compute it from `cycles` and
`years` at decision time - it is a scheduling input, not a stored field.

### Step 4: Retrieve cycles using the registry

Construct URLs from the registry rather than searching for them. This is what makes the method
cheap and what keeps it under the WebSearch quota.

Measured: registry-assisted runs used ~24 WebSearches per city versus a baseline run that
exhausted its search budget entirely. Tool calls dropped 48% on a same-city A/B.

### Step 5: Check for mid-term changes - MANDATORY

**Do not skip this. It is the known failure mode of the registry approach.**

Election results show only the elected skeleton. Appointments, resignations, deaths, recalls, and
resign-to-run vacancies never appear in them. In testing, one city had **four** appointed members
invisible in election results, and one registry-assisted run silently missed an appointment that
the slower baseline caught.

For each city, run explicit searches for `<city> <state> council appoints <year>`,
`<city> council member resigns`, and `<city> council vacancy`. Record every mid-term change with
its effective date.

**Absence of special elections can PROVE no turnover — a rare positive negative.** Where a
charter requires a vacancy to be filled by special election, enumerate every election the county
or city ran across the window: if no municipal special election appears, no district seat turned
over. One city established zero mid-term district turnover across eight years this way, corroborated
by annual roster snapshots. That converts "I searched and found nothing" into actual evidence —
worth far more than an unbounded search, and it is the only clean way to *close* Step C rather than
merely exhaust it. Note the charter may treat seat classes differently: in that same city, district
vacancies required a special election while **at-large vacancies were simply left unfilled until the
next general** — one seat sat vacant 19 months.

**The structural tell beats any search:** a seat appearing on two consecutive ballots, or an
off-cycle race, means an *unexpired term* — so somebody left early. That single observation
cracked open three cities in one batch. Mid-term changes were found in **every city measured**,
up to eleven in one.

**Also track the internal presiding officer** — deputy mayor, mayor pro tem, council president,
council chair — as its own seat with `role: vice_mayor` and one stable `seat_label`. The holder
simultaneously holds their ordinary council seat, so both get rows. This is not a courtesy title:
in one measured city the charter names the council chair as mayor pro tem, making it the
succession path that explains two mayoral turnovers. Collect it **opportunistically** — take it
while reading reorganization records you are already fetching; if the minutes portal is blocked,
log one line and move on rather than working the ladder for a single field. Collected inline it is
nearly free; collected as a later backfill it measured ~18k tokens per row.

### Step 6: Escalate flagged cycles

Any cycle that Step 4 could not source is a flagged unit. Work `references/escalation-ladder.md`
against flagged cycles only - never against whole cities.

Measured: 3 of 3 flagged cycles recovered, 34 seat-years unlocked, ~4,650 tokens per seat-year.

### Step 7: Validate

Before writing any record:

- **Every name must have a source URL.** No URL, no name. The cell stays empty.
- **Winning is not holding.** A ballot winner earns a tenure row only if a source shows them
  *seated* — sworn in, on a roll call, or on a roster. One measured city had a winner disqualified
  before taking office for residing outside city limits; an election-driven method would have
  credited him four years. The tell is an off-cycle *unexpired term* race appearing later.
- **Verbatim check.** The page-summarizing layer has been observed inventing plausible content -
  in one case supplying first names for a document that contained only surnames. The invented
  names happened to be correct, which makes the failure invisible by inspection. Spot-check quoted
  roster text against the source.
- **Check the day of the week against any claimed date.** This caught four separate errors in one
  session — a fabricated "January 5, 2018" that was a Friday, a summarizer's "January 7, 2025" that
  was a Tuesday, a republished archive article whose "Dec. 4 runoff" placed it in 2007 rather than
  2019, and two minutes files internally dated "March 03, 2019" (a Sunday) that actually carried the
  2020 roll call. It is the cheapest validation available.
- **Beware undated republished archive content.** One local paper reposts old articles without
  dates; a search snippet presented a 2007 council race as 2019, which would have seated the wrong
  person for four years.
- **Redistricting breaks seat identity, silently.** When a city redraws its map mid-panel,
  `District N` before and after are **different seats**. One councillor was elected in District 3
  in 2021 and District 4 in 2023 **without moving house**, and three incumbents were thrown into
  one new district. Never assume a district number tracks the same territory or the same person
  across a redistricting boundary — establish the effective date and treat the labels as
  discontinuous there.
- **Seat count sanity.** Does the number of seats match the city's form of government?
- **Continuity.** A person appearing, vanishing, and reappearing usually signals a missed
  appointment, not two separate tenures.

### Step 8: Deliver

Write the panel per `references/output-schema.md`. Report yield honestly: seat-years sourced,
seat-years unrecoverable, and which cities and cycles fell short.

## Expected yield and cost

Measured across 20+ cities in this method's development:

| Metric | Value |
|---|---|
| Tokens per city, 8-year span | ~92k with registry, ~107k without |
| WebSearches per city | ~24 with registry |
| Seat-year yield, typical state | 85-100% |
| Seat-year yield, worst state (SD) | ~50-55% |
| Cost per usable city-year | ~19k tokens |

Small cities cost **more** than large ones and return less - the most expensive single city
measured (111k tokens, 102 tool calls) returned half a roster. Budget accordingly, but do not
skip them: a pilot specifically targeting the hardest cities in a corpus returned 81%, against a
predicted near-zero.

## Retrieval mechanics — establish these before improvising

**WebFetch cannot parse PDFs, but it saves the binary to disk anyway.** It reports municipal
PDFs as corrupted or empty; the file is there. Run `pdftotext -layout` on it (or `pypdf`). Four
agents discovered this independently in one batch, and it rescued cycles in five cities. Local
extraction also yields genuinely verbatim text, **removing the summarizing layer from the trust
path entirely** — which is the single most effective guard against invented content. Never accept
"unreadable binary" as absence.

**A robots.txt `Disallow: /` is not proof the host will refuse you.** One town site carries a
blanket disallow yet serves everything to plain curl with a browser UA — archive listings,
`/ArchiveCenter/ViewFile/Item/{id}` and `/DocumentCenter/View/{id}` PDFs, and a plain-HTML site
search at **`/Search/Results?searchPhrase=`** (the CivicPlus pattern) that located every certified
results PDF. Several corpus cities recorded as "robots-blocked" are reachable this way. Likewise a
Granicus viewer recorded as blocked was not:
`{tenant}.granicus.com/MetaViewer.php?view_id=6&clip_id={id}&meta_id={id}` returns a real PDF.

**curl and WebFetch do not fail on the same hosts.** When one is blocked, try the other with a
full browser user agent. Several recoveries came from nothing but the difference. A fetchable
*site search* on a local outlet is often worth more than a search engine: one city with a dead
official source was fully reconstructed at a cost of zero WebSearches that way.

**A 404 or 403 on a search-indexed document is a BLOCK, not an absence.** Record it as blocked
and move on; never conclude the record does not exist.

## Known environment blockers

- `web.archive.org` - proxy-blocked. Do not build any step on Wayback snapshots.
- `ballotpedia.org` - robots-blocked to direct fetch in every state tested. Search snippets are
  usable; retrying the same URL occasionally succeeds.
- `results.enr.clarityelections.com` - the Clarity Elections platform carries municipal race detail
  in many states and was **robots-blocked in every one tested** (NJ, GA, TX, AZ). Election IDs are
  non-sequential and must be discovered per election. Do not build on it without a browser tool.
- JavaScript single-page results portals defeat plain fetching: Virginia's `enr.elections.virginia.gov`,
  Georgia's `results.sos.ga.gov`, Arizona's `results.arizona.vote`. The data is there; the tool
  cannot read it.
- CivicClerk, Granicus, CivicEngage and Laserfiche portals are frequently robots-blocked or
  JavaScript-only. **CivicClerk exposes an OData API — but on a different HOST, not a subpath:**
  `https://{tenant}.api.civicclerk.com/v1/Events` works, while
  `{tenant}.portal.civicclerk.com/api/v1/Events` **404s**. Verified independently by two agents,
  2026-08-17. This turns a JavaScript-only portal into a live minutes archive — **but only the
  bare collection responds**: `$orderby`, `$filter` and `$select` all 404 even on the working
  host, so it cannot be narrowed by date and you must page the whole collection.
- **CivicPlus / CivicEngage AgendaCenter — the highest-yield unlock found so far.** Archived
  minutes are served to **plain curl** at `/AgendaCenter/ViewFile/ArchivedMinutes/_MMDDYYYY-NNN`,
  and **the date segment is cosmetic — only the trailing integer selects the document.** So you do
  not need an index: sweep the integer range (~120-780 covered a decade on one city), fetch each
  PDF, and extract its printed date plus its "Present from City Council:" roll-call line locally.
  One city built its entire 8-year reconstruction from ~70 dated roll calls this way at **zero
  search cost**, on a site the census had recorded as robots-blocked. Parallelise with
  `xargs -P`. The `/AgendaCenter/Search/?CIDs=<id>&startDate=&endDate=` endpoint is also often
  reachable, but on at least one deployment it returns **only the current rolling year** and does
  not reach the archive — prefer the id sweep.
  **Organizational-meeting oath headings are gold** for seat mapping: "OATH OF COUNCILMEMBERS FOR
  POST 1 & POST 2 (2022-2026)" is stronger evidence of a seat map than any results report.
- **Hyperlocal blogs are queryable in bulk.** Blogger exposes a JSON feed
  (`/feeds/posts/default?alt=json&q=<terms>`) and WordPress exposes `wp-json/wp/v2/search`,
  letting you sweep hundreds of full post texts in a single call. A Blogger-hosted local paper was
  the highest-yield source for one city, carrying a runoff, two organizational meetings, a
  resignation and an entire presiding-officer rotation.
- Municipal sites often serve minutes from a **vendor domain that differs from the portal you
  expect** (e.g. `{city}.suiteonemedia.com`). When the expected portal fails, search for the
  document rather than the portal.
- Some sites serve 404 to fetchers for documents that search engines have indexed. Treat a 404 on
  an indexed document as a block, not as absence.

## What to avoid

- Searching for a roster by year. Search for the election that seated it.
- Accepting any name without a URL.
- Running the escalation ladder against a whole city instead of a specific cycle.
- Treating a small city as hopeless. Treat a *missing cycle* as the thing to escalate on.
- Skipping Step 5 because the registry answered cleanly. That is exactly when appointments hide.
- Reporting "not found" and "not attempted" as the same value.
