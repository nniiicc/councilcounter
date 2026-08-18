# Escalation Ladder for Missing Election Cycles

## When to use this

Only against a **specific flagged cycle** — never against a whole city.

A flagged cycle is a `(city, election_date, seats)` unit that Step 4 could not source. Compute its
blast radius first - `seats_up x years until the next cycle`, e.g. 3 seats x 4 years = 12
seat-years - because it tells you what escalating is worth before you spend anything. This is a
decision input computed at query time, not a column.

Failure in this pipeline is almost never "this city is too small." It is "this one cycle is
missing, and the gap propagates forward until the next findable cycle." The same defect appeared
in three separate cities during development.

## The ladder

Work in order. Stop as soon as the cycle is fully sourced. Record which rung succeeded in
`run_log`, not on `cycles` — that feeds back into the state registry for every remaining city in
that state, but it is process metadata and does not belong in the data model.

### Rung 1 — State / county election portal
The registry's primary source, retried with alternate year-path formats. Some state portals cover
only recent years and 404 silently for older ones.

### Rung 2 — County clerk, registrar, or auditor canvass
Official canvass PDFs. Frequently search-indexed but robots-blocked; an indexed-but-unfetchable
canvass is a block, not an absence — record it and move on.

### Rung 3 — County incumbent lists, municipal league, trade press, state audit agency
**Try county filing-period incumbent lists and cities-and-towns rosters FIRST at this rung.**
They are not canvasses and carry appointment/resignation dates in Remarks fields — the one class
of official document that records mid-term change. Highest measured yield per token for small
municipalities.

Municipal league directories and trade papers publish statewide election tallies and annual
officer directories. This rung solved a 2,200-person town outright, and a state audit-report
archive was the single best verified source in the hardest state measured.

Also try the **state audit agency** here: municipal audit reports normally contain a governing-body
page listing mayor and council with term dates.

### Rung 4 — Local newspaper
**Before concluding a paper is blocked:** a 403 often yields to `curl -A "<browser UA>"`, and
failing that, syndication mirrors (yahoo.com and similar) of the same article usually fetch
cleanly. Find the paper's real search parameter — it is frequently not `q`.

The highest-yield rung in practice. Small-town election results are local news even when they are
nothing else. Search the specific paper by name; many rate-limit, so pace retries rather than
looping.

### Rung 5 — Statutory public notices
State press-association portals and legal-notice archives. Most states require municipalities to
publish council proceedings, which name attendees. Note that many of these portals default to a
trailing-12-month window and hide older material behind a separate archive search.

### Rung 6 — Minutes roll call
**This is where meeting minutes earn their place.**

Minutes do not tell you the election result. They tell you **who sat**, which is what the panel
actually needs. Find a meeting shortly after the cycle's seating date and read its attendance list.

In development this rung was decisive twice: it supplied a 2016 town council that exists in no
reachable election record, and independently confirmed a newspaper-sourced result in another city.

Practical notes:
- The minutes are often **not** on the portal you expect. One city's minutes lived on
  `{city}.suiteonemedia.com` while its CivicClerk portal 404'd. Search for the document, not the portal.
- Minutes typically give **surnames only** with courtesy titles, no wards, and no mayor in
  council-manager cities. Use them to establish *composition*, then resolve identities against the
  election record.
- Some PDFs are image scans with no extractable text — `pdftotext` returns a handful of bytes.
  **Try the AGENDA for the same meeting before reaching for OCR.** In one city every 2019 *minutes*
file was an image-only scan while the *agendas* in the same folder had a real text layer — and the
agenda's first-page header prints the full roster **with titles** (`MAYOR • … / VICE MAYOR • … /
COUNCILMEMBER • …`), which beats a surname-only roll call. One `pdftotext` call replaces a whole
`pdftoppm`+`tesseract` pass, and it is often the *better* document. Where minutes are scanned, check
the agenda first.

**Diff two independent annual series wherever you can.** A stale carry-over is invisible inside a
single series — one city's FY2020 audit was character-identical to FY2019 and silently hid a mid-term
vice-mayor change, which surfaced only when a second annual roster disagreed. Two series that agree
are strong evidence; one series alone can be confidently wrong for years.

**There is now a working OCR path; use it before recording `scanned_pdf`:**
  ```
  pdftoppm -r 300 -png <file.pdf> <prefix>
  tesseract <prefix>-1.png - --psm 4 -c preserve_interword_spaces=1
  ```
  `--psm 4` (single column of variable-size text) plus `preserve_interword_spaces` is what makes
  tabular roster and results layouts come out readable rather than scrambled. Verified recovering
  a town clerk's image-only **certified election results** — every name and vote total verbatim.
  Treat OCR'd text as **`medium`** confidence unless it is crisp and cross-checkable against
  another source, and read the output yourself rather than trusting a summary of it.
  **`pdftoppm` naming trap:** it writes `{prefix}-1.png` for short PDFs and `-001.png` only once the
  page count reaches three digits — so a hard-coded `-001` glob silently matches nothing and looks
  exactly like an OCR failure. Glob for `{prefix}-*.png`.
  **Orientation is a real trap:** some scans are fed upside-down and need `sips -r 180` first, while
  others are correctly oriented and are *destroyed* by the same rotation — the giveaway is mirrored
  output (`ssaulsng ON` for `No Business`). Try both orientations and keep the readable one. Where
  labels are printed vertically, rotate 90°. If `tesseract` still scrambles a page, rendering to PNG
  and reading the image directly also works.
  This path has now recovered five otherwise-lost cycles, including a county's **entire** run of
  summary PDFs, so attempt it before writing anything off. This is not confined to old
  minutes; one city's **official 2025 election results PDF** was a scan. **Workaround that
  worked:** find a secondary source that *cites* the scanned document and carries its numbers as
  text — in that case Wikipedia's raw wikitext, which quotes the official results and links the
  PDF. That is `medium` confidence, not `high`, but it beats recording the cycle as lost.

### Rung 6b — The NEXT organizational meeting, not just the one after the election
Where an internal office (presiding officer, mayor pro tem) is selected at an annual
organizational meeting, that meeting's minutes typically name **both the incoming and the
outgoing** holder in the gavel-exchange passage — **one document sources two years**.

**And when the January minutes come up empty, go forward a year, not sideways.** In one city the
election happened at a separate *Inauguration Ceremony* whose minutes are a distinct document, so
two Januaries carried no election at all — those years were recoverable only from the **following**
January's retrospective passage ("presented outgoing President X with a plaque"). An agent that
fetches only the January after each election will come up empty on exactly the years it most wants.

### Rung 7 — Everything else
Budget documents, adopted ordinances with signature blocks, comprehensive plans, audit reports,
grant applications, chamber of commerce pages, board and commission rosters.

### Terminal — Mark unrecoverable
Write a `gaps` row per lost seat-year with `reason` and `attempted` filled in — the latter is the
provenance of the negative result and is required. Log the full rung-by-rung trail in `run_log`.
An honest `unrecoverable` with a documented trail is a valid research output. A guessed roster is
not.

## Measured results

| Flagged cycle | Recovered | Winning rung | Seat-years |
|---|---|---|---|
| Show Low AZ 2018 | yes | 4 (newspaper), confirmed by 6 | 12 |
| Tazewell VA 2020 | yes | 3 (VPAP) | — |
| Tazewell VA 2016 | yes | 6 (minutes roll call) | 22 |

3 of 3 recovered. ~4,650 tokens per seat-year unlocked. Expect roughly 4 flagged cycles per 10
cities.

Small sample, and these were well-defined cycles. A cycle in a state with no accessible canvass
*and* no local paper may still terminate unrecovered — expect the ladder to fail sometimes, and
record it plainly when it does.
