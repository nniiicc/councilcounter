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
> skill and amended continuously against a live run — **37 cities across WA, MI, AL, GA, TN, MA, VA
> and AZ** as of this revision, at 99.4% seat-year coverage. It **supersedes** the plugin version, which is unchanged and still carries a
> dead Michigan source and several wrong URLs.
>
> It lives in the councilcounter repo at `.claude/skills/municipal-roster-panel/`, so it is
> versioned alongside the data it was derived from. `~/.claude/skills/municipal-roster-panel`
> is a **symlink** to it — one file set, discoverable both project-locally and globally. Edit
> either path; they are the same files. If the repo moves, re-point that symlink.
>
> Merged into this fork so far: **eight "fetch-verified" registry entries that failed on contact**,
> including a county host now 403ing everything and a newspaper PDF pattern that never matched; unopposed candidates vanish from results in some states and not others; the ACFR
> "List of Principal Officials" is a near-universal roster source *with three failure modes*; county
> filing-period incumbent lists are a new source class; a working **OCR path** now exists; PDF text
> must be extracted locally; curl and WebFetch fail on **different, non-overlapping** hosts; a
> robots `Disallow: /` is not proof of refusal; the CivicPlus AgendaCenter id sweep; `gaps`
> semantics and the `vacant` status; presiding-officer tracking; and several validation techniques
> (day-of-week checks, stated-count completeness, absence-of-special-elections).
>
> Also added: an **orchestration** section (shared brief, propagating findings to in-flight agents,
> resuming rather than respawning) and **cost figures re-measured over 37 cities** — searches ran at
> 7.4 per city against the pilot's ~24, while tokens rose to ~150k.
>
> Entries carry verification dates — **re-verify before trusting any of them**, since this fork will
> itself go stale. One source verified early in the 37-city run had gone bot-walled by the end of it.
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

Measured over 37 production cities: **7.4 WebSearches per city**, against ~24 in the original pilot
and a baseline run that exhausted its search budget entirely. Portal APIs and constructed URLs — not
search — now carry most retrieval; several cities completed on 0-1 searches.

### Step 5: Check for mid-term changes - MANDATORY

**Do not skip this. It is the known failure mode of the registry approach.**

Election results show only the elected skeleton. Appointments, resignations, deaths, recalls, and
resign-to-run vacancies never appear in them. In testing, one city had **four** appointed members
invisible in election results, and one registry-assisted run silently missed an appointment that
the slower baseline caught.

For each city, run explicit searches for `<city> <state> council appoints <year>`,
`<city> council member resigns`, and `<city> council vacancy`. Record every mid-term change with
its effective date.

**A stated COUNT closes an enumeration.** When a source says how many of something there were —
"the fifth councillor out of the 13 to be appointed" — it converts your list from "everything I
happened to find" into a checkable set. One city's nine mid-term changes were confirmed complete
exactly this way. Actively look for such assertions in meeting coverage and anniversary pieces;
they are the cheapest completeness proof available, and they are what lets you stop searching with
justification rather than from exhaustion.

**Prove an absence with a POSITIVE CONTROL in the same dataset.** "The record does not contain X"
is only evidence if you show the dataset would have contained X had it existed. One agent established
that a city has no mayoral ballot line by finding **a neighbouring city's mayoral contest sitting in
the same id block** — same election, same index, same neighbourhood. Without that control the absence
is indistinguishable from an indexing gap. Whenever you are about to record a structural negative,
ask what the positive case would look like *in this same source* and go find one.

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
- **An ACFR's "Years of Service" column is unreliable** — one credited a member with 4 years when he
  had been seated for 2. The `Term Expires` column and the name/district pairing held across seven
  consecutive editions; the tenure arithmetic did not. Use the structural columns, not the derived one.
- **RESIGNING IS NOT LEAVING.** A resignation date and a vacancy date are different things, and
  conflating them is how a roster acquires phantom vacancies. Texas Const. art. XVI §65 makes a
  resign-to-run announcement an **automatic resignation**, while §17 keeps the incumbent in office
  **"until their successors shall be duly qualified"** — so an official can resign in October, keep
  chairing meetings, and hand over four months later. In one city this fired **five times** in an
  8-year panel and produced **no vacant seat-year at all**; a certified canvass even styled a
  resigned member "Incumbent" while she won the special for the seat she had resigned, and another
  canvass listed two districts as "vacancies" while their holders were still moving motions. Most
  states have an equivalent holdover provision. **Establish the holdover rule before recording any
  vacancy**, and date the handover from the successor's qualification, not the resignation.
- **Winning is not holding.** A ballot winner earns a tenure row only if a source shows them
  *seated* — sworn in, on a roll call, or on a roster. One measured city had a winner disqualified
  before taking office for residing outside city limits; an election-driven method would have
  credited him four years. The tell is an off-cycle *unexpired term* race appearing later.
- **Verbatim check.** The page-summarizing layer has been observed inventing plausible content -
  in one case supplying first names for a document that contained only surnames. The invented
  names happened to be correct, which makes the failure invisible by inspection. Spot-check quoted
  roster text against the source.
- **Roll-call arithmetic can rule a vacancy in or out without naming anyone.** "Called to order
  with ten members present, Councillor X absent" establishes **eleven seated members** — which
  proves a contested seat was filled even when no source names the appointee. Use it before filing
  `reason: "vacant"`: an unfilled seat and an unidentified holder are different findings, and the
  attendance line distinguishes them for free.
- **Check the day of the week against any claimed date.** This caught four separate errors in one
  session — a fabricated "January 5, 2018" that was a Friday, a summarizer's "January 7, 2025" that
  was a Tuesday, a republished archive article whose "Dec. 4 runoff" placed it in 2007 rather than
  2019, and two minutes files internally dated "March 03, 2019" (a Sunday) that actually carried the
  2020 roll call. It is the cheapest validation available.
- **Same-name cities in other countries fail SILENTLY, with real names and dates.** This has now hit
**three separate cities in one corpus** — Wikipedia's "Dublin City Council election" articles are
Dublin **Ireland**, "Bristol City Council election" is Bristol **England**, and
"Portsmouth City Council election" for 2018, 2019, 2021, 2022, 2023, 2024 and 2026 are all
**Portsmouth, England** — plausible, well-sourced, and completely wrong for Portsmouth, Virginia.
"Dublin City Council election" is Dublin, **Ireland**. Only the comma form ("Portsmouth, Virginia")
disambiguates. Scope every query by state, and check the country before using any encyclopaedic
source on a city whose name is shared with a British or Irish one.

**A hyperlocal outlet can CHANGE the town it covers.** One blog reprinted Alcester SD council roll
calls verbatim from 2019 through early 2024 — then switched entirely to **Spirit Lake, Iowa**, same
title format, different mayor and council. Reading the later posts as the original town would have
produced a wholly fabricated roster. **Re-confirm the municipality on every post, not just on the
outlet.**

**Beware undated republished archive content.** One local paper reposts old articles without
  dates; a search snippet presented a 2007 council race as 2019, which would have seated the wrong
  person for four years.
- **A document's URL path can lie about its vintage.** One city **overwrites its "ELECTED CITY
  OFFICIALS" PDF in place**, so `uploads/2020/01/ELECTED-CITY-OFFICIALS-1.pdf` actually carried the
  **2024-25** roster and `uploads/2024/06/…` carried the **2026** one. Dating a roster from its
  upload path would have seated the wrong council by several years. Always date a document from
  content printed *inside* it, never from its URL.
- **`pdftotext -layout` can reverse the reading order of rotated text.** On born-digital results
  PDFs with vertically printed candidate labels it inverted two wards' winners. Where a table has
  rotated headers, match columns to the TOTALS row by x-coordinate using `pdftotext -bbox` rather
  than trusting the linear text order.
- **A member can change SEATS without leaving office.** One councillor held an at-large seat
  2019-2024 and then won a *ward* seat in 2024 — two distinct tenure rows, which a continuity read
  would have merged into one. Another, defeated for one ward in 2022, ran for a different seat in
  2024 and lost; a ballot-appearance read would have re-seated him. **Agenda cover pages that print
  each member's ward** are what expose this.
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

## Running the batch — orchestration that was measured, not assumed

The pipeline above describes the work; this describes how to run it across many cities at once. All
of it comes from a 37-city production run.

**One shared brief file, not N hand-written prompts.** Put the method, validation rules, retrieval
techniques and output schema in a single file every agent reads, and keep per-city prompts to the
specifics — county, mayor-selection, known traps, census warnings. Hand-writing the common body into
each prompt guarantees drift between concurrent agents and silently propagates whatever was stale in
your head that day. **Update the shared file the moment a batch teaches something general**; that is
far cheaper than the alternative, which is 50 agents rediscovering it.

**⚠ The scratchpad is SHARED across concurrent agents — isolate working files.** One agent found
another city's downloads appearing inside a directory it had created itself. This is not hypothetical:
it produced a real incident where a locally cached minutes file OCR'd as **another city's council
minutes**, complete with a different mayor and a different municipal code citation, caught only because
that agent checked the city name inside the extracted text. **Instruct every agent to work in a
city-specific subdirectory with city-prefixed filenames**, and to confirm the municipality inside every
document — including ones it downloaded itself, since the collision risk is local as well as
cross-tenant.

**Propagate findings to in-flight siblings — this was decisive four times.** Agents in a batch finish
at very different times, and the first to finish often finds the thing that unlocks the rest. When one
reports a source, a trap or a correction that generalizes, **message the agents still running.**
Measured cases: one city's discovery that its state declares unopposed candidates elected without a
ballot reached four siblings, three of which reported back that they had explicitly checked and
cleared it — without that, the batch would have carried spurious gaps in cities with perfect records.
Another found a state audit mirror that a sibling then credited as the source that carried its entire
reconstruction. A third found the corrected API host for a portal three cities were about to write off.

**Resume a capped agent; do not respawn it.** An agent that stops at its tool-call cap with a specific
diagnosis is a *budget* stop, not an exhausted-sources stop — and its context is still loaded. One
city went from 7 gaps to 0 on a 15-call resume at **zero searches**, after the fresh-agent equivalent
would have cost a full research pass. Resume with a tight scope and an explicit budget.

**Decide the schema BEFORE dispatching.** Adding one field to already-researched cities measured
**~18k tokens per row**, and one city in three returned nothing for it. Collected inline during the
original pass it is nearly free. The same applies to enum values: two agents independently reached for
a value the schema did not have, and fixing that afterwards meant editing raw files and re-ingesting.

**Expect one dead registry entry per batch and budget for it.** Across five batches, eight
"fetch-verified" entries failed on contact — a county host that had begun 403ing everything, a
newspaper PDF pattern that never matched, two wrong URL paths, a hostname that used the city name
where the tenant slug was needed. This is the normal rate, not bad luck.

**Watch for the environment killing agents.** Long background agents die if the host sleeps. Check the
machine's power settings before a long batch rather than diagnosing it from three identical
mid-response failures.

## Expected yield and cost

Measured across 20+ cities in this method's development:

**Superseded by a 37-city production run (2026-08-17).** The figures below were measured across
WA, MI, AL, GA, TN, MA, VA and AZ — 8 states, 37 cities — and differ sharply from the original
pilot in both directions.

| Metric | Pilot estimate | **Measured over 37 cities** |
|---|---|---|
| WebSearches per city | ~24 | **7.4** (batch range 4.2-10.4; several cities ran 0-1) |
| Tokens per city | ~92k | **~150k**, rising batch over batch |
| Seat-year yield | 85-100% typical | **99.4%**; 31 of 37 cities at exactly 100% |
| Tool calls per city | ~57 | ~45, cap of 60 rarely binding |

**Searches fell as the technique library grew, while tokens ROSE** — agents now fetch and verify far
more per search (portal APIs, id sweeps, local PDF extraction, OCR) instead of asking a search engine.
Treat a city running hot on *searches* as a signal its registry entry is wrong; treat high *tokens*
with low searches as normal and healthy.

**Yield is far above the pilot's estimate because the failure modes were systematic, not random** —
dead registry entries, unopposed-candidate rules, and portals wrongly recorded as blocked. Each was
fixable once, for the whole corpus.

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

**A missing `-L` can make a live archive look dead.** One CivicPlus document series returned
**0 bytes** without `curl -L` and the full PDF with it — indistinguishable from an empty archive.
**Always follow redirects before concluding a document endpoint is broken**, and combine flags where
a host also has a bad certificate (`curl -kL`).

**Test the REDIRECT TARGET, not the recorded domain.** One survey row recorded a domain that is a
**108-byte meta-refresh shell** pointing at the real site; testing the recorded host said "blocked",
testing the target said 200-to-plain-curl with a full 2013-2026 archive. Before accepting any negative,
follow redirects (`curl -sIL`) and check where the host actually lands.

**A feasibility survey's NEGATIVE findings are unproven — re-test them.** An input census marked
eight corpus cities as having "no working archive"; the first one researched returned **HTTP 200 to
plain curl with a browser UA on the first try**, with robots disallowing only `/admin` and a few
utility paths — and its ACFR archive, which carried the whole reconstruction, was sitting on that
same domain. That city reached 100% with zero gaps. A survey records what one fetcher saw once.
Positive findings (a URL that worked) age well; **negative findings do not age at all** — they were
often wrong when written.

**A robots.txt `Disallow: /` is not proof the host will refuse you.** One town site carries a
blanket disallow yet serves everything to plain curl with a browser UA — archive listings,
`/ArchiveCenter/ViewFile/Item/{id}` and `/DocumentCenter/View/{id}` PDFs, and a plain-HTML site
search at **`/Search/Results?searchPhrase=`** (the CivicPlus pattern) that located every certified
results PDF. Several corpus cities recorded as "robots-blocked" are reachable this way. Likewise a
Granicus viewer recorded as blocked was not:
`{tenant}.granicus.com/MetaViewer.php?view_id=6&clip_id={id}&meta_id={id}` returns a real PDF.

**A browser USER AGENT alone is often not enough — send a full browser HEADER SET.** One city's
Akamai edge 403s curl *and* WebFetch even with a browser UA, including on `robots.txt`. Adding
`Accept`, `Accept-Language`, `Sec-Fetch-Dest/Mode/Site`, `Upgrade-Insecure-Requests` and a same-host
`Referer` returned **HTTP 200 on every static asset** under the site's `/files/sharedassets/…` tree,
unlocking canvasses, a candidate pamphlet and a whole ACFR series. HTML routes stayed 403 regardless
— so **construct asset URLs and never try to browse**. Try this before writing a host off.

**curl and WebFetch do not fail on the same hosts — and the asymmetry runs BOTH ways.** One
Massachusetts city served everything to curl though its robots.txt said otherwise; the other, in the
same batch, gave curl a blanket nginx **403 on all of `wp-json`** and on many `/wp-content/uploads/`
paths **while WebFetch fetched every one of them**, with no discernible pattern between which upload
folders 403'd and which did not. **Try both tools per file**, not merely per host. When one is blocked, try the other with a
full browser user agent. Several recoveries came from nothing but the difference. A fetchable
*site search* on a local outlet is often worth more than a search engine: one city with a dead
official source was fully reconstructed at a cost of zero WebSearches that way.

**Local-news bodies are often OBFUSCATED, not absent.** Three outlets in one corpus served article
text scrambled for non-subscribers while the page returned a clean 200 — two **ROT47** inside
`kAm…k^Am` wrappers, one **ROT13**. The lede is usually plain and the body decodes in a few lines.
One city's ACFR even stored two names ROT47-shifted **inside the PDF text layer**. If fetched text
looks like mojibake rather than a paywall notice, try decoding before concluding it is unreachable.

**A 404 or 403 on a search-indexed document is a BLOCK, not an absence.** Record it as blocked
and move on; never conclude the record does not exist.

## Known environment blockers

- **⚠ `web.archive.org` is NOT proxy-blocked and `/cdx` does NOT 404 — this was the FIRST source this
  project ruled out, and it was wrong (corrected 2026-08-17).**
  `http://web.archive.org/cdx/search/cdx?url={domain}&matchType=domain` returns **HTTP 200 and
  thousands of rows to plain curl** — one city got 8,000 rows including 1,529 archived PDFs and a
  complete 2019-2026 council-packet series, the exact files recorded as unreachable. Only
  `archive.org/wayback/available` misbehaves (persistent 429). **Use CDX directly.**
  **Wayback is often the COMPLIANT route into a robots-blocked site:** municipal robots.txt files
  frequently carry a blanket `Disallow: /` while **explicitly permitting `archive.org_bot` and
  `ia_archiver`**, so the archive's copy was collected with the site's consent.
  **Truncation trap:** some payloads are cut at an **exact power of two** (1,048,576 or 5,242,880
  bytes) while still indexing at HTTP 200 — `pdftotext` fails, `pypdf` dies on `Invalid object in
  /Pages`. A 1MB or 5MB Wayback payload is **truncated, not the document**.
- `ballotpedia.org` - robots-blocked to direct fetch in every state tested. Search snippets are
  usable; retrying the same URL occasionally succeeds.
- `results.enr.clarityelections.com` - the Clarity Elections platform carries municipal race detail
  in many states and was **robots-blocked in every one tested** (NJ, GA, TX, AZ). Election IDs are
  non-sequential and must be discovered per election. Do not build on it without a browser tool.
- JavaScript single-page results portals defeat plain fetching: Virginia's `enr.elections.virginia.gov`,
  Georgia's `results.sos.ga.gov`, Arizona's `results.arizona.vote`. The data is there; the tool
  cannot read it.
- **OnBase Public Access (OBPA) has an open JSON API — and a "Certificates of Election / Oaths of
  Office" query is the single best mid-term source found anywhere.** Read
  `/publicaccess/docs/searchq/obpa-config.json` for `api.url`, then:
  `GET /publicaccess/api/CustomQuery` (saved queries), `POST /publicaccess/api/Keywords`
  `{"QueryID":"…"}` — **which returns the complete VALUE DATASET for a keyword field**, i.e. the city's
  own exhaustive list of everyone who ever held office — and
  `POST /publicaccess/api/CustomQuery/KeywordSearch`, `POST /publicaccess/api/DocumentType/FullTextSearch`,
  `GET /publicaccess/api/Document/{urlencoded-docID}/`. The oaths query gives a **dated, per-person
  seating record including for unopposed seats that never appear on a ballot**. The keyword value
  dataset is a rare thing: it lets you *prove* an enumeration complete rather than merely exhaust it.
- **Legistar has a wide-open Web API — the cheapest mid-term check found so far.**
  `https://webapi.legistar.com/v1/{client}/officerecords` returns dated per-person, per-body
  membership rows (213 for one city), and `/matters` accepts OData `substringof()` filters, which
  surfaced every dated "Selection of Vice Mayor" and vacancy item. Caveats: `OfficeRecordTitle`
  often back-fills a person's *latest* title across their whole record; some members are missing
  entirely; some end-dates are wrong. **Only the records split by the main council body break at
  real title changes** — corroborate a boundary before trusting it.
- CivicClerk, Granicus, CivicEngage and Laserfiche portals are frequently robots-blocked or
  JavaScript-only. **CivicClerk exposes an OData API — but on a different HOST, not a subpath:**
  `https://{tenant}.api.civicclerk.com/v1/Events` works, while
  `{tenant}.portal.civicclerk.com/api/v1/Events` **404s**. Verified independently by two agents,
  2026-08-17. This turns a JavaScript-only portal into a live minutes archive — **but only the
  bare collection responds**: `$orderby`, `$filter` and `$select` all 404 even on the working
  host. **`$filter` and `$orderby` DO work on at least some tenants** (contrary to an earlier note) —
  only the page size is fixed at 15, paged with `$skip`. Test them before resigning yourself to paging
  the whole collection. Documents come from
  `/v1/Meetings/GetMeetingFileStream(fileId={id},plainText=false)` — **but this is deployment-dependent**:
  it returned real files on one tenant and **HTTP 200 with a zero-byte body on every id** for another,
  where the API was metadata-only. A zero-byte 200 is a dead endpoint, not an empty document.
- **CivicPlus / CivicEngage AgendaCenter — the highest-yield unlock found so far.** Archived
  minutes are served to **plain curl** at `/AgendaCenter/ViewFile/{KIND}/_MMDDYYYY-NNN`, and
  **the date segment is cosmetic — only the trailing integer selects the document.** `{KIND}` varies
  by deployment: `ArchivedMinutes` works on some, **`Minutes` on others where `ArchivedMinutes`
  404s** — try both before concluding the site is closed. Where the deployment supports it, the
  **dated search is better than sweeping**:
  `/AgendaCenter/Search/?term=&CIDs=<id>&startDate=<d>&endDate=<d>` returned plain HTML for *any*
  year on one city and handed over a complete 2018-2026 minutes archive at **zero search cost**
  (that city cost 1 WebSearch in total). On another deployment the same endpoint returned only the
  current rolling year — so test its reach before relying on it, and fall back to the id sweep. So you do
  not need an index: sweep the integer range (~120-780 covered a decade on one city), fetch each
  PDF, and extract its printed date plus its "Present from City Council:" roll-call line locally.
  One city built its entire 8-year reconstruction from ~70 dated roll calls this way at **zero
  search cost**, on a site the census had recorded as robots-blocked. Parallelise with
  `xargs -P`.
  **The Archive Center often beats the AgendaCenter, and needs no sweep at all:** `/2209/…` style
  paths 302 to `/Archive.aspx`, whose dropdown exposes `AMID` ids per document class (agendas,
  minutes, audits, newsletters), each listing `ADID`s that resolve directly at
  `/ArchiveCenter/ViewFile/Item/{ADID}`. **Also: "City Council Packet" items contain the PREVIOUS
  meetings' approved minutes** — that recovered four meetings absent from the minutes archive
  entirely, and is the fix for an archive with holes.
  **⚠ CivicPlus INTEGER ID SPACES ARE SHARED ACROSS TENANTS — a blind sweep can silently return
  ANOTHER CITY'S document.** Verified: one city's AgendaCenter Minutes id 1 returned a **City of
  Richmond Hill, Georgia** file, and its `sitemap.xml` returned an Akamai denial addressed to
  **www.tucsonaz.gov**. This is the single biggest risk in the id-sweep technique, and it fails
  *silently* — a well-formed minutes PDF from the wrong municipality looks exactly like a hit.
  **Confirm the city name inside the extracted text of every swept document before using it.**
 The `/AgendaCenter/Search/?CIDs=<id>&startDate=&endDate=` endpoint is also often
  reachable, but on at least one deployment it returns **only the current rolling year** and does
  not reach the archive — prefer the id sweep. **Critically, its `term=` parameter searches document
  TITLES only, not full text**, so it is useless as a mid-term-change probe; the separate CivicPlus
  site search **`/Search/Results?searchPhrase=` does hit full text** and is what surfaces
  ward-bearing agenda headers and appointment motions buried inside documents. Use the dated search
  to enumerate the archive, and `searchPhrase=` to search inside it.
  **Organizational-meeting oath headings are gold** for seat mapping: "OATH OF COUNCILMEMBERS FOR
  POST 1 & POST 2 (2022-2026)" is stronger evidence of a seat map than any results report.
- **WordPress.com-HOSTED outlets 404 on `wp-json`** (unlike self-hosted ones) — but the **public
  WordPress.com REST API works with no key**:
  `public-api.wordpress.com/rest/v1.1/sites/{host}/posts/?search=&after=&before=&number=100&fields=date,URL,title,content`.
  One call returned 125 full-content posts and carried an entire town on a single WebSearch.
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
