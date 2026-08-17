# Registry Corrections

Findings from live runs that correct or extend `municipal-roster-panel`'s
`references/state-registry.md`. The registry lives inside the skill and cannot be edited
from this project, so corrections accumulate here and should be folded into agent
prompts for subsequent batches.

Each entry records how it was established, because an unverified correction is worse
than none.

---

## Cross-state — applies to every batch

### WebFetch cannot parse PDFs, but the binary is still on disk

**Discovered independently by four agents in batch 1.** WebFetch reports municipal PDFs
as "corrupted binary" or refuses to parse them, but it has already saved the file
locally. Extracting the text directly recovers the content:

```bash
pdftotext -layout <cached-pdf> -
```

`pypdf` works equally well. This matters beyond convenience: local extraction yields
genuinely verbatim text, which **eliminates the invented-content risk** that the
summarizing layer introduces. Four separate cycles in batch 1 were recovered this way
and would otherwise have been recorded as unrecoverable — Federal Way 2015, Lacey's two
roster newsletters, and Bothell's AgendaCenter minutes.

This partially addresses the "no OCR path" open item: it is not OCR, and it does nothing
for image-scanned PDFs, but a large share of documents that *look* unreadable are in fact
text PDFs that WebFetch simply declined.

### Winning an election is not the same as holding the seat

**College Place, Position 1, 2021.** John C. Haid won the race outright and appears as the
winner in the official county results — then was **disqualified before taking office**, no
longer residing inside city limits. He never served a day. The seat sat vacant 1–24 January
2022 until Paul Jessup was appointed.

An election-results-driven method will record him as the seat-holder for four years unless
something checks. The check that catches it is the same one that catches everything else in
this pipeline: an off-cycle race for an *unexpired term* appearing where none should exist.
**A winner gets a tenure row only if a source shows them seated** — swearing-in, a roll
call, or a roster.

### A gap row is not a notes field

Agents repeatedly filed three distinct things under `gaps`: genuine unsourced seat-years,
date-precision caveats on seat-years that *are* sourced, and scope notes about titles that
are not elected seats. Only the first belongs there — `gaps` maps to `unrecoverable` in the
`panel` view, so the other two emit a contradictory second row for a cell that already has
a sourced tenure, and depress coverage. `ingest.py` now detects and diverts them to
`run_log`, including composite labels like `"Mayor / Deputy Mayor"`.

**The schema cannot express a genuinely vacant seat.** A seat that was lawfully empty for
part of a year is not "unrecoverable" — we know precisely that nobody held it — but `gaps`
is the only place to put it and `panel` will label it unrecoverable. Batch 1 hit this six
times (Oak Harbor ×4, Federal Way ×2, Bothell ×1). Currently diverted to `run_log`, which
preserves the trail but loses the structure.

---

## Washington

### King County's 2015 results dataset is incomplete — NOT a statewide problem

`https://results.vote.wa.gov/results/20151103/King/` returns **HTTP 200** but carries only
Auburn, Bothell, Milton and Pacific — the four cities that straddle a county line.
Federal Way and Seattle are genuinely absent from it, and the linked county export CSV
omits them too. There is no pagination or filter to miss.

**Confirmed independently by two agents**, each of which inventoried the page's links
before concluding absence. Both recovered the cycle from the **King County certified final
canvass PDF** (Rung 2) plus local text extraction.

**A clean 200 from this host is not evidence a city is absent.** Any King County city
needing a 2015 cycle should skip straight to the canvass PDF.

This does **not** generalize to Washington as a whole: Thurston (Lacey), Island (Oak
Harbor) and Walla Walla (College Place) all returned 2015 municipal races cleanly. Do not
propagate it as a statewide caveat.

### County filing-period incumbent lists — a new source class, and the best one for tiny towns

**The single highest-yield discovery of batch 1.** County election offices publish
*filing-period incumbent lists* and *cities-and-towns rosters* as PDFs — these are **not
canvasses**, and they are not what Rung 2 tells you to look for. Their Remarks fields carry
**appointment and resignation dates**, which is exactly the mid-term data election results
structurally cannot contain.

Verified on Lewis County (`lewiscountywa.gov/.../documents/{id}`), which supplied Vader's
roster verbatim:

```
Kenneth Smith - Elected 2015, Resigned 4/25/2019
Lois Wilson   - Appointed 5/9/2019
Judy Costello - elected 2017, resigned 3/21/19
Randal Hall   - appointed 4/11/19
```

Roughly two-thirds of Vader's total yield came from three such documents. **Try these before
the escalation ladder's newspaper rungs in any small municipality**, and check whether other
counties in the corpus publish the same class of document.

### Washington's State Auditor does NOT name officials — the cross-state claim is state-specific

The registry's cross-state finding calls audit reports "the most underrated source," verified
for Alabama and South Dakota. **It does not hold in Washington.** Vader's SAO reports are
addressed generically to "Mayor and City Council" and contain no governing-body roster; they
were useful only for a structural profile line. Do not spend Rung 3 budget on WA audit
reports expecting a roster.

### CivicEngage AgendaCenter — the Search endpoint is reachable when browse URLs are not

Year-filtered AgendaCenter browse URLs are robots-blocked on several corpus cities, but the
**Search endpoint is reachable by curl**:

```
/AgendaCenter/Search/?CIDs=<committee-id>&startDate=<date>&endDate=<date>
```

It enumerates `ViewFile/Minutes/_MMDDYYYY-NNN` document ids directly, which can then be
fetched and text-extracted. Verified on Oak Harbor, where it opened a minutes archive the
original run had recorded as blocked. Worth trying on every CivicEngage city in the corpus
before accepting the portal as dead — the census marks several this way.

Note the archive may genuinely start later than the panel window: Oak Harbor's minutes begin
January 2021, and the Search endpoint returns zero records for 2020. That is a real absence,
distinct from the robots block.

### A 403 from a local paper is not the end — try syndication mirrors

*The Chronicle* (chronline.com) returned HTTP 403 on all five direct fetch attempts, but
**yahoo.com syndication mirrors of the same articles fetched cleanly** and supplied Vader's
2025-2026 mid-term changes. Worth one attempt wherever Rung 4 is blocked.

### bothellwa.gov is NOT blocked — the input census is wrong here

The feasibility census recorded Bothell's CivicPlus robots.txt as unreachable and its
AgendaCenter as not fetchable. In practice DocumentCenter PDFs, AgendaCenter
agendas/minutes and CivicAlerts news items all returned 200. This makes the city portal a
**live Rung 6** rather than a dead one, and suggests other Washington CivicEngage cities in
the census may be mislabelled the same way.

### The multi-county summation rule is load-bearing, not a footnote

Bothell spans King and Snohomish, and summing both counties **changed the winner in three
of six cycles**:

| Race | King only | Combined (correct) |
|---|---|---|
| 2019 Pos. 2 | Henderson 3,645 | **Thompson 5,807 – Henderson 5,802** |
| 2021 Pos. 1 | Tran 3,689 | **Zornes 6,066 – Tran 5,554** |
| 2021 Pos. 5 | Kuehn 3,518 | **Mahnkey 5,921 – Kuehn 5,625** |

The 2019 margin is **five votes**. Mason Thompson, who went on to be mayor, would have been
dropped from the panel entirely by a single-county read. All three combined-vote winners
were independently confirmed in office by city documents, so this is verified, not merely
arithmetic.

---

## Michigan — the registry's primary source is DEAD

The registry rates Michigan **HIGH, "validated end-to-end"** against a complete Dearborn
Heights roster for 2019 and 2023. **That path no longer works.**

`www.waynecountymi.gov` returns **HTTP 403 to everything** — the hub page, the
`/2016-2020-Elections` and `/2021-2024-Elections` subpaths, the `/files/assets/mainsite/…`
PDF asset directory, the site root, and even `/robots.txt` — via both WebFetch *and* curl
with a full browser user agent, Accept and Referer. This is a **blanket WAF block, not a
robots directive**, so it cannot be worked around by respecting or re-reading robots.
`waynecounty.com` 302s into the same host. `michigan.totalvote.com/Wayne` serves only the
current election. `mielections.us` did not respond at all (TCP timeout).

**No cycle was recoverable from any official Michigan source.** Every Dearborn Heights
election row is `medium` confidence off local news, not `high` off a canvass.

The lesson generalizes beyond Michigan: **a registry entry verified at some past date can
go dead**, and "validated end-to-end" is a claim about when it was checked, not a
guarantee. Entries should be treated as leads to re-verify, not as facts.

### What worked instead — curl succeeds where WebFetch fails

- **`arabamericannews.com` is fully fetchable by curl, including its site search**
  (`?s=<query>`), which returns dated permalinks. This let the agent enumerate cycles and
  appointment votes **almost entirely without WebSearch** — 5 searches for the whole city.
  A fetchable site search on a local outlet is worth more than the search engine.
- **`patch.com` and `ballotpedia.org` also fetched fine by curl.** The registry's
  cross-state claim that Ballotpedia is robots-blocked in every state tested **may be
  stale** — worth re-testing before writing it off in later batches.

**Try curl before concluding a host is blocked.** WebFetch and curl do not fail on the same
set of hosts, and several batch-1 recoveries came from the difference.

---

## Fabrication: caught three times in five cities

The invented-content failure mode is not rare and is not theoretical.

- **Oak Harbor** — a summary asserted "Alison Perera was appointed to the Position 4 seat,"
  ahead of "David Ford with 61%." The official canvass shows **Armes 1,982 v. Chaszar
  1,790**. Neither named person exists in Oak Harbor's record; Perera is a Port Angeles
  councilmember. A second summary gave fabricated vote totals for the same race.
- **Seattle** — a snippet placed Teresa Mosqueda's vacated seat at "citywide Position 9."
  The state portal shows she won **Position 8** in both 2017 and 2021, with Nelson holding
  Position 9. Recording it would have put two people in one seat.

All three were caught by re-sourcing against the official record. **Every one would have
been invisible on inspection** — the invented material was plausible, internally
consistent, and in one documented case even correct. Spot-checking quoted roster text is
not optional.

---

## The presiding officer can be the charter succession path

Dearborn Heights' city charter names the **Council Chair** specifically as mayor pro tem in
the event of a mayoral vacancy. That is how Denise Malinowski-Maxwell became interim mayor
when Daniel Paletko died (2020-12-29) and how Mo Baydoun became acting mayor when Bill Bazzi
resigned (2025-10-08) — both kept their council seats throughout.

**This resolved a contradiction batch 1 had left open.** Two sources disagreed on whether
Baydoun was elevated by charter succession or by a council appointment vote. Three
independent statements of the charter mechanism outweigh the single January 2026 line saying
he was "appointed by the City Council in October"; that wording is an error. Recorded as
`entry_mode: "succeeded"`.

Where a charter works this way, the presiding officer is not an internal courtesy title — it
determines who runs the city when the mayoralty empties, and omitting it makes the mayoral
succession look unexplained.

**A new contradiction was opened and left visible rather than smoothed over:** a Feb 2025
profile says Baydoun was "elected City Council president in September 2023, succeeding Ray
Muscat," which is incompatible with Dave Abdallah being directly sourced as chair in both
August and November 2023. Best reading is that Baydoun became chair *pro tem* in Sept 2023
and the profile conflated the two offices. His chair span therefore starts 2024-01-01 with
`entry_mode: "unknown"`.

---

## Backfill economics — decide the schema BEFORE dispatching

Adding the presiding officer to six already-researched cities cost **~18k tokens per row**,
and one city in three returned nothing at all. A narrow task still pays an agent's full fixed
cost: bootstrap, source discovery, verification.

The split is predictable. **The backfill succeeds where the city publishes reorganization
actions on the open web** (Seattle, Federal Way, Dearborn Heights) **and fails where the
minutes portal is blocked** (College Place: BoardDocs 403 plus a rate-limited paper). It is
not a function of city size — Dearborn Heights cost 0 searches because its local outlet has a
fetchable site search.

Two rules follow:

1. **Settle the schema before dispatching a batch.** Collected inline, this field costs
   essentially nothing; collected afterwards it costs a second agent per city.
2. **Collect it opportunistically, not exhaustively.** Where the reorganization record is
   reachable, take it. Where the portal is blocked, write one `run_log` line and move on —
   do not work the escalation ladder for a single field.

**Never file gap rows for a seat whose existence is unsourced.** The College Place backfill
left eight gap rows for a "Mayor Pro Tem" it could not confirm the city even designates,
which would have invented a phantom seat and eight unrecoverable seat-years. If the office
cannot be established, that is a `run_log` note, not a column of failures.

---

## Corpus consistency — resolved

**Is the internal presiding-officer title a tracked seat?** Batch 1 split on this:

- **Bothell and Lacey** recorded Deputy Mayor as its own tenure rows (8 seat-years each)
- **Seattle, Oak Harbor and Federal Way** did not; Federal Way explicitly declined, noting
  it is not a separate elected seat

The schema's `role` enum includes `vice_mayor`, so there is a slot for it. This inflates
some cities' seat-year counts relative to others and should be settled before the panel is
compared across cities.
