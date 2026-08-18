# State Source Registry

## Why this exists

Source discovery is what consumes the research budget. It is a **per-state** problem, not a
per-city one. A 64-city corpus spanning 12 states means 12 discovery problems, not 64.

Build the registry once, up front, before any city research runs. One agent per state, ~55-95k
tokens each.

## Rules

0. **An entry records WHEN it was verified, not that it still works.** Michigan was rated HIGH
   and "validated end-to-end"; its county host later began returning 403 to everything,
   including `/robots.txt`. Treat every entry as a **lead to re-verify**, not a fact. Budget for
   roughly one dead source per batch, and when a primary source is gone, route around it and say
   so plainly rather than reporting the city as unrecoverable.
1. **Verify every URL pattern by actually fetching it.** An unverified pattern is worse than an
   empty field, because downstream agents will trust it and waste budget. Every entry below marked
   "verified" was fetched at least three times across different localities and years.
2. **Record dead ends explicitly.** "Clarity Elections is robots-blocked" saves every downstream
   agent from rediscovering it.
3. **Distinguish blocked from absent.** A 403 or robots failure means unverified, not disproven.
4. **Output an operational block** of direct imperatives, pasted verbatim into downstream prompts.

## Fields to resolve per state

Results URL pattern (with quirks) · verified URLs · failed patterns · exact election dates ·
county map · race naming convention · fetchability per host · **mayor determination** ·
audit reports · municipal league / trade press · public-notice portal · government conventions.

### On mayor determination

In council-manager cities the mayor is chosen **by the council from among its members** and never
appears on a ballot. Election results alone will not give you the mayor. Getting this wrong
produces a confident, complete-looking roster with the wrong person as mayor.

Verified rotating/council-selected in this corpus: Bothell WA, Lacey WA, Albany CA, Canyon Lake CA,
Ripon CA, Yuba City CA, Sahuarita AZ, Bristol VA, Franklin Twp NJ.

---

## Cross-state findings

These emerged from building all twelve entries and generalize beyond this corpus.

**1. State audit reports are the most underrated source.** Municipal audits normally contain a
governing-body page naming the mayor and full council with term dates.

| State | Status |
|---|---|
| Alabama | **Partial — see the Alabama entry before relying on this.** `alison.legislature.state.al.us/files/pdf/eopa/audit_reports/{yy}__{id}_{yy}-{id}-City%20of%20{Name}.pdf` — "Exhibit #1" names mayor + council with term years. No search UI; find via search engine. **Verified on Homewood only; confirmed ABSENT for Auburn, Mobile and Selma** (larger cities use independent CPA firms; EOPA holds only their county's reports). Not a per-year series. |
| South Dakota | **Verified.** `legislativeaudit.sd.gov/reports/City/{City} City {Year}.pdf` — "City Officials" page, as of Dec 31. |
| TN, GA, AZ, VA, MI, NJ | Source class exists; municipal-level index not located or not fetchable. Open leads. |
| California, Massachusetts | **Ruled out.** State Controller / DLS reports are financial only, never name officials. |

**2. ⚠ CLARITY IS NOT ROBOTS-BLOCKED — this entry was WRONG, and it was the project's most
expensive wrong entry (corrected 2026-08-17).**

`results.enr.clarityelections.com/robots.txt` returns **HTTP 404**, serving the same 2,616-byte
page as any nonsense path — i.e. **no robots.txt exists**, so no Disallow directive exists either.
The original finding ("failed robots checks in every state tested") appears to have read a *failed
check* as a *prohibition* — precisely the confusion Rule 3 above warns against. Clarity carries the
richest municipal data of anything found in this corpus and was written off from the start on this
basis.

**And its JSON API is open even where the web UI resists a fetcher.** Route, verified on Essex
County NJ:
```
{county}clerk.com/Election/                     → lists elections with their Clarity election id
…/{ST}/{County}/{id}/current_ver.txt            → current version string
…/{ST}/{County}/{id}/{ver}/json/en/summary.json → full contest/candidate/vote arrays, plain JSON
```
Election ids remain non-sequential and must be discovered per election. **Confirmed working in
production**: one city sourced all five of its cycles (2016-2024) from certified county canvass JSON
this way, after the same county turned out to publish **no canvass PDFs at all**. **This should
generalize to every Clarity county in the corpus** (NJ, GA, TX, AZ) — all of which were routed around
at significant cost.

**Three traps in the JSON route, all live:**
- **Older elections use a different filename and shape** — 2016 served `json/sum.json`, a *dict* with
  flat vote arrays, rather than `json/en/summary.json`.
- **Bodies arrive GZIPPED, sometimes with no `Content-Encoding` header** — use `curl --compressed`;
  raw output looks like binary garbage and reads as a broken endpoint.
- **ID discovery is the hard part.** `/NJ/{County}/elections.json` returns an **empty array** on
  multiple counties and every `ElectionList`/`api` variant returns the generic ENR shell — there is
  often **no past-election index**. What works: sweep `current_ver.txt` across a plausible id range
  anchored on a known neighbouring county's id (one agent found Middlesex's 2024 id by sweeping
  122100-123400 anchored on Essex's 122756, hitting exactly two live ids).
- **Coverage is not universal.** Hudson County NJ exposes only a 2026 primary id, and
  `/NJ/{County}/elections.json` returned `[]` — no id-discovery route at all, so its historical
  municipal results had to come from the clerk's own PDF archive instead. A Clarity county may still
  be a dead end for older years.
- **The `{ver}` segment is mutable** — always read `current_ver.txt` rather than caching a version. Note one filing quirk: a May municipal election may be filed under a
"Special Municipal Elections" entry rather than a "May Municipal" one.

**2b. County filing-period incumbent lists are the best small-town source found.** County
election offices publish *incumbent lists* and *cities-and-towns rosters* as PDFs — these are
**not canvasses**, and the ladder does not otherwise point at them. Their Remarks fields carry
**appointment and resignation dates**, exactly the mid-term data election results structurally
cannot contain. Verified on Lewis County WA (`lewiscountywa.gov/…/documents/{id}`), yielding
verbatim lines like `Kenneth Smith - Elected 2015, Resigned 4/25/2019`. Two-thirds of one town's
entire yield came from three such documents. Editions are not indexed together — a fourth was
found only on a second pass — so enumerate ids rather than assuming you have them all. Note the
field may be populated only for larger municipalities in the county.

**3. Municipal leagues and trade press are the small-town unlock — but only some are free.**
Tennessee's *Tennessee Town & City* (verified, statewide tallies) and Georgia's `gacities.com`
(verified, current rosters) work. Alabama's and New Jersey's are **paid products**. Arizona's is
unverified. Texas's magazine is JavaScript-gated.

**3b. An absent seat may mean UNOPPOSED, not missing.** Alabama declares sole qualified
candidates elected **without a ballot**, so unopposed seats never appear in results at all — one
Auburn cycle was missing 4 of its 9 seats for this reason, including the mayor. Reading those
omissions as missing data produces spurious gaps and a half-empty roster. Certification of an
unopposed seat is often published **weeks apart** from the contested results, as a separate
notice. **Before recording a gap for a seat that simply does not appear, establish what the state
does with unopposed candidates.** **Confirmed statutory in THREE states** — Texas under **Elec. Code §2.053** (the city passes an
ordinance cancelling the election and declaring the unopposed candidates elected, so the city
**vanishes from that date's county canvass entirely** — seen in four Texas cities), Alabama, and
Georgia
under **O.C.G.A. §21-2-285(c) / §21-2-291** (no election is held in a precinct where no candidate
is opposed; the unopposed candidate is deemed to have voted for themselves and is certified
elected). Assume other states have equivalents and check the statute rather than guessing.

**3c. The ACFR is a widely available roster source — but an audit report is NOT an ACFR.**
The distinction is what makes this work or fail. A full **Annual Comprehensive Financial Report**
has an *introductory section* containing the **"List of Principal Officials"**. A bare
**financial-statement audit** has no introductory section at all — it opens straight at "FINANCIAL
SECTION" and addresses its transmittal generically to "the Honorable Mayor and Members of City
Council", naming nobody. Verified both ways: Auburn publishes true ACFRs FY2000-FY2025 with a full
officials page; **Selma's series contains no principal-officials page in any year**, FY2020 is
missing entirely, and FY2018-FY2019 are image-only scans. Smaller or fiscally distressed cities
frequently publish only the audit. **Check the table of contents for an introductory section
before spending budget on the series.**

Where a true ACFR exists it is the best roster source available, for two reasons: it is **annual
rather than episodic**, giving a verbatim official snapshot for *every* panel year from one linked
series; and it **names the presiding officer**, which election results structurally cannot.
Diffing consecutive years' officials pages also dates council-size changes and
mid-term replacements directly.

**But the officials page is not infallible — FOUR failure modes, all observed:**
0. **It can run AHEAD of its own fiscal year, not just behind.** One city's ACFRs are as-of-
   *publication* rosters: the FY2020 report (fiscal year ending 2020-06-30, when Croft was still
   mayor) prints "Jack Miller, Mayor" — the council seated that **December**. This is the mirror
   image of stale carry-over and would silently mis-date an entire series. **Establish which
   convention a series uses before trusting any of it**, by checking one year against a dated
   primary record.
1. **Stale carry-over.** One FY2025 report still printed the *previous* year's council chair. A
   contemporaneous council agenda named the real one. When an ACFR contradicts a dated primary
   record, the primary record wins.
2. **It is a snapshot, not a span.** Every page is as-of fiscal-year-end (commonly June 30), so a
   member who left in the autumn still appears in that year's report — one FY2021 report showed a
   mayor who had been gone for months. Never read it as a full-year roster.
3. **Extraction quirks.** Filenames are inconsistent within a single series (`FYnn-Annual-Report`,
   `FY23-ACFR`, `FY24-ACFR-Updated-version`, `Revised-FY25-COM-ACFR`) across several upload
   directories, so **scrape the finance page for real hrefs rather than constructing them**; some
   bare domains serve a small HTML challenge for PDFs where the `www.` host serves the file; and
   some pages extract **with all spaces stripped**, which silently welds names together. Look under the city's finance department; ACFRs are often hosted
**off-domain** (state repositories, EMMA/MSRB bond disclosure, the audit firm), so a robots block
on the city domain need not reach them.

**4. Ballotpedia is INTERMITTENT — two agents got opposite results on the same day.** One received
an **HTTP 202 JavaScript bot-challenge shell**; another, hours later, got **HTTP 200 with full
content on 18 of 18 URLs** via plain curl with a browser UA, including result tables. Its
officeholder pages carry **Predecessor / Successor / "Years in office"**, which resolved a seat
lineage no other source gave. **Always try it — but never conclude it is dead from a single
failure, and never depend on it.** Robots still disallows it for direct fetch as a stated
preference.

**5. Two-year terms double your work.** Massachusetts cities and many Texas cities use 2-year
terms, meaning 4 election cycles per 8-year panel instead of 2.

---

## Verified entries

### Washington — HIGH

```
https://results.vote.wa.gov/results/{YYYYMMDD}/{County}/
```
County takes **no spaces**: `WallaWalla`, not `Walla Walla` (404). **No robots.txt at all**;
server-rendered, fetches cleanly. No index at host root — dates must be supplied.

Dates: `20151103, 20171107, 20191105, 20211102, 20231107, 20251104`. August primaries only where
3+ filed; the November general is authoritative.

Verified across Lewis, King, Snohomish, WallaWalla, Thurston, Island for 2015/2021/2023/2025.

**⚠ King County's 2015 dataset is incomplete (verified 2026-08-17).** `…/20151103/King/` returns
**HTTP 200** but carries only Auburn, Bothell, Milton and Pacific — the four cities straddling a
county line. Seattle and Federal Way are genuinely absent, and the linked county export CSV omits
them too; there is no pagination to miss. Confirmed independently by two agents. **A clean 200
from this host is not evidence a city is absent** — go to the King County certified final canvass
PDF instead. This does NOT generalize: Thurston, Island and WallaWalla all returned 2015 municipal
races cleanly.

**Washington's State Auditor does NOT name officials.** The cross-state "audit reports" finding
holds for Alabama and South Dakota but fails here — WA SAO reports are addressed generically to
"Mayor and City Council". Do not spend Rung 3 budget expecting a roster.

At-large numbered Positions, 4-year staggered; a full snapshot needs the **two most recent**
generals. **Multi-county cities** (Bothell = King + Snohomish) report the same race separately in
each county — fetch both and sum. Three races flipped winner versus either county alone.

Mayor: council-selected in Bothell, Lacey; directly elected in Federal Way, Oak Harbor,
College Place, Vader.

### Michigan — PRIMARY SOURCE DEAD as of 2026-08-17 (was rated HIGH)

**`www.waynecountymi.gov` returns HTTP 403 to everything** — hub, every `/…-Elections` subpath,
the `/files/assets/mainsite/…` PDF directory, the site root, even `/robots.txt` — via both
WebFetch **and** curl with full browser UA/Accept/Referer. A blanket WAF block, not robots, so
politeness does not get around it. `waynecounty.com` 302s into the same host.
`michigan.totalvote.com/Wayne` serves only the current election. `mielections.us` does not
respond at all. **No cycle was recoverable from any official Michigan source.**

**What works instead:** `arabamericannews.com` is fully fetchable **by curl**, including its
site search at `?s=<query>`, returning dated permalinks. A full Dearborn Heights reconstruction
— every cycle plus six mid-term changes — cost **5 WebSearches**; a follow-up run cost **zero**.
`patch.com` and `ballotpedia.org` also fetched fine by curl. Expect `medium` confidence
throughout, since news is not a canvass.

The path below is retained only in case the block is lifted. Wayne County Clerk, verified with a
complete Dearborn Heights roster for 2019 and 2023:
```
https://www.waynecountymi.gov/Government/Elected-Officials/Clerk/Elections/Election-Results-Candidates
  → /{startYear}-{endYear}-Elections        e.g. 2016-2020-Elections, 2021-2024-Elections
  → /{YYYY}/{Month}-{D}-{YYYY}-{Type}-Election-Results
  → PDF under /files/assets/mainsite/v/1/clerk/documents/elections/election-results/{yyyy-month-d}/
```
**The hub slug does not match the visible link label** — do not guess it. Take the "Official
Summary Report" PDF, not the candidate-listing PDF (no votes).

Races labeled `Mayor - City of {City}` and `City Council - {City} (Vote for N)`; a vacancy fill
appears as a separate "Partial Term" race on the same ballot.

Odd-year cycle: August primary → November general. `michigan.gov/sos` is a directory of links, not
a results host. `mielections.us`, `dearbornheightsmi.gov`, Ballotpedia all robots-blocked.

**Why this state is the best illustration of Step 5.** Dearborn Heights had *two* mid-term
mayoral successions in the window: Daniel Paletko died Dec 29 2020 → Council President
Malinowski-Maxwell interim → Council appointed Bill Bazzi Jan 2021 → Bazzi won both the partial
and full term Nov 2021; then Bazzi resigned in 2025 → Mo Baydoun acting → won Nov 2025. Neither
appears in any election result. `arabamericannews.com` covered every appointment vote.

### Alabama — MEDIUM-HIGH

**No statewide results source** — municipalities administer their own elections. Verified against
the SoS and confirmed by reporting.

**Best historical source: EOPA audit reports** (see cross-state table above). Verified on
Homewood — **but NOT universal.** Larger Alabama cities are audited by independent CPA firms
rather than the Department of Examiners of Public Accounts, so EOPA simply has nothing for them
(confirmed for Auburn; a search returns only the county commission, county BOE and the
university). The pattern also needs a **per-city numeric id** that is not derivable and did not
surface by search for Fairhope. **Use the city's own ACFR series instead** — see cross-state
finding 3c; it is annual, names the presiding officer, and worked where EOPA did not.
EOPA confirmed absent for **Auburn** (independent CPA firm) and **Mobile** (EOPA holds only
*Mobile County Commission* reports) — three cities now, so treat the category mismatch as the rule
for larger Alabama cities, not the exception. Verified ACFR routes:
`auburnal.gov/finance/city-information/acfr/` and `cityofmobile.gov/government/financials/`
(FY2019-FY2025, curl-fetchable, clean under `pdftotext -layout`, org charts naming every district
holder and — from FY2022 — annotating `(President)` / `(Vice President)`). Mobile's **FY2025 ACFR
uniquely carries two charts**, "as of 09/30/2025" and "as of 11/03/2025", so one document sources
an entire handover. Selma's series by contrast has no officials page in any year — see 3c.

**⚠ Unopposed seats are ABSENT from Alabama results** — see cross-state finding 3b. This is the
single most likely cause of a spurious gap in this state.

**2021 Act status, resolved per city (2026-08-17):** Mobile **exempt** (already odd-year, 2021 /
2025). Auburn **unaffected** — its cycle is Aug 2018 / 2022 / 2026, so it never had a 2024
election to move. Fairhope **AFFECTED** — no 2024 cycle at all; the Aug 2020 council served a
**five-year term to 2025-11-03**, next election 2025-08-26. Homewood **AFFECTED** (SB119, signed
April 2021) — same profile, term 2020-11-02 to 2025-11-03, confirmed three independent ways
including EOPA Exhibit #1 listing every 2020-elected member as "Term Expires 2025". Selma **AFFECTED** — no Aug 2024 election; next cycle 2025-08-26, so the 2020 council served
2020-11-03 to 2025-11-03. **Three of five resolved cities were affected**; treat "affected" as
the default prior for an unverified Alabama city, then confirm with the whether-a-2024-election-
happened test.

**Selma's proposed council reduction never took effect.** A July 2024 plan to cut eight districts
to five and abolish the elected at-large presidency died with the council attorney; Selma voted in
Aug 2025 on eight wards plus the at-large presidency. Size was **constant at 9** across the window.
The decisive test is simply **whether a 2024 election happened**; if not, the prior term was
extended to five years and every later term boundary shifts.

**Alabama local news 403s WebFetch but generally fetches cleanly by curl** with a browser UA
(`gulfcoastmedia.com` verified). `wkrg.com` blocks **both** (HUMAN Security challenge) — do not
retry it.

Auburn publishes its own results archive at `auburnal.gov/elections/results/` (ward-level, 2018+).
Other corpus cities publish current rosters only.

Elections: 4th Tuesday in August, terms begin November. **A 2021 Act moved most cities' August
2024 elections to August 2025 and extended the prior term to five years.** Mobile is exempt
(already odd-year: 2021, 2025). Verify per city — do not assume a uniform cycle.

**Structural instability — and the Homewood note here was wrong (corrected 2026-08-17).**
Homewood did **not** run "10 members / 5 wards". It ran **12 elective offices**: Mayor + a
**separately elected at-large Council President** (a real council seat, presides, and is the
statutory successor to the mayor) + **10 ward councilors (5 wards × Place 1 / Place 2)** — an
11-member council, **constant across 2019-2024**. The change is a single step at **2025-11-03**:
a 2024-09-24 special election adopted the **Council-Manager form**, and the Aug 2025 election ran
on **4 newly drawn wards, one councilor each, plus a directly elected Mayor who serves as Council
President** — a 5-member council. Seat labels are `Ward N Place M` before and `Ward N` after, and
they are **not interchangeable**: the wards were redrawn from scratch.

Selma has 8 wards + an at-large elected Council President with a reduction proposed. In both
cities the **Council President is an elected seat, not an internal title** — record it as
`council_member`, never `vice_mayor`. Do not assume constant council size across the panel.

EOPA reports are **not a per-year series** — Homewood has exactly one (`25-169`), fetched by
curl with a browser UA plus `pdftotext -layout`. `bhamwiki.com` is **Cloudflare-walled** (403 to
both curl and WebFetch). `thehomewoodstar.com`'s `?s=` site search is JS-driven and returns
nothing to curl, though its article pages fetch cleanly via WebFetch.

**`selmatimesjournal.com` is NOT "snippets only" — that line was wrong (corrected 2026-08-17).**
`curl` with a browser UA returns HTTP 200 and full text. Migration quirk: dated
`/YYYY/MM/DD/slug/` permalinks render only headline+lede, while **`/news/{slug}-{importedId}`
returns the full body** — the importedId is printed in the dated page's own markup. It is
**Next.js, not WordPress**, so the `wp-json` trick returns an error shell.

Two more Alabama outlets, both curl-fetchable: **`bamapolitics.com`** carries complete per-race
results including runoffs and `(I)` incumbency markers at
`/alabama/alabama-elections/{Y}-alabama-elections/{Y}-{city}-al-{race}-election/` — but coverage is
patchy per city (only 2020 exists for Selma). **`blackbeltnewsnetwork.com`** is TownNews with a
plain-HTML site search at `/search/?q=<terms>&s=start_time&sd=desc`. `selmasun.com` is **dead** —
permalinks 200 but redirect to the BBNN section front.

**Homonym trap:** ABC11 (Raleigh-Durham) stories about "Selma council members" are **Selma, NORTH
CAROLINA**. AL.com: search snippets only. `almonline.org` has no free directory,
but its election-date calendar PDFs are fetchable and useful.

### Virginia — MEDIUM (prior notes were substantially wrong)

**Correction: `results.elections.virginia.gov` does not cover "2022 onward."** Of thirteen
election folders tested spanning 2014-2025, **only `2022 November General` returns content**.
Everything else 404s, before *and* after. It is an orphaned snapshot from a migration.
```
https://results.elections.virginia.gov/vaelections/2022%20November%20General/Site/Locality/{NAME}_CITY/Index.html
```
Live results moved to `enr.elections.virginia.gov` — a JS SPA, unfetchable.

**⚠ CORRECTION OF THE CORRECTION (2026-08-17): `historical.elections.virginia.gov` IS scriptable
— this is the best Virginia source that exists.** Constructed *locality/contest* paths do 404, which
is what earlier testing found. But the **numeric contest form works**, and there is a CSV API behind
it returning full precinct-level canvass data:
```
https://historical.elections.virginia.gov/elections/view/{contest_id}/
https://va2.elstats.civera.com/api/download_contest/{id}_table.csv?split_party=false
```
**Contest ids are contiguous within an election**, so one seeded id lets you sweep the neighbourhood
to enumerate that election's other contests. This sourced **every cycle** for one city at Rung 1 and
should generalize across the state — including to **towns**, whose contests are ids like any other,
sidestepping the county-nesting problem entirely. **⚠ THE CSV ENDPOINT 307-REDIRECTS — `curl -s` without `-L` returns an HTML stub, so a sweep
silently finds NOTHING.** One agent swept **540 ids, got zero hits, and nearly recorded "ids are not
clustered" as a finding**; with `-L` they were clustered exactly as expected. **Always `curl -sL`.**

**Try both path forms:** `/elections/view/{id}/` worked on one locality and 404'd on another where
`/contest/{id}` returned 200. Test both before calling an id dead.

**The mayor contest sits immediately below the council contest id** for the same locality and date —
confirmed pairs 134206/134209 (2018), 144704/144705 (2020), 161672/161673 (2024).

**Clustering is not universal.** A full sweep of 134240-134300 from a 2018 seed returned no Bristol
City row at all, though the numeric form worked for that city on other dates. Treat the sweep as a
cheap first attempt, not a guarantee.

**Sweep from a SAME-ELECTION seed, never from the previous cycle's block — the id blocks are not
adjacent, and the failure mode is misleading.** Sweeping forward from 2022's block into 168249-168254
returned `"this contest does not have a division assigned"` **HTTP 500s on every id**, which reads
like a broken endpoint rather than a wrong neighbourhood; the real 2024 block was 161546-48, *below*
the guess. Seed ids gathered so far:

| Election | Known contest ids |
|---|---|
| 2016 | 81065, 81066 (Portsmouth) |
| 2018 | 134263 (Poquoson), 134266 (Portsmouth) |
| 2020 | 144755, 150812-150822 (Poquoson), 144756, 144757 (Portsmouth) |
| 2022 | 156793 (Poquoson) |
| 2024 | 161542 (Poquoson), 161546, 161547 (Portsmouth) | The site's own `/search` is a Next.js SPA and useless to a
fetcher — go straight to the numeric paths.

**⚠ THE REAL VIRGINIA UNLOCK: localities publish their OWN canvass archives (found 2026-08-17).**
This routes around every broken state portal. Norfolk's Office of Elections hosts **one official
canvass PDF per election date back to 2008** — plain curl, clean under `pdftotext -layout`:
```
https://www.norfolk.gov/4713/Election-Results
```
It was found via the **CivicPlus site search** `/Search/Results?searchPhrase=election+results`, which
is the way to locate the equivalent page on any Virginia locality. **Try this FIRST**, before the
state portal or VPAP: it is `high`-confidence primary evidence, and for towns the equivalent sits at
**county** registrar / electoral-board level. Extraction caveat: candidate names sit in **stacked
header rows above their columns** and must be aligned by character offset, not read in linear order.

**⚠ VPAP is dead — FIVE independent confirmations across five localities. Do not use it.**
Tazewell got an **HTTP 202 Akamai challenge shell (2,425 bytes)** on both town and county slugs;
Bristol VA got empty 200s then the same 2,425-byte error page on every date. **The registry's claim
that VPAP recovered Tazewell's 2020 cycle no longer holds.** Portsmouth identified
the mechanism: an **AWS WAF JavaScript challenge**, returning HTTP 202 with a ~2.4KB shell to curl
and 403 to WebFetch on every date. This is not intermittent rendering; it is a bot wall. Poquoson: **HTTP 202 with
0 bytes** on all five date slugs to curl, **403** to WebFetch — 0 usable of 5. Three dates tried: `20241105`
returned **HTTP 200 with an entirely empty JS shell**, `20201103` returned **HTTP 500**, `20181106`
returned **404**. Zero usable pages out of three, contributing nothing. **An empty 200 is a failed
fetch, not evidence that no election occurred.** It did recover Tazewell's 2020 cycle in an earlier
pilot, so it is locality-dependent rather than uniformly dead — but do not budget on it.

**VPAP as fallback**, archive back to 2015:
`https://www.vpap.org/electionresults/{YYYYMMDD}/local/{locality-slug}-va/`. Content rendering is
inconsistent — 3 of 6 detail pages returned empty on a 200. Confirm non-empty before trusting.

**The critical structural fact: towns have no standalone locality page.** Tazewell's mayor and
council races appear nested inside `TAZEWELL_COUNTY`, alongside Bluefield, Cedar Bluff,
Pocahontas and Richlands. Independent cities (Norfolk, Portsmouth, Bristol, Waynesboro, Poquoson)
*are* top-level. **Always look up a town by its containing county.**

Town elections moved May → November under **SB 1157 (2021)**, effective for elections after
Jan 1 2022. §24.2-222.1 bars shortening terms — incumbents held over, so terms were *extended*.

**The same shift hit CITIES, not just towns, and earlier (confirmed on Norfolk 2026-08-17).**
Norfolk voted in **May through 2020** and then moved to November, with terms **lengthened, not cut**:
wards elected 2018-05 ran to **2022-12-31**, and the 2020 cycle — **postponed to 2020-05-19 by
COVID** — ran to **2024-12-31**. So Norfolk had **no council contest in Nov 2018 or Nov 2020 at
all**. Consequences for any Virginia locality: a "missing" November cycle early in the panel is a
structural fact rather than a gap; a term you assume is four years may be four and a half; and a
**May 2020 election may have been COVID-postponed to an unexpected date**, which is easily mistaken
for a cycle that never happened. Establish the calendar before spending escalation budget.

Norfolk is **council-manager**: mayor elected at large, **Vice Mayor chosen by the council from
among its members**, 8 members (Mayor + Wards 1-5 + Superwards 6-7). Its **ACFR series FY2011-FY2025
carries a "Municipal Officials" page** (PDF p10 for FY2019-22, p12 for FY2023-25) — an annual spine,
but **titles only, no ward numbers**, so seat assignment must come from the canvasses.

Mayor: directly elected in Norfolk, Tazewell (town), and Poquoson (an at-large seat that serves as
mayor); **council-selected in Bristol — and the registry's old wording, "simply the top vote-getter in an
ordinary at-large council race", was IMPRECISE (corrected 2026-08-17).** Charter §4.05 is explicit:
*"council shall elect one of its members as chairman, who shall be entitled mayor and one of its
members as vice chairman, who shall be entitled vice mayor, each of whom shall serve for a term of
one year."* It is a **distinct charter office filled by an internal annual vote**, not a by-product
of the poll. **The trap is live:** in 2022 Jake Holmes led the poll with 2,621 votes and did **not**
get it — Neal Osborne became mayor on 2023-01-03, and Holmes did not become mayor until 2026-01-05.
Reading the ballot top as a mayoral win would have been wrong by three years and one person.

**The state contest index independently confirms Bristol VA has NO mayoral ballot line**, and the
proof is a positive control: its 2020 block is `139711` School Board / `139712` City Council and its
2024 block `161319` City Council / `161320` School Board — no Mayor contest in either — while
**Chesapeake City in the very same 2020 block does carry one** (`139713` Mayor beside `139714` City
Council). That rules out an indexing artifact. Bristol VA is council-manager, **5 at-large seats, no districts**,
4-year staggered in two classes (3+2), with mayor **and** vice mayor selected annually by the
council. **Waynesboro — RESOLVED as COUNCIL-SELECTED (2026-08-17), closing the registry's open question.**
Charter §3.4(c): *"The council shall elect one of its members as mayor"*, and a vice mayor likewise,
both on **two-year** terms (§3.4(d)). Corroborated three ways: the 2022 state-portal locality page
lists Ward C and Ward D contests and **no** mayoral contest; a 2024 canvass sweep found council
contests only; and every organizational meeting records a roll-call motion "to appoint … as Mayor
for the two-year term ending …". Composition (§3.2(a)) is **five members — one resident each of
Wards A, B, C, D plus one at-large**, four-year terms, with **C+D** elected together (2018, 2022,
2026) and **A+B+At-Large** together (2020, 2024). Waynesboro **did** shift May→November under
SB 1157 with terms extended, so there was no council contest in Nov 2018 or Nov 2020; the July 2022
minutes record the bridge verbatim, moving the mayor's and vice mayor's terms "to terminate on
January 1, 2023".

**Bristol VA also moved May→November with terms EXTENDED** — first Tuesday in May of even years
through 2020 (the May 2020 election **COVID-postponed to 2020-05-19**), then November of even years;
the 2018 class ran to 2022-12-31 and the 2020 class to 2024-12-31. So 2019, 2021, 2023 and 2025 are
structural holdover years. **Three of six Virginia localities made this shift** — Norfolk, Bristol and Waynesboro — while
three did not (Portsmouth, Poquoson, Tazewell). It is genuinely per-locality and **splits almost
evenly**, so check each charter rather than assuming either way. Where it happened, terms were
**extended**, and a May 2020 election may have been **COVID-postponed to 2020-05-19** — a real cycle
on an unexpected date, easily mistaken for one that never happened.

**Read the charter FIRST — the single cheapest, highest-yield source in Virginia:**
`https://law.lis.virginia.gov/charters/{locality}/`. One fetch routinely settles composition,
calendar, term length, mayor-selection, the organizational-meeting date rule and the vacancy-filling
deadline. For Bristol it corrected a term boundary (councilmembers serve "from January 1 following
their election", so the 2022 class began **2023-01-01** — the 2023-01-03 date is merely the oath),
converted an inferred organizational-meeting date into a **charter-derived** one (§4.03: "nine
o'clock a.m. on the first business day following January 1"), and its 30-day vacancy rule
corroborated two appointments (filled in 28 and 24 days). Several rows moved from medium to high
confidence on the strength of it. It settled Portsmouth's mayor-selection question
outright and, for Tazewell, disclosed in a single fetch that there was **no May→November transition
at all** and that its **mayor serves a TWO-year term while councilmen serve four** — a fact that would
otherwise have mis-stated 2021, 2023 and 2025.

**Portsmouth — RESOLVED as directly elected (2026-08-17), upgrade from "medium-confidence".** Three
independent proofs: the charter at `law.lis.virginia.gov/charters/portsmouth/` ("a Mayor and six
Council members to be elected by and from the city at large", mayor elected "in nineteen hundred
seventy-six and every four years thereafter"); a standalone `Mayor — Portsmouth City` ballot contest
in 2016, 2020 and 2024; and the city's own bio pages giving explicit term dates. Its **Vice Mayor is
internal** — council-selected on a 2-year presiding term (Jan 2019/2021/2023/2025) — and the two must
not be conflated. Composition is **7 at-large seats (Mayor + 6), constant**, no wards at any point,
3 council seats per November even-year general. Portsmouth **did not vote in May**, so the SB 1157
shift and COVID postponement that hit Norfolk do not apply — the calendar is genuinely per-locality.

**Portsmouth's CMS is an SPA trap.** `/AgendaCenter/ViewFile/`, `/ArchiveCenter/ViewFile/`,
`/DocumentCenter/View/` and `/Search/Results?searchPhrase=` all return **HTTP 200 with an identical
~327KB React shell**, `text/html`, never a PDF — even for documents a search engine has indexed with
full text. Norfolk's CivicPlus site-search route does **not** work here. The replacement asset host
does serve real PDFs to plain curl — `https://content.civicplus.com/api/assets/va-portsmouth/{uuid}`
— but uuids are non-enumerable. The `www2` Laserfiche archive's SSL error is **not** the blocker:
`curl -kL` gets through to a **WebLink 9 sign-in wall** requiring credentials, so its pre-2023
minutes are behind authentication and out of reach.

### Tennessee — MEDIUM-HIGH (prior notes partly wrong)

**Correction: "county election commissions are frequently robots-blocked" is not supported.**
Shelby (`electionsshelbytn.gov`) and Putnam fetched cleanly. Two further corrections from live runs:
**Sumner did not "fail" — it is on a different host entirely.** `sumnertn.org/departments/election-commission`
404s; the real host is **`www.votesumnertn.org`**, HTTP 200 to plain curl with a browser UA, with a
complete municipal archive back to 2007 at `/november-general-and-city-elections/` (one summary PDF
per general). It was the single most productive source in that city's run. **All five of its summary
PDFs are image-only scans** — use the OCR path. Conversely **Sullivan does NOT serve results**:
`sullivancountytn.gov/departments/election-commission` and `/election-results` both 404 and
`sullivanelections.com` redirects to a login wall. And Putnam's useful form is
`putnamcountytn.gov/electionresults/{YYYY}-{MM}/` — the `/electionresults/` root itself 403s. The blocking is at the
**state** level — `sos.tn.gov` and `elections.tn.gov` return **403 on every path**.

**⚠ TENNESSEE TOWN & CITY IS INCOMPLETE, AND ITS OMISSIONS ARE SILENT (verified 2026-08-17).**
For Westmoreland, the `nov_23_2020.pdf` roundup lists **5 of the 7 candidates who actually ran and
omits the one who WON** (James Brian Smalling). Trusting it seats the wrong three aldermen for
2020-2024 and makes the 2022 unexpired-term races inexplicable. It also has **no Nov 2018 issue at
all** — the index jumps from `ttc_may_14_2018.pdf` to `ttc_jan_14_2019.pdf` (353 PDFs total; `?page=N`
returns identical content, so it is *not* paginated and there is nothing further to find).

**Treat TTC as a lead to corroborate, never as a canvass.** Its roundups look authoritative and
complete, which is precisely what makes a missing winner invisible. Always reconcile against a
county source before recording. Note this town is roughly the size of the one this rung was
previously credited with "solving outright" — that earlier success may itself have been silently
wrong.

**Tennessee Town & City is systematic, not incidental — and it is not a per-city lookup.** TTC
publishes a statewide roundup after *each* election date, titled e.g. "Municipal elections held in
80 cities." One article covers dozens to 200+ municipalities with candidate names and vote counts.
```
post-2021:  https://ttc.tml1.org/{YYYY}/{MM}/{DD}/{slug}
pre-2020:   https://ttc.tml1.org/sites/default/files/uploads/ttc-issues/{date-slug}.pdf
index:      https://ttc.tml1.org/tennessee-town-city-issues     (chronological, back to 2006)
```
Procedure: determine the city's election month from its charter, find the matching dated roundup,
then search within it for the city. Verified on 2019, 2022 (×2), 2024.

`mtas.tennessee.edu/directories/cities/{city}` verified 5/5 — but **current officials only, no
term dates**, and its "Next Election" field is unreliable (Memphis shows a date contradicting its
confirmed 4-year October cycle).

Nashville: use the city's own archive rather than the 403'd county route — **but the path
recorded here previously was wrong (corrected 2026-08-17); it 404s.** The working one is:
```
nashville.gov/departments/elections/election-results-and-statistics/election-results
  → /{YYMMDD}      per-cycle pages, e.g. 190801, 190912, 230803, 230914
```
Coverage back to 2008. Candidate tables render **client-side**, so these pages serve as cycle
sources but vote-level detail is not extractable by fetch. Metro Nashville's **ACFR carries an
`ELECTED OFFICIALS / Members of the Metropolitan Council` page dated "at June 30, YYYY"** naming
mayor, vice mayor and all 40 council seats — seven consecutive reports FY2019-FY2025 did the
entire 42-seat reconstruction, and it prints `Vacant` where a seat was unfilled. Metro council is **still 40 members** — the 2023 law reducing it to
20 was blocked by injunction.

**⚠ Cookeville "Aug/even" is wrong — it is QUADRENNIAL (corrected 2026-08-17).** All five
at-large seats are elected together in one `VOTE FOR 5` contest in **2018, 2022 and 2026 only**.
The Putnam County summaries for 2020-08-06 and 2024-08-01 carry Algood, Baxter and Monterey races
but **no Cookeville contest at all**, so 2019-2021 and 2023-2025 are holdover years, not gaps.
Mayor and vice-mayor are internal offices taken from roll-call titles — the election record alone
would have made the top vote-getter look like an elected mayor in both cycles, by coincidence.
`www.cookeville-tn.gov` robots.txt does **not** time out: it returns 200 and only name-blocks
Baiduspider/Yandex; the CivicPlus site search `/Search/Results?searchPhrase=` works to plain curl.

Calendars vary by charter: Cookeville Aug/**quadrennial** · Memphis Oct/4-yr (2019, 2023, 2027) · Nashville
Aug/odd · Westmoreland Nov/even. **Never assume a statewide TN date.**

**⚠ Bristol TN "Nov/even" is only half right (corrected 2026-08-17).** Bristol elected in **MAY of
ODD years through 2019-05-21** (terms beginning July 1, oath at the first July meeting), then moved
to **November of even years** (2022-11-08, 2024-11-05) with the oath at the first January meeting.
**The move EXTENDED two sitting terms** — three district seats ran to 2023-01-10 and two at-large
seats to 2025-01-07. Consequently **2020, 2021, 2023 and 2025 had no municipal election at all**:
structural holdover years, not gaps. Bristol is council-manager with **mayor and vice mayor selected
by the council from among its members**, and its seat scheme is mixed — three residency-district
seats (East, South, West) plus two at-large.

**`bristoltn.gov` is NOT robots-blocked to curl** despite the census note — the AgendaCenter dated
search plus `/AgendaCenter/ViewFile/Minutes/_MMDDYYYY-NNN` yielded the whole 2018-2026 archive.
**Sullivan County's election commission does NOT serve results**, contrary to the note above:
`sullivancountytn.gov/departments/election-commission` and `/election-results` both 404, and
`sullivanelections.com` redirects to a login wall. Route via *Tennessee Town & City*, which carried
full Bristol results with vote totals in its Nov 2022 special-election and Nov 2024 issues.
`heraldcourier.com` fetches by curl — article bodies are rot13-obfuscated for non-subscribers, but
**results tables and the JSON dataLayer publication dates are plain text**.

### Texas — MEDIUM (prior notes partly wrong)

**Confirmed: no statewide municipal source.** Verified against the SoS historical index and the
Texas State Library's own guidance. `results.texas-election.com` 403s.

**El Paso County is confirmed dead**: `epcountyvotes.com/election-archives` indexes 1998-2026 but
every link points at robots-blocked Clarity. **The city's own pre-Legistar clerk archive is the
route** — plain HTML, curl-fetchable, with district-labeled headers *and* live roll calls:
```
https://www2.elpasotexas.gov/municipal-clerk/agenda/{MM-DD-YY}/minutes.html
```
Working 2017-06-27 through 2020; 404 from 2023. **Caution: two files carry wrong internal dates** —
the 2020-01-07 minutes are headed "January 7, 2019" and the 2020-02-04 minutes "January 21, 2019".
Date documents from their content and cross-check, not from the header alone.

Work at county level. Vendor map from a single SoS PDF: **ES&S** — Bexar, El Paso, Jefferson,
Victoria; **Hart/Verity** — Hidalgo, Ector, Montgomery. Four route through Clarity (robots-blocked);
Ector and Montgomery publish PDFs directly:
```
https://www.ectorcountytx.gov/DocumentCenter/View/{id}/...
https://elections.mctx.org/results/{YEAR}_{MONTH}_{Description}.pdf
```
**The `{Description}` segment is NOT guessable — scrape the index instead:**
`https://elections.mctx.org/ElectionResults.asp` lists every canvass **2006-2026** as plain
server-rendered hrefs. **Extraction trap:** MCTX canvasses print candidate names **rotated 90°**, so
`pdftotext -layout` emits them in an order that does **not** match the vote columns — map by
**horizontal indent** (leftmost name to leftmost number). Reading in line order **reverses** at least
one known result. Verify the indent rule against a race with an independently known outcome first.
City races are usually **bundled into joint "City/School" county reports**, not itemized per city.
**In practice the county was never needed for any Texas city in this corpus** — every one was solved
city-side. Three city-side routes, all verified:

- **The CivicPlus site search returns full extracted PDF TEXT plus the DocumentCenter id** —
  `{city}/Search/Results?searchPhrase=<term>`. Every Mission canvass was found this way at **zero
  WebSearch cost**. Note `/DocumentCenter/View/{id}` must be enumerated with **GET, not HEAD** (HEAD
  404s on every id; GET exposes filenames via `Content-Disposition`).
- **The CivicPlus Archive Center, not the site search, is the ACFR route** — `/Archive.aspx?AMID={n}`
  lists the full series and `/ArchiveCenter/ViewFile/Item/{ADID}` fetches it. Victoria's `AMID=41`
  gave CAFR/ACFRs 2008-2023 with an `ELECTED OFFICIALS` page naming all seven seats **with district
  and term-expiry** — a complete annual snapshot, and the single most valuable Texas find of the run.
  The site search found only three recent copies.
- **Municode Meetings:** `?year=` and `?page=` **do not filter**; the working control is the Drupal
  exposed date filter (`date_filter[value][year|month|day]`). Minutes are plain PDFs on
  `mccmeetings.blob.core.usgovcloudapi.net/{tenant}/MEET-Minutes-{hash}.pdf`.

**Correction: the TML directory does not resolve name variants**, and more importantly it has
**no term dates and no history** — `directory.tml.org/profile/city/{id}` answers "who holds it
now," never "who held it in year X." IDs are non-guessable (Castle Hills 1387, Odessa 943,
Mission 895, Groves 1135); find via external search.

**Texas cities cancel uncontested elections outright** under Elec. Code §2.053 — the city passes an
ordinance cancelling the election and declaring the unopposed candidates elected, so **the city simply
does not appear on that date's county canvass**. One city was absent from three separate canvasses for
this reason. This is Texas's form of the unopposed-seat trap: **an absent city is not a missing cycle**.
Look for the cancellation ordinance, or fall back to an annual roster source.

**Three confirmed calendars, all different — never assume May.**
- **El Paso:** November of **even** years since 2018, 4-year terms, 2-term limit.
- **Groves:** November of **EVERY** year on **2-year** terms — Wards 1/3 in odd years, Mayor + Wards
  2/4 in even years. **Ten cycles in an 8-year panel.** Majority required, so a plurality forces a
  **December runoff** (two occurred in-window) and **incumbents hold over** past the November canvass
  — reading the canvass alone mis-dates those tenures.
- **Shenandoah:** first Saturday in **May, ANNUALLY**, 2-year terms — Mayor + Positions 1/5 in even
  years, Positions 2/3/4 in odd. **Eight cycles.**

- **Mission:** first Saturday in **May** through 2024-05-04, then **moved to the November uniform
  date** by a charter amendment adopted at that same election — so **there was no May 2026 election**
  and the 2022 class runs ~6 months long to 2026-11-03. **4-year** terms; the four cycles come from a
  **2-year stagger offset**, not short terms. Majority required, so **runoffs are routine** — the
  runoff seated the mayor in both 2018 and 2022.
- **Victoria:** **THREE-year** terms — not 2, not 4 — on the May uniform date. Districts 1-4 in 2018 /
  2021 / 2024; Mayor + Super Districts 5-6 in 2019 / 2022 / 2025. **2020, 2023 and 2026 have no city
  general election at all.**

- **Odessa:** **November of even years**, 4-year terms, majority-vote with December runoffs.
  Mayor + At-Large + Districts 1-5. The **At-Large seat did not exist before the 2018 election**
  (ACFR FY2017/FY2018 show six seats), which is why that election is titled "General/**Special**".

- **Castle Hills:** first Saturday in **May, EVERY year**, 2-year terms — Mayor + Places 2/3 in odd
  years, Places 1/4/5 in even. **Eight regular cycles** plus a 2019 special. Its mayor is a distinct
  office, not one of the five Places, which is why he votes only to break ties.

All seven Texas cities are now settled, and **no two share a calendar**. Given the above, **assume nothing**: of five confirmed
cities, no two share a calendar, terms run 2, 3 and 4 years, and two elect every single year.

Castle Hills' mayor **does not vote** except to break ties. **Groves' mayor occupies one of the five
seats** rather than presiding over four — its own council page says "The mayor, who serves as one
member of the Council", and the mayor moves, seconds and votes throughout the minutes. Its **Mayor Pro
Tem rotates by ward number** on an annual council vote.

### Arizona — MEDIUM (prior notes substantially wrong)

**Arizona structural facts settled per city (2026-08-17).** The mayor question splits sharply and
must never be assumed: **directly elected** in Cottonwood (4-year), Page (**2-year**), Chino Valley
(**2-year**), Show Low (4-year), Phoenix and Tucson; **council-selected** only in Sahuarita. Vice
mayors are council-designated everywhere observed. Show Low's 2018 vice-mayoralty was decided by
**drawing cards** (Allsop drew the deuce of clubs).

**Correction: "county sites are robots-blocked" is false as a blanket claim.**

| County | Status |
|---|---|
| Pima (Tucson, Sahuarita) | **Fully open**, robots.txt permits. `pima.gov/2865/Election-Results`, 2010-2024, explicit municipal coverage. Best AZ source. |
| Maricopa (Phoenix) | Page loads, but robots.txt **name-blocks ClaudeBot/GPTBot/PerplexityBot**. Fragile. |
| Navajo (Show Low) | **The 429 is gone (re-verified 2026-08-17):** `navajocountyaz.gov/506/Election-Results` returns HTTP 200 (161 KB) to plain curl with a browser UA and lists every municipal canvass back to **2004**. No `DocumentCenter` id enumeration needed. 2016 and 2018 canvasses are image-only scans — use the OCR path. |
| Coconino (Page) | Fully robots-disallowed. |
| Yavapai (Chino Valley, Cottonwood) | **BLOCKED, not unresolved (2026-08-17).** `yavapaiaz.gov` **and** the county's real elections host — a separate domain, **`yavapaivotes.gov`** (canvasses at `/files/assets/elections/v/1/documents/results/{year}/{slug}.pdf`) — both return an **Akamai 403 to curl with a browser UA on every path, including `/robots.txt`**. A WAF wall, not robots. **Route around it:** both corpus cities' own CivicPlus Archive Centers publish each canvass **resolution**, which incorporates the County Election Director's certification as Exhibit A — the county canvass without the county. |

**Phoenix runs its own municipal elections separately from Maricopa County** — its races are not
on the county portal.

**`{city}.suiteonemedia.com` is Show-Low-specific — and even there the hostname was WRONG
(corrected 2026-08-17).** `showlow.suiteonemedia.com` does **not exist** (`/`, `/web/home.html`,
`/Web/DocumentViewer.aspx`, `/Web/Player.aspx`, `/sirepub/*` all 404). The real host is
**`showlowaz.suiteonemedia.com`** — i.e. the tenant slug, not the city name — with direct endpoints:
```
/event/GetMinutesFile/Minutes?mid={id}
/event/GetAgendaFile/Agenda?aid={id}
```
It holds the entire **pre-CivicClerk archive (Dec 2018 → early 2023)** and was the most productive
source in that city's run: sweeping `mid` 1-300 yielded 142 council minutes and a meeting-by-meeting
membership series with no unobserved interval longer than ~6 weeks. Still confirmed 404 for
Cottonwood, Page and Sahuarita — do not guess it elsewhere, but **do try the tenant-slug form** where
a SIRE/suiteonemedia deployment is suspected.

**"August primary elects outright" is an *optional* procedure** under A.R.S. §9-821.01(D), adopted
per municipality — **and the corpus now splits both ways, so check each city rather than assuming.**

- **Adopted and load-bearing:** Cottonwood (all three seats in 2018, everything in 2020, the
  mayoralty plus two of three seats in 2024 decided in the primary and never on a November ballot)
  and Page (no mayoral race at all on the Nov 2024 canvass — Kidman won outright in July, 781-483).
- **Does NOT apply:** Tucson, whose August election is a **partisan party primary** — the canvass
  prints "DEM Council Member Ward 3" / "REP …", so it nominates rather than elects. Nor Phoenix,
  which runs a November general with a following **March** runoff.

**Arizona permanently moved its primary to the second-to-last Tuesday in JULY** (bill signed
2026-02-06), so the 2026 primary was **July 21**, not August — do not look for an August 2026 ballot.

Where the rule is adopted, **check the primary canvass FIRST**: a seat decided there never appears
in November, and recording a gap for its absence is wrong every time.

Sahuarita's mayor is **chosen among council members**, not elected. `azleague.org` is fetchable but
its officials data sits in an XLSX that could not be verified. `azauditor.gov` has a real
cities/towns report database whose filters WebFetch cannot drive.

News routes verified: `wmicentral.com`, `journalaz.com`. `lakepowellchronicle.com` 403s.

### California — MEDIUM

**⚠ THERE IS A STATEWIDE SOURCE — the "no statewide source" line was WRONG (2026-08-17).**
The **California Roster** (Secretary of State) carries an **"Incorporated City and Town Officials"**
section naming **Mayor, Vice Mayor and the full council for EVERY California city, annually**:
```
https://admin.cdn.sos.ca.gov/ca-roster/2019/02j-city-town.pdf
https://admin.cdn.sos.ca.gov/ca-roster/{YYYY}/cities-towns.pdf    # 2020,2021,2022,2024,2025,2026
```
2023 403s under every filename tried.

**⚠ IT IS A CORROBORATOR, NEVER A SPINE — and "check one year" is NOT sufficient.** Measured per
edition against dated resolutions for one city: **4 correct, 2 stale, 1 unverified.** **Staleness is PER-CITY, not per-edition** — the 2022 edition is a stale carry-over for one city and
demonstrably correct for another (matching that city's Dec-2021 reorganization and its FY2022 ACFR).
Never discard a whole edition; check the city you need. The worst case seen is a **2025 edition four
years stale**, reprinting the same block as 2022. That is not an off-by-one: a spot-check on 2024 or 2026 **passes** and then licenses a
completely wrong 2025 roster wearing an official state seal. The pattern suggests the SoS reprints the
last block received when a city does not report. **Verify every edition you rely on, or use it only to
fill a gap nothing else reaches.**

**⚠ COVERAGE IS NOT UNIVERSAL — check per city per year.** The data is *"provided to the Secretary of
State's Office by local jurisdictions"* (its own header), so **a city that does not submit is silently
absent**. Ripon is missing entirely from the 2019, 2020, 2021, 2022 and 2024 editions while its
alphabetical neighbours Rio Vista and Riverbank appear in all of them — a genuine omission, not a
page-break artifact. An absence in the Roster says nothing whatever about the city.

**Extraction traps.** It is **two-column**, and `pdftotext -layout` interleaves the neighbouring column
line-by-line — a naive `grep -A` on a city name returns the *adjacent* city's officials, and in one
case attached **Riverside's** legislative districts and 324,000 population to **Ripon** (real
population ~17,000). **Read the left column only, by offset.** **Grep case-INSENSITIVELY:** the 2019-2024 editions print
`CITY OF X` in caps while 2025-2026 use mixed case `City of X` — a case-sensitive search concludes the
city is absent from the two newest and most useful editions. Self-reported fields are also unreliable
— one edition gives a city's website with the wrong TLD — and it carries source typos, misprinting
"Suza Francina" as "Susan Francina".

Election *results* still have no statewide source — `sos.ca.gov` is state/federal only. Results are certified at **county**
level, and the portals differ by county:

- **Alameda** (Albany, Oakland): `alamedacountyca.gov/rovresults/{ELECTION_ID}/…`. IDs are small
  integers minted per election, **not derivable from the date**: **236 = Nov 2018, 241 = Nov 2020,
  248 = Nov 2022, 252 = Nov 2024, 257 = 2025-04-15 special, 259 = 2026-06-02 primary.**
  **The index filename varies per election** — 241 serves `indexA.htm`; 248 and 252 serve `index.htm`
  and **404 on `indexA.htm`**. Try both.
  **RCV has two mechanisms.** Older (2018): static `rcvresults_{nnn}.htm` pages linking a
  `Pass Report.pdf` per race. Newer (2022+): the page is JS-gated, but the real data sits at
  **`/rovresults/rcv/{ID}/{City}/{NNN-RaceCode}/RcvDetailedReport.xml`**, whose `Textbox21` field
  states "X is elected because all other candidates have been eliminated" — this **removes the JS
  gate entirely** and is the route to use.
  **Take the FINAL RCV round, never the first count.** One winner took a seat with **34.62%**
  first-choice support. **⚠ Alameda published no RCV tabulation at all for Nov 2020 (id 241)** —
  every path 404s — so three seats decided below 50% in round 1 must be sourced from the January
  inauguration roll call instead.
- **San Joaquin** (Ripon) and **Riverside** (Canyon Lake): shared Democracy Live vendor —
  `livevoterturnout.com/ENR/{county}caenr/{ID}/en/Index_{ID}.html`. IDs county-specific, not
  date-ordered.
- **Kern** (California City): per-city page `kernvote.com/elections/past-elections/california-city`.
- **Ventura** (Ojai) and **Sutter** (Yuba City): JS dropdown / folder-ID, **not deep-linkable** —
  go to the city's own site instead.

Consolidated onto even-year Novembers under SB 415. Mayor **rotates or is council-selected** in
Albany, Canyon Lake, Ripon, Yuba City; directly elected in Oakland (RCV) and California City.

**CVRA districting shifts mid-window — and the two cities DIFFER (corrected 2026-08-17).**
- **Yuba City — as previously stated.** Ordinance adopted **2022-02-01**, first applied 2022-11-08,
  members seated **2022-12-06**. Districts 1-3 = 2022/2026 group; 4-5 = 2024 group.
- **⚠ Ojai — the "2022" claim was WRONG.** Ojai transitioned by **Ordinance No. 889, adopted
  2018-12-11**. 2022 was post-census **redistricting**, not the CVRA transition. The boundary is
  **split**: **District 4** first elected 2020-11-03, seated **2020-12-15**; **Districts 1-3** first
  elected 2022-11-08, seated **2022-12-13**. Labelling 2019-2021 uniformly at-large puts District 4
  under the wrong scheme for a full year.

Oakland has been districted since 1988.

**Ojai's mayor is DIRECTLY ELECTED throughout — RESOLVED (2026-08-17), and the intuitive reading of
Measure L is BACKWARDS.** Measure L proposed *abolishing* the elected mayoralty and returning to
council rotation; **its defeat PRESERVED direct election** (Res. 22-62 certifies it "was not
carried"). The same proposition had already failed once as Measure J in 2018; **Measure A
(2014-11-04)** created the elected mayoralty. Ojai's council-selected office is the **Mayor Pro
Tempore**. **Live trap for a later panel: Measure M passed in 2022** (RCV plus reversion to at-large
from Nov 2024) but was **never implemented** — Nov 2024 still ran by district.

**`canyonlakeca.gov` is NOT robots-blocked in practice** — its `robots.txt` says `Disallow: /` but the
host served 200s with full HTML to plain curl with a browser UA on every path. Its AgendaQuick portal
is at **`public.destinyhosted.com/22696/agenda/`**, where
`default.cfm?mt=ALL&month={M}&year={Y}` returns a six-month window with **direct hrefs to minutes and
packet PDFs** under `/canyodocs/{year}/CC/{YYYYMMDD}_{id}/` — no JavaScript, covering 2016-2026. That
single endpoint closed the whole city at **zero searches**. **`cityofripon.org` is NOT (corrected 2026-08-17)** — HTTP 200 to
plain curl with a browser UA on `/robots.txt`, `/`, `/Archive.aspx` and `/AgendaCenter`, disallowing
only `/Search`, `/admin`, `/map`. **Ripon's council minutes are not in the AgendaCenter at all** (a
full sweep returned only Parks & Rec and committee minutes); they live on **IQM2/MinuteTraq** at
`riponcityca.iqm2.com`: `/Citizens/Calendar.aspx?From=&To=` → `Detail_Meeting.aspx?ID=` →
`FileOpen.aspx?Type=15&ID={doc}` (Type=12 is the 12-23 MB packet).

**⚠ Ripon's "Seat 1"-"Seat 5" are ROTATING CHAIR POSITIONS, not stable seats.** Seat 1 *is* the Mayor,
Seat 2 *is* the Vice Mayor, and every member's number changes each December. Copying them produces
five seats that silently permute every year — use election-cohort lineage labels instead.

**California is the FOURTH state with the unopposed rule** (Elections Code **§10229**, and appointment
in lieu of election): where candidates equal seats the council appoints them and the city vanishes from
the county canvass. Confirmed in Canyon Lake (2022, Res. 2022-48) and Ripon (2018, 2022 partial, 2024).
Joins Alabama, Georgia and Texas.

**California has the unopposed rule too:** where candidates equal seats the council **appoints in lieu
of election** and the city vanishes from the county canvass (Ripon 2018, 2022 partial, 2024 — in 2024
no Ripon council contest exists in the county file at all).

**Kern County (California City) is DEAD** — `kernvote.com` and `www.kerncounty.com` both 403 (Akamai)
to curl *and* WebFetch. That city was rebuilt entirely without the county, via its **Granicus
viewpublisher, which the census wrongly recorded as robots-blocked**:
`{tenant}.granicus.com/viewpublisher.php?view_id=1` served a 432-row archive to plain curl, and
`AgendaViewer.php?view_id=1&clip_id=N` returns each packet as a raw PDF whose cover page prints the
full council with the Mayor Pro Tem marked. **California City's mayor serves a TWO-year term.** **Query trap:** "Ripon" alone collides
heavily with Ripon, North Yorkshire, UK — always add "California".

### New Jersey — MEDIUM

**State PDFs contain zero municipal races** — verified; they carry only state/county contests and
turnout. Use county clerk canvass PDFs where they exist.

**⚠ The Camden URL pattern does NOT generalize across years — SCRAPE THE INDEX, never construct.**
`…/wp-content/elections/general{YEAR}/{YEAR}_General_Election_Canvasser.pdf` returns 200 **only for
2023, 2024 and 2025**. It 404s for 2015/2017/2019/2021: those use **hyphens** rather than
underscores, and **2019 sits one directory deeper** (`/general2019/results/2019-General-Election-Canvasser.pdf`).
The directory index 403s. The fix is a complete, curl-fetchable href index of every Camden canvass
**2000-2026**:
```
https://www.camdencounty.com/service/voting-and-elections/election-results/
```
**And the PDF pattern does not generalize across counties either:** Monmouth publishes **no canvass
PDFs at all** — `monmouthcountyvotes.gov` links only to Clarity for every election 2003-2026, and its
`wp-json` API is closed (HTTP 401). Where a county has no PDFs, use the Clarity JSON API in
cross-state finding 2.
Contest label: `Members of Council {Municipality} — Vote For {N}`. Each county hosts its own path;
this is one verified instance of a pattern class, not a statewide template. **Hudson's master list excludes Jersey City** — but that is a fact about one list, not a dead end:
`hudsoncountyclerk.org/elections-archives/` is a single page indexing the **complete** Hudson archive,
with Jersey City-specific canvass and candidate PDFs for every cycle, and it carried that entire city.
Hudson's `wp-json` is closed (HTTP 401), so the WordPress media technique does not work there.

**⚠ Hudson district-canvass PDFs print candidate names as ROTATED COLUMN HEADERS**, and `pdftotext`
emits them in an order that does **not** match the numeric columns — wrong in 4 of 8 contests checked.
Column order is **ballot-position order**, recoverable from the clerk's certified-candidates PDF,
which lists every ballot position and daggers incumbents. **Never read a name off those header
blocks.** Later cycles also publish *Summary Results by Contest* with names and totals on one line —
prefer those. (This is the same rotated-header trap seen in Montgomery County TX canvasses.)

`data.nj.gov/resource/gkt3-i954.json?$q={muni}` — NJ DCA Mayors Directory, **JSON API works**
(the HTML page is JS-only). Current mayor, county, term_start/term_end. No council, no history.

**Franklin Township in this corpus = Gloucester County — CONFIRMED three ways (2026-08-17):** the DCA
API returns four NJ Franklin Townships and only Gloucester's (dlgs 805, Franklinville 08322) has mayor
John Bruno; Resolution R-16-2024 reads "Township of Franklin, **County of Gloucester**"; and Gloucester
County Clarity carries "TOWNSHIP COMMITTEE - TOWNSHIP OF FRANKLIN" naming the same people as its
minutes. **Search decoy: `franklin-twp.org` is the HUNTERDON township** and surfaces for
"Franklin Township NJ election results". Structure: **5 at-large seats, 3-year staggered terms, 1-2-2
cycle**, mayor selected annually by the committee.

**Gloucester County's Clarity route is its ONLY route** — no canvass PDF exists in the Camden form.
Its **Previous Election Results page (`gloucestercountynj.gov/1252`) lists all 25 Clarity election ids
as plain links**, which solves the id-discovery problem outright. Nov 2023 = id 118787, ver 324803.
`electionsettings.json` did not expose a title or date — identify an election from its contest list.

Forms of government differ and determine mayor selection: Belmar (Small Municipality), Gloucester
Twp (Mayor-Council Plan B, confirmed verbatim in its reorganization resolutions — **7 at-large seats,
4-year terms, two classes: 4 seats in 2015/2019/2023, and 3 seats plus the mayor in 2017/2021/2025**;
the odd-year-only calendar is confirmed by the *absence* of any Gloucester Twp contest in the 2020,
2022 and 2026 Camden canvasses), Howell (Council-Manager — mayor still *directly elected* despite the
"Township" name), Montclair (Council-Manager — but its **mayor is DIRECTLY ELECTED**, confirmed 2026-08-17 from a
contested "Mayor-Montclair" ballot line on the Essex County canvass in both 2020 and 2024; the
council-appointed office is the **Deputy Mayor**, whose term the code leaves undefined, which is why
its rotation is disputed. **No runoffs** — a 2024 ward seat was won on a 45% plurality with none),
New Brunswick (Mayor-Council), Jersey City
(Mayor-Council, ward-based). **Franklin Twp is a traditional Township Committee — the committee
selects the mayor annually at its January reorganization**, so committee results alone won't tell
you who was mayor.

Dates vary: Belmar/Franklin/Gloucester Twp/New Brunswick partisan November; Howell November of
**even** years only; Gloucester Twp **odd** years only; Montclair nonpartisan **May**, all seats
concurrent every 4 years; Jersey City nonpartisan November with December runoffs.

**New Brunswick's council grew from 5 to 7 seats — mechanism and stagger established 2026-08-17.**
A **citizen petition** under N.J.S.A. 40:69A-190 (Ordinance O-032008, readings 2020-03-18 and
2020-04-01) put the charter question on the **2020-11-03** ballot; the new seats were first filled at
**2022-11-08** and seated **2023-01-01**. **The stagger was set by TWO separate contests on that one
ballot** — `Members of the City Council … Vote For 3` (4-year terms) and `Member of the City Council …
**Vote For 1**` (an **initial 2-year term**). Only one of the two new seats took a short term; missing
that second contest mis-dates the whole later stagger. Council size is not constant.

**The unlock there is the January reorganization agenda**, not the minutes: every year's
`COUNCIL DESIGNATION OF LIAISONS TO VARIOUS AUTHORITIES, BOARDS AND COMMISSIONS FOR {YEAR}` resolution
**names every member and prints their President/Vice-President titles** — a complete annual roster
spine in one document series.

`njlm.org`, `twp.howell.nj.us`, `cityofnewbrunswick.org` robots-blocked; `belmar.com` JS-walled.

### Georgia — MEDIUM

**No fetchable structured results.** Clarity is robots-blocked; `results.sos.ga.gov` is a JS SPA.

**⚠ `gacities.com` is MISLEADING on seat counts (2026-08-17, confirmed on two cities).**
Milledgeville's GMA page listed **ten names for a six-member council** by merging outgoing members
with incoming ones; Dublin's listed **eight names for a seven-seat body**, still carrying a member
who left 2025-12-31 while omitting his successor. Use it to confirm individuals, **never** to
establish council size.

**Georgia ACFR practicalities (from two cities).** Filenames frequently use several incompatible
conventions within one series — constructed URLs 404, and one embeds a `%C2%A0` — so **scrape the
finance page for real hrefs** rather than guessing. Watch for a **format regime change**: Dublin's
FY2012-FY2021 reports give an *unlabeled* org chart that *does* annotate "(Mayor Pro Tem)", while
FY2022+ give a *labeled* Ward/At-Large table that *drops* the annotation — so seat labels and
officer identity come from different eras of the same series. Every page is a **fiscal-year-end
(June 30) snapshot**, proven by one FY2021 report still showing a mayor who had left months
earlier. Budget documents carry an officials roster in some cities (Milledgeville) and not others
(Dublin) — check rather than assume.

**Georgia municipal audits are mirrored off-domain on the Carl Vinson Institute portal, open to
curl** — this is the state's best structured source and it routes around city-domain robots
blocks entirely:
```
https://ted.cviog.uga.edu/financial-documents/node/{id}     (Milledgeville = 532)
```
**No node lookup is actually needed** — files are directly constructible, though the URL is
unforgiving (the **doubled slash** and the **upper-case path segment** are both required):
```
https://ted.cviog.uga.edu/FINANCIAL-DOCUMENTS/sites/default/files//budgetdoc/financial-report/city-{slug}-fy{YYYY}-financial-report.pdf
```
Coverage is per-city and patchy — Richmond Hill has FY2020-FY2023 only, with FY2019/FY2024/FY2025
404. Some ACFRs **print post/district numbers explicitly**, which independently corroborates a
seat map derived from elsewhere.
Coverage FY2007-FY2024 plus budgets to FY2025. Each audit carries a **"List of Principal
Officials"** page naming mayor, mayor pro-tem and council. It confirmed a full 2019-2024
reconstruction name-for-name, including a year that printed the sixth council line as "Vacant".
**Use the Principal Officials page (as of fiscal year end), not the letterhead roster (as of
publication)** — they differ. The **budget** document is often what maps names to district or post
numbers.

**Georgia papers are more open than the registry implied.** The *Union-Recorder* does **not** 403
— it fetches cleanly by curl and is WordPress: `/search/?q=` 404s but `?s=<query>` works, and the
REST API works better: `/wp-json/wp/v2/posts?search=<term>&after=…&before=…&per_page=60&_fields=date,link,title`.
That took one city to **3 total WebSearches**. Caveat: CNHI syndication from sister papers
(Dalton, Valdosta, Moultrie) contaminates results — relevance-check every hit.

`gacities.com` (GMA) is the verified route for **current** rosters:
`https://www.gacities.com/gma-cities-districts/{city}/{id}` — Dublin 24376, Richmond Hill 65044,
Milledgeville 51492. No historical archive.

Historical rosters come from **local news**: Union-Recorder, Bryan County News, WSAV (use
`/amp/`), WTOC, 13WMAZ. Two handling notes: **WTOC and WSAV article bodies live in an Arc
Publishing JSON blob** — extract `"type":"text","content":"…"` rather than the rendered page,
which returns navigation chrome only. And **Bryan County News republishes undated archive
articles**: a search snippet presented a 2007 Post 3 race as 2019, which would have seated the
wrong person for four years. Verify an article's era from its internal details (a named runoff
date's day-of-week is decisive) before using it.

**⚠ The Courier Herald pattern previously recorded here was WRONG (corrected 2026-08-17).**
`CH-{Month DD, YYYY}.pdf` **404s for every date**. The working pattern uses hyphens, no comma and
no leading zero:
```
courierheraldtoday.com/wp-content/uploads/{YYYY}/{MM}/CH-{Month}-{D}-{YYYY}.pdf
```
Some issues carry a `-1` suffix. **More importantly its archive begins in 2024**, so it cannot
reach the 2019, 2021 or 2023 cycles at all — it is not a route to this panel's early years.
`/e-editions/` is a Pelcro paywall portal with no PDF links.

**County election pages are a dead end here:** `laurenscoga.org/258/Election-Results` 302-redirects
straight into Clarity (robots-blocked) and the host 403s curl.

Elections: **November of odd years only** (2019, 2021, 2023, 2025), runoffs 3-4 weeks later,
sometimes into December — search both months. **But cadence is per-charter, not statewide:**
Milledgeville is **quadrennial** — mayor and all six districts run concurrently in 2017, 2021,
2025, so **2019 and 2023 are holdover years with no city election at all**. Establish each city's
cadence before treating a missing odd-year cycle as a gap.

Seat naming differs by city: Richmond Hill "Post" (at-large), Milledgeville "District",
Dublin "Ward" 1-4 **plus** 3 at-large.

**Corpus correction confirmed: "Richmond city, Georgia" is Richmond Hill, Bryan County.**
**Query trap:** Wikipedia's "Dublin City Council election" articles are Dublin, **Ireland**.

### Massachusetts — MEDIUM

**`electionstats.state.ma.us` contains no municipal races at all** — verified by search returning
zero for Amherst. The Secretary's own "where do I find election results" page points there, which
is misleading for municipal researchers. DLS and the State Auditor name no officials either.

Only source: **city/town clerk archives**.
- Brockton: `brockton.gov/city-departments/elections-commission/` → `brockton.gov/wp-content/uploads/{year}/{month}/*.pdf` (`brockton.ma.us` 302s here). **"Fetchable" means WebFetch, NOT curl** — curl gets a blanket nginx 403 on all of `wp-json` and on many upload paths, while WebFetch succeeds on all of them. **The unlock is the WP media REST endpoint** via WebFetch: `wp-json/wp/v2/media?search=<term>&per_page=100&_fields=date,source_url,title` returns the whole elections tree back to **2003**, including files **not linked from the elections page at all** (`Nov-2019-Unofficial-Results.pdf` was findable no other way). Three of five in-panel cycles are **image-only scans** (CCITT Fax / JBIG2) — use the OCR path in the ladder; one needs 90° rotation for vertically printed labels
- Greenfield: **the URL recorded here was wrong (corrected 2026-08-17).**
  `.../elections_and_voting/election_results.php` returns 200 but is a **stub with no result
  links**. The live archive is `.../elections_and_voting/elections_results.php` — note the plural
  **"elections"** — and even that only reaches back to **March 2024**; no 2019/2021/2023 local
  results are hosted anywhere on the city domain. The working route is the *Greenfield Recorder*:
  **`recorder.com` is WordPress and fully open to curl** with a browser UA, bodies complete and
  unpaywalled, `/wp-json/wp/v2/posts?search=&after=&before=&per_page=` reaching back to at least
  2017. That alone reconstructed four cycles and nine mid-term changes. (Note the contrast with
  Amherst's WordPress outlet, where `search=` was near-useless and slug lookup was reliable — test
  both.) The Revize CMS repository sits at `cms5.revize.com/revize/greenfield/Document_Center/…`.
  Superseded stub: `greenfield-ma.gov/elections_and_voting/election_results.php`
- Amherst: **the "entirely robots-blocked" note was WRONG (corrected 2026-08-17).** `robots.txt`
  does carry `Disallow: /`, but the host serves everything to plain curl with a browser UA:
  `Archive.aspx?AMID=206` returns ~250 dated Town Council minutes links **in a single fetch**
  (2018-12 to 2025-06), plus `/ArchiveCenter/ViewFile/Item/{id}` and `/DocumentCenter/View/{id}`
  PDFs. The unlock is the plain-HTML site search **`/Search/Results?searchPhrase=`**, which located
  every certified results PDF. The React DocumentCenter folder API is genuinely unreachable — use
  the site search. `gazettenet.com` fetches full article bodies by curl; `amherstindy.org` is
  WordPress where `wp-json/wp/v2/posts?slug=` is reliable while `search=` is near-useless, and its
  meeting reports print attendance **with each councillor's district**

**Amherst before December 2018 is a category error.** The town had no Town Council — it had open
Town Meeting plus a 5-member Select Board. The 13-member council (3 at-large + 10 district) was
created by a charter adopted March 2018, first elected Nov 2018. Amherst has **no mayor**; its
Council President is chosen by the councilors.

**2-year terms** in Amherst and Brockton mean 4 cycles (2019, 2021, 2023, 2025). Greenfield's
mayor is 4-year (2019, 2023).

**Greenfield's council cadence is RESOLVED (2026-08-17) — the "ambiguity" was only bad phrasing.**
All 13 seats carry **4-year terms with half the council elected every 2 years** in November of odd
years; "four-year terms… elected biannually" means *biannually* describes the election and *four
years* the term. Precinct and at-large seats share one cadence:
- **Cohort A** — 2 at-large + Precincts 1-4 (6 seats): 2015 / 2019 / 2023
- **Cohort B** — 2 at-large + Precincts 5-9 (7 seats): 2017 / 2021 / 2025

Established three non-inferential ways: the council members page carries a **"Term expires 12/31"**
column splitting exactly along those cohorts (2027 vs 2029); the certified Nov 2025 results print
**zero ballots cast in Precincts 1-4**; and the 2023 ballot-position list contains Precincts 1-4
and no 5-9.

Clerk archives bundle **every** election including even-year state/federal — filter by contest
name, not by year parity.

**Massachusetts does NOT hide unopposed candidates** — unlike Alabama and Georgia (cross-state
finding 3b), an uncontested MA seat still appears on the certified results with full vote counts.
Verified on a district that ran uncontested in three consecutive cycles. **So in Massachusetts an
absent seat really is missing data** — do not suppress a gap on unopposed grounds here.

**Amherst's cadence is not what either obvious reading predicts (established 2026-08-17).** The
2018 ballot itself prints **"COUNCILOR (3 years)"**: the inaugural council served a transitional
**three-year** term, 2018-12-03 to 2022-01-03. The regular cycle is then **odd years** — 2021-11-02,
2023-11-07, 2025-11-04 — on 2-year terms. **There was no 2019 council election**; the 2019 town
election carried only School Committee, Housing Authority, Library Trustees and Elector of the
Oliver Smith Will. Even years have no town election at all. Amherst also **redistricted mid-panel**
(map adopted 2021-10-29, effective for 2023), so district numbers are discontinuous across 2023.

### South Dakota — MEDIUM (the "hardest state measured" framing does NOT hold everywhere)

**Sioux Falls was the cheapest city per seat-year in the entire 64-city corpus** — 8 searches, 80
seat-years — via the **OnBase Public Access JSON API** at `amv.siouxfalls.gov` (see SKILL.md
"Retrieval mechanics"). Its **Certificates of Election / Oaths of Office** saved query gives a dated
per-person seating record *including unopposed seats that never reach a ballot*, and its keyword
**value dataset** enumerates every officeholder the city has ever indexed — which proves a mid-term
check complete rather than merely exhausted. The legislative-audit, public-notice and
newspaper-proceedings routes were **never needed** there.

**⚠ `www.siouxfalls.gov` is 403 to both curl and WebFetch on every path including `/robots.txt`** —
Akamai. That kills the ACFR spine (finance pages live there). The separate `amv.` host is wide open.

**Unopposed-means-absent is confirmed in South Dakota too** (a fourth state): three cycles had seats
with no ballot line at all, recovered only from Certificates of Election.

**No centralized municipal results exist.** Confirmed absent at the Secretary of State and four
county auditors. Cities administer their own elections — **but "April" is not universal: Mitchell votes in JUNE**,
even years on the state primary date and odd years with the school election, a pattern holding
2020-2026 (not a COVID artifact). **Establish each city's month from its own canvass resolutions.**
Do not spend budget looking for a state or county results portal.

**⚠ South Dakota does not put UNOPPOSED municipal seats on the ballot at all** — confirmed in a
second city: every canvass there covers only the contested race while the July oath seats four or five
people. **Reading a canvass as the full slate manufactures three spurious gaps a year.** Take the oath
of office, not the canvass, as the roster.

**For a domain-move city, query Wayback on the OLD host.** `url={old-domain}&matchType=domain` returned
2,979 rows and 1,043 PDFs where the *current* domain returned **zero** — recovering a whole minutes
series **deleted from the live server** under a third filename convention that no amount of guessing
would have hit.

**SD canvass resolutions are unusually rich** where they exist — naming ward, term length, vote
totals, *and* the offices where only one petition was filed and the candidate was declared elected
without a contest. That last part is South Dakota's form of the unopposed rule, and it is heavy:
3 of 4 seats in one city's 2020 cycle, 2 of 5 in 2021, 2 of 4 in 2023.

**⚠ The SD legislative audit's "City Officials / December 31, {YEAR}" page can be a PUBLICATION-date
roster, not the Dec 31 snapshot it claims.** `Alcester City 2024.pdf` lists two members appointed in
**May and June 2025** and omits one who sat through April 2025 — the "runs ahead of its own fiscal
year" failure mode, in a South Dakota audit. **Prefer dated minutes wherever they exist.**

**⚠ The audit route is unreliable in SD — it failed on THREE of four cities tested.** Hot Springs
404s for 2018-2024 and its only report (2025) is a **private-CPA financial-statement audit with no
"City Officials" page at all**; the `/reports/` index 403s. Brandon's 2024 report *does* have one, so
the route is not dead — just unreliable enough that it cannot be planned around. For
Mitchell, `legislativeaudit.sd.gov/reports/City/Mitchell City {Year}.pdf` 404s for 2018-2023 and 2025,
and the one report that exists (2024) is a **bare financial-statement audit with no "City Officials"
page at all** — it opens at the auditor's report addressed generically "To the City Council". For
Alcester only 2024 exists and it is a publication-date roster, not the Dec 31 snapshot it claims.
Budget accordingly and prefer minutes.

**Best source: state legislative audit reports** (see cross-state table). Anchor points to
interpolate between, not a timeline — the index shows only the most recent report per city, older
years mostly 404 when guessed, and small towns are audited irregularly.

`sdmunicipalleague.org` 403s — unverified, not disproven. `sdpublicnotices.com` works but defaults
to a trailing 12 months. Statutory publication of proceedings in the official newspaper names
attendees, and a hyperlocal blog reprinting proceedings produced a 100% roster for one town at the
lowest cost of any city measured.

**⚠ The "~50% robots ceiling" for this state does NOT follow from the evidence (re-examined
2026-08-17).** Hartford's `robots.txt` was fetched and read in full: it returns HTTP 200 and carries a
genuine blanket `User-agent: * / Disallow: /` — so the block is real and must be honoured — **but there
is no year-scoped rule anywhere in the file.** The recorded 2019/2020-blocked-vs-2021/2023-fine
asymmetry cannot come from this file; it was tooling noise misread as policy.

**And the same file explicitly PERMITS `archive.org_bot` and `ia_archiver`**, so Wayback's copy of the
site was collected with the city's consent and is the **compliant** route in. Via CDX, Hartford turned
out to be **~100% recoverable, not ~50%**. SD municipal sites commonly whitelist the archive crawlers
— check for that before accepting any SD ceiling.
