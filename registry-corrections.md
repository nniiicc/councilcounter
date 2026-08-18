# Registry Corrections

Findings from live runs that correct or extend `municipal-roster-panel`.

**Status: merged upstream (2026-08-17).** Every finding here has been folded into a
user-level fork of the skill at `~/.claude/skills/municipal-roster-panel/`, which supersedes
the bundled plugin version and is the operational source of truth for future runs **in any
project**. **This file is the audit trail** — the evidence, measurements and reasoning behind
each correction, which the skill states only as bare instructions.

New findings must be recorded here **and** merged into the fork. Two documents that disagree
are worse than one that is merely incomplete.

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


---

# Batch 2 — Alabama, Georgia (in progress)

## The unopposed-seat trap — the highest-value finding so far

**Alabama declares sole qualified candidates elected without a ballot**, so unopposed seats
never appear in election results at all. Auburn's 2022 archive is missing **4 of its 9 seats**
for this reason — the mayor and three wards. Its 2018 archive omits one.

Reading those omissions as missing data would have produced four spurious gaps in a city that
actually has a perfect record. The certification of an unopposed seat is often published
**weeks apart** from the contested results as a separate notice — Auburn's Ward 4 was certified
a month after the others, which was itself the tell that the seat had been vacated and
re-qualified.

**This is a legal provision, not an Alabama quirk**, and several states have equivalents. It is
now a cross-state finding in the fork: establish what a state does with unopposed candidates
*before* recording a gap for a seat that simply does not appear.

## The ACFR — a near-universal roster source, better than audit reports

Almost every US municipality publishes an Annual Comprehensive Financial Report, and its
**"List of Principal Officials"** page names the mayor, every council seat, and usually the
presiding officer.

Two properties make it strictly better than the state-audit route the registry recommends:

- **Annual rather than episodic** — one linked series covers every panel year. Auburn's runs
  FY2000-FY2025 as direct PDFs, giving seven verbatim official snapshots for this panel.
- **It names the presiding officer**, which election results structurally cannot.

Diffing consecutive years' officials pages also dates council-size changes and mid-term
replacements directly — which is exactly the evidence Homewood's shifting ward count needs.
ACFRs are frequently hosted **off-domain** (state repositories, EMMA/MSRB bond disclosure, the
audit firm), so a robots block on the city domain need not reach them.

## Alabama's EOPA route is not universal

The registry rates EOPA audit reports "Verified" for Alabama, but that verification was on
**Homewood specifically**. Auburn is audited by an **independent CPA firm**, not the Department
of Examiners of Public Accounts — EOPA has nothing for it, and a search returns only the county
commission, county BOE and the university. The URL pattern also needs a **per-city numeric id**
that is not derivable and did not surface by search for Fairhope.

Not a dead host — a **category mismatch**, and it will recur for larger Alabama cities.

## CivicClerk's OData API is on a different HOST

The census recorded the endpoint as `{tenant}.portal.civicclerk.com/api/v1/Events`. **That
404s.** The working endpoint is:

```
https://{tenant}.api.civicclerk.com/v1/Events
```

Verified returning JSON. This matters well beyond Alabama — CivicClerk appears across the
corpus, and the correct host turns a JavaScript-only portal into a live minutes archive.

## Bulk-queryable hyperlocal sources

A **Blogger-hosted local paper was the single highest-yield source for Fairhope**, carrying a
runoff, two organizational meetings, a resignation-and-appointment, and an entire
presiding-officer rotation. Blogger exposes a JSON feed
(`/feeds/posts/default?alt=json&q=<terms>`) that returns hundreds of full post texts in one
call; WordPress exposes `wp-json/wp/v2/search`. Note `published-min` is ignored when `q` is
present.

## 2021 Act — registry gap partially closed

| City | Status | Evidence |
|---|---|---|
| Mobile | Exempt | already odd-year (2021, 2025) |
| Auburn | **Unaffected** | cycle is Aug 2018 / 2022 / 2026 — never had a 2024 election to move |
| Fairhope | **AFFECTED** | no 2024 cycle at all; Aug 2020 council served a **five-year term** to 2025-11-03, next election 2025-08-26 |
| Homewood, Selma | Unverified | in progress |

The decisive test is simply **whether a 2024 election happened**. If not, the prior term was
extended to five years and every later term boundary shifts.

## Fetchability

`gulfcoastmedia.com` and Alabama local news generally **403 WebFetch but fetch cleanly by curl**
with a browser UA. **`wkrg.com` blocks both** (HUMAN Security challenge) — the Fairhope agent
correctly declined to record vote totals it could not verify verbatim rather than trusting a
snippet. `www.fairhopeal.gov` is Akamai-blocked on every HTML path via both methods.

---

# Batch 4 — Virginia

## The census's "no working archive" list is not reliable

Poquoson was one of the **eight cities the census recorded as having no working archive**, with
`robots.txt` "timing out on repeated attempts". In fact `ci.poquoson.va.us` and its `robots.txt`
both returned **HTTP 200 to plain curl with a browser UA on the first try**, and robots disallows
only `/admin`, `/Search`, `/Map`, `/CurrentEvents` and `/RSS.aspx`. The city's ACFR archive was
sitting on that same domain.

The city reached **100% coverage with zero gaps**. A census entry records what one fetcher saw on
one occasion — **re-test before accepting a negative**. Seven cities remain on that list, all in
batches still to run.

## `historical.elections.virginia.gov` is scriptable after all — the best Virginia source

The registry recorded it as non-scriptable because every constructed *locality/contest* path 404s.
That is true, and it is the wrong shape of URL. The **numeric contest form works**, and behind it
is a CSV API returning full precinct-level canvass data:

```
https://historical.elections.virginia.gov/elections/view/{contest_id}/
https://va2.elstats.civera.com/api/download_contest/{id}_table.csv?split_party=false
```

**Contest ids are contiguous within an election**, so one seeded id lets you sweep to enumerate the
rest. This sourced **every cycle** for Poquoson at Rung 1. It should generalize to all Virginia
localities — and critically to **towns**, whose contests are ids like any other, which sidesteps the
county-nesting problem that the registry flags as Virginia's biggest structural trap.

The site's own `/search` is a Next.js SPA and useless to a fetcher.

## Virginia localities publish their own canvass archives

Norfolk's Office of Elections hosts one official canvass PDF per election date **back to 2008** at
`norfolk.gov/4713/Election-Results` — plain curl, clean under `pdftotext -layout`, found via the
CivicPlus site search `/Search/Results?searchPhrase=election+results`. A second `high`-confidence
primary route that ignores the state portals. Extraction caveat: candidate names sit in **stacked
header rows above their columns** and must be aligned by character offset.

## VPAP is dead

| City | Result |
|---|---|
| Norfolk | empty JS shell on 200, HTTP 500, HTTP 404 — 0 usable of 3 |
| Poquoson | **HTTP 202 with 0 bytes** on all 5 dates to curl; **403** to WebFetch — 0 usable of 5 |

The registry called it "the working fallback" with rendering "inconsistent". It is worse than that.
It did recover Tazewell's 2020 cycle in an earlier pilot, so it is locality-dependent rather than
uniformly dead — but **an empty response is a failed fetch, not evidence that no election occurred.**

## The May→November shift hit CITIES, not just towns

The registry frames this as SB 1157, a town rule effective 2022. **Norfolk — a city — voted in May
through 2020**, then moved to November with terms **extended, not cut**: wards elected 2018-05 ran
to **2022-12-31**, and the 2020 cycle, **postponed to 2020-05-19 by COVID**, ran to **2024-12-31**.
Norfolk therefore had **no council contest in Nov 2018 or Nov 2020 at all**.

Poquoson, by contrast, has voted even-year November throughout with no May cycle — so this is
per-locality, not statewide. Establish the calendar before spending escalation budget on a cycle
that may never have existed.

## A missing `-L` makes a live archive look dead

Poquoson's CivicPlus ACFR series at `Archive.aspx?AMID={n}&Type=&ADID={n}` returns **0 bytes without
`curl -L`** and the full PDF with it — indistinguishable from an empty archive. Follow redirects
before concluding a document endpoint is broken.

## Dead ends worth not repeating

**Virginia Electoral Board minutes are procedural only** — they record that "a canvass was conducted"
and name no candidates. Ballotpedia had a single Poquoson page across the whole window.
