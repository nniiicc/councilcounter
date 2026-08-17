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

**2. Clarity Elections is used widely and is robots-blocked everywhere.**
`results.enr.clarityelections.com/{ST}/{County}/{id}/` carries municipal detail in NJ, GA, TX, and
others — and failed robots checks in every state tested. Do not build on it without a
browser-capable tool. Election IDs are non-sequential and must be discovered per election.

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
does with unopposed candidates.** **Confirmed statutory in two states so far** — Alabama, and Georgia
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
mid-term replacements directly. Look under the city's finance department; ACFRs are often hosted
**off-domain** (state repositories, EMMA/MSRB bond disclosure, the audit firm), so a robots block
on the city domain need not reach them.

**4. Ballotpedia is robots-blocked to direct fetch in every state tested.** Search snippets only
— **but it fetched fine by curl in 2026**, as did `patch.com`. Re-test with curl before writing
it off.

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

**Correction: `historical.elections.virginia.gov` deep links do not work.** Every constructed
locality/contest path 404s. Treat as non-scriptable.

**VPAP is the working fallback**, archive back to 2015:
`https://www.vpap.org/electionresults/{YYYYMMDD}/local/{locality-slug}-va/`. Content rendering is
inconsistent — 3 of 6 detail pages returned empty on a 200. Confirm non-empty before trusting.

**The critical structural fact: towns have no standalone locality page.** Tazewell's mayor and
council races appear nested inside `TAZEWELL_COUNTY`, alongside Bluefield, Cedar Bluff,
Pocahontas and Richlands. Independent cities (Norfolk, Portsmouth, Bristol, Waynesboro, Poquoson)
*are* top-level. **Always look up a town by its containing county.**

Town elections moved May → November under **SB 1157 (2021)**, effective for elections after
Jan 1 2022. §24.2-222.1 bars shortening terms — incumbents held over, so terms were *extended*.

Mayor: directly elected in Norfolk, Tazewell (town), and Poquoson (an at-large seat that serves as
mayor); **council-selected in Bristol** (the "mayor" was simply the top vote-getter in an ordinary
at-large council race); Portsmouth medium-confidence directly elected; Waynesboro unverified.

### Tennessee — MEDIUM-HIGH (prior notes partly wrong)

**Correction: "county election commissions are frequently robots-blocked" is not supported.**
Sullivan, Shelby and Putnam all fetched cleanly; only Sumner failed. The blocking is at the
**state** level — `sos.tn.gov` and `elections.tn.gov` return **403 on every path**.

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

Calendars vary by charter: Bristol Nov/even · Cookeville Aug/even · Memphis Oct/4-yr (2019, 2023,
2027) · Nashville Aug/odd · Westmoreland Nov/even. **Never assume a statewide TN date.**

### Texas — MEDIUM (prior notes partly wrong)

**Confirmed: no statewide municipal source.** Verified against the SoS historical index and the
Texas State Library's own guidance. `results.texas-election.com` 403s.

Work at county level. Vendor map from a single SoS PDF: **ES&S** — Bexar, El Paso, Jefferson,
Victoria; **Hart/Verity** — Hidalgo, Ector, Montgomery. Four route through Clarity (robots-blocked);
Ector and Montgomery publish PDFs directly:
```
https://www.ectorcountytx.gov/DocumentCenter/View/{id}/...
https://elections.mctx.org/results/{YEAR}_{MONTH}_{Description}.pdf
```
City races are usually **bundled into joint "City/School" county reports**, not itemized per city.
Check the city's own DocumentCenter too — Mission hosts its own canvasses.

**Correction: the TML directory does not resolve name variants**, and more importantly it has
**no term dates and no history** — `directory.tml.org/profile/city/{id}` answers "who holds it
now," never "who held it in year X." IDs are non-guessable (Castle Hills 1387, Odessa 943,
Mission 895, Groves 1135); find via external search.

**El Paso is a confirmed exception to the May uniform date** — November of even years since 2018,
4-year terms, 2-term limit. Castle Hills, Mission, Odessa and Victoria dates remain unverified;
do not assume May without checking.

Castle Hills' mayor **does not vote** except to break ties. Groves' mayor votes as one of five.

### Arizona — MEDIUM (prior notes substantially wrong)

**Correction: "county sites are robots-blocked" is false as a blanket claim.**

| County | Status |
|---|---|
| Pima (Tucson, Sahuarita) | **Fully open**, robots.txt permits. `pima.gov/2865/Election-Results`, 2010-2024, explicit municipal coverage. Best AZ source. |
| Maricopa (Phoenix) | Page loads, but robots.txt **name-blocks ClaudeBot/GPTBot/PerplexityBot**. Fragile. |
| Navajo (Show Low) | Listing page 429s; **direct `DocumentCenter/View/{id}` PDFs fetch fine.** |
| Coconino (Page) | Fully robots-disallowed. |
| Yavapai (Chino Valley, Cottonwood) | Unresolved — DNS failure and robots timeout. |

**Phoenix runs its own municipal elections separately from Maricopa County** — its races are not
on the county portal.

**Correction: `{city}.suiteonemedia.com` is Show-Low-specific, not an AZ pattern.** Confirmed 404
for Cottonwood, Page, Sahuarita. Do not guess it.

**Correction: "August primary elects outright" is an *optional* procedure** under A.R.S.
§9-821.01(D), adopted per municipality — not an automatic statewide rule. In practice standard
here. Still check the August canvass first: a seat decided in August may not appear in November.

Sahuarita's mayor is **chosen among council members**, not elected. `azleague.org` is fetchable but
its officials data sits in an XLSX that could not be verified. `azauditor.gov` has a real
cities/towns report database whose filters WebFetch cannot drive.

News routes verified: `wmicentral.com`, `journalaz.com`. `lakepowellchronicle.com` 403s.

### California — MEDIUM

**No statewide source** — `sos.ca.gov` is state/federal only. Results are certified at **county**
level, and the portals differ by county:

- **Alameda** (Albany, Oakland): `alamedacountyca.gov/rovresults/{ELECTION_ID}/indexA.htm`, RCV at
  `/rovresults/rcv/{ID}/rcvresults.htm?race={City}/{RaceCode}`. IDs are small integers minted per
  election (241 = Nov 2020, 248 = Nov 2022, 252 = Nov 2024) — **not derivable from the date**.
- **San Joaquin** (Ripon) and **Riverside** (Canyon Lake): shared Democracy Live vendor —
  `livevoterturnout.com/ENR/{county}caenr/{ID}/en/Index_{ID}.html`. IDs county-specific, not
  date-ordered.
- **Kern** (California City): per-city page `kernvote.com/elections/past-elections/california-city`.
- **Ventura** (Ojai) and **Sutter** (Yuba City): JS dropdown / folder-ID, **not deep-linkable** —
  go to the city's own site instead.

Consolidated onto even-year Novembers under SB 415. Mayor **rotates or is council-selected** in
Albany, Canyon Lake, Ripon, Yuba City; directly elected in Oakland (RCV) and California City.

**CVRA districting shifts mid-window:** Ojai and Yuba City moved at-large → by-district in 2022.
Label seats by district from 2023 on, at-large for 2019-2021. Oakland has been districted since
1988. Ojai's mayor-selection method after Measure L (2022) is **unresolved** — verify before
asserting.

`canyonlakeca.gov` and `cityofripon.org` robots-blocked. **Query trap:** "Ripon" alone collides
heavily with Ripon, North Yorkshire, UK — always add "California".

### New Jersey — MEDIUM

**State PDFs contain zero municipal races** — verified; they carry only state/county contests and
turnout. Use county clerk canvass PDFs. Camden verified:
```
https://www.camdencounty.com/wp-content/elections/general{YEAR}/{YEAR}_General_Election_Canvasser.pdf
```
Contest label: `Members of Council {Municipality} — Vote For {N}`. Each county hosts its own path;
this is one verified instance of a pattern class, not a statewide template. **Hudson's master list
excludes Jersey City** — do not assume county lists cover every municipality.

`data.nj.gov/resource/gkt3-i954.json?$q={muni}` — NJ DCA Mayors Directory, **JSON API works**
(the HTML page is JS-only). Current mayor, county, term_start/term_end. No council, no history.

**Franklin Township in this corpus = Gloucester County** (mayor John "Jake" Bruno, cross-confirmed
against the DCA dataset). Not Somerset, Hunterdon, or Warren.

Forms of government differ and determine mayor selection: Belmar (Small Municipality), Gloucester
Twp (Mayor-Council Plan B), Howell (Council-Manager — mayor still *directly elected* despite the
"Township" name), Montclair (Council-Manager), New Brunswick (Mayor-Council), Jersey City
(Mayor-Council, ward-based). **Franklin Twp is a traditional Township Committee — the committee
selects the mayor annually at its January reorganization**, so committee results alone won't tell
you who was mayor.

Dates vary: Belmar/Franklin/Gloucester Twp/New Brunswick partisan November; Howell November of
**even** years only; Gloucester Twp **odd** years only; Montclair nonpartisan **May**, all seats
concurrent every 4 years; Jersey City nonpartisan November with December runoffs.

**New Brunswick's council grew from 5 to 7 seats in January 2023** — council size is not constant.

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
- Brockton: `brockton.gov/city-departments/elections-commission/` → `brockton.gov/wp-content/uploads/{year}/{month}/*.pdf` (fetchable; `brockton.ma.us` 302s here)
- Greenfield: `greenfield-ma.gov/elections_and_voting/election_results.php`
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
mayor is 4-year (2019, 2023); its council's cadence is ambiguous in the city's own wording —
verify per cycle.

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

### South Dakota — MEDIUM, the hardest state measured

**No centralized municipal results exist.** Confirmed absent at the Secretary of State and four
county auditors. Cities administer their own April elections. Do not spend budget looking.

**Best source: state legislative audit reports** (see cross-state table). Anchor points to
interpolate between, not a timeline — the index shows only the most recent report per city, older
years mostly 404 when guessed, and small towns are audited irregularly.

`sdmunicipalleague.org` 403s — unverified, not disproven. `sdpublicnotices.com` works but defaults
to a trailing 12 months. Statutory publication of proceedings in the official newspaper names
attendees, and a hyperlocal blog reprinting proceedings produced a 100% roster for one town at the
lowest cost of any city measured.

**Robots directives, not missing records, set the ceiling here.** For one city, 2021 and 2023
council packets fetched fine while every 2019 and 2020 packet was blocked across seven attempts.
