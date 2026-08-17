-- municipal-roster-panel schema
-- Design rule: the data model holds only evidentiary fields. Anything describing
-- HOW data was found lives in run_log, which is not part of the panel.

PRAGMA foreign_keys = ON;

CREATE TABLE cities (
  city_id         INTEGER PRIMARY KEY,
  city            TEXT    NOT NULL,
  state           TEXT    NOT NULL,
  fips            TEXT,
  gov_form        TEXT,               -- mayor-council | council-manager | commission | township
  seat_count      INTEGER,            -- council seats, excluding mayor
  seat_scheme     TEXT,               -- at-large | ward | position-numbered | mixed
  term_length     INTEGER,            -- years
  stagger_pattern TEXT,               -- free text: which seats in which cycles
  mayor_selection TEXT    NOT NULL,   -- elected | council-selected
  election_month  TEXT,
  archive_url     TEXT,               -- corrected URL from the census
  notes           TEXT,
  UNIQUE (city, state)
);

CREATE TABLE persons (
  person_id          INTEGER PRIMARY KEY,
  name_canonical     TEXT    NOT NULL,
  name_variants      TEXT,            -- JSON array of observed forms
  first_name_sourced INTEGER NOT NULL DEFAULT 0   -- 0 where only a surname was ever sourced
);

-- The unit of work. One row per EXPECTED election cycle, whether or not it was found.
CREATE TABLE cycles (
  cycle_id      INTEGER PRIMARY KEY,
  city_id       INTEGER NOT NULL REFERENCES cities(city_id),
  election_date TEXT    NOT NULL,
  seats_up      INTEGER,
  status        TEXT    NOT NULL CHECK (status IN ('sourced','flagged','unrecoverable')),
  source_url    TEXT,
  UNIQUE (city_id, election_date)
);
-- Blast radius (seats_up x years to next cycle) is COMPUTED at query time, not stored.
-- See the view `cycle_cost` at the bottom.

-- The substantive output. One row per person per seat per continuous span.
CREATE TABLE tenures (
  tenure_id        INTEGER PRIMARY KEY,
  city_id          INTEGER NOT NULL REFERENCES cities(city_id),
  person_id        INTEGER NOT NULL REFERENCES persons(person_id),
  seat_label       TEXT    NOT NULL,  -- 'Ward 3' | 'Position 5' | 'District 2' | 'At-Large' | 'Mayor'
  role             TEXT    NOT NULL CHECK (role IN
                     ('mayor','vice_mayor','council_member','alderman','commissioner','selectman')),
  start_date       TEXT    NOT NULL,  -- ISO 8601; day precision where known, else YYYY-01-01
  end_date         TEXT,              -- NULL = ongoing
  entry_mode       TEXT CHECK (entry_mode IN ('elected','appointed','succeeded','unknown')),
  exit_mode        TEXT CHECK (exit_mode IN
                     ('term_end','resigned','recalled','died','defeated','ongoing',
                      'elevated','unknown')),
  -- 'elevated' = vacated this seat by taking another office (vice mayor succeeding to
  -- the mayoralty, council president becoming acting mayor). Distinct from 'resigned':
  -- the person did not leave office, they moved up, and the vacancy is a mechanical
  -- consequence rather than a choice to depart. The corresponding row for the office
  -- they moved INTO carries entry_mode='succeeded'.
  source_url       TEXT    NOT NULL,  -- PROVENANCE, ENFORCED. No URL, no row.
  retrieval_method TEXT    NOT NULL CHECK (retrieval_method IN
                     ('state_portal','county_canvass','trade_press','audit_report',
                      'newspaper','public_notice','minutes_rollcall','municipal_league','other')),
  confidence       TEXT    NOT NULL CHECK (confidence IN ('high','medium','low')),
  cycle_id         INTEGER REFERENCES cycles(cycle_id),  -- NULL for appointments
  CHECK (end_date IS NULL OR end_date >= start_date)
);

-- Seat-years that were attempted and could not be sourced. These cannot live in
-- tenures (no person, no URL), so `attempted` carries their provenance instead.
CREATE TABLE gaps (
  gap_id     INTEGER PRIMARY KEY,
  city_id    INTEGER NOT NULL REFERENCES cities(city_id),
  year       INTEGER NOT NULL,
  seat_label TEXT    NOT NULL,
  reason     TEXT    NOT NULL CHECK (reason IN
               ('missing_cycle','robots_blocked','scanned_pdf','no_archive',
                'homonym_unresolved','budget_cap','vacant','other')),
  -- 'vacant' is NOT a research failure: the seat was lawfully empty and we know it,
  -- usually to the day. It lives here because a vacant seat-year has no person and
  -- so cannot live in `tenures`, but the panel reports it as its own status and it
  -- does not count against coverage. Everything else here is a failure to source.
  attempted  TEXT    NOT NULL,        -- what was tried and how it failed. REQUIRED.
  notes      TEXT,
  UNIQUE (city_id, year, seat_label)
);

-- PROCESS STATE. Not part of the data model. Exists so a multi-session run can resume.
CREATE TABLE run_log (
  entry_id   INTEGER PRIMARY KEY,
  city_id    INTEGER REFERENCES cities(city_id),
  cycle_id   INTEGER REFERENCES cycles(cycle_id),   -- NULL for city-level work
  step       TEXT NOT NULL CHECK (step IN
               ('registry','cycle_calendar','cycle_retrieval','midterm_check',
                'escalation','validation','export')),
  rung       INTEGER,                 -- 1-7, only meaningful when step='escalation'
  outcome    TEXT NOT NULL CHECK (outcome IN ('success','blocked','not_found','budget_cap')),
  tool_calls INTEGER,
  searches   INTEGER,
  detail     TEXT,
  logged_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE years (year INTEGER PRIMARY KEY);
INSERT INTO years (year) VALUES (2019),(2020),(2021),(2022),(2023),(2024),(2025),(2026);

CREATE INDEX idx_tenures_city   ON tenures (city_id);
CREATE INDEX idx_tenures_person ON tenures (person_id);
CREATE INDEX idx_tenures_dates  ON tenures (start_date, end_date);
CREATE INDEX idx_cycles_city    ON cycles  (city_id, status);
CREATE INDEX idx_gaps_city      ON gaps    (city_id, year);
CREATE INDEX idx_runlog_city    ON run_log (city_id, step);

-- ---------------------------------------------------------------------------
-- The flat panel: one row per (city, year, seat). Spans exploded, gaps unioned in
-- so the panel is complete rather than silently short.
-- A seat held by two people in one year yields TWO rows for that cell. Correct.
-- ---------------------------------------------------------------------------
CREATE VIEW panel AS
SELECT c.city, c.state, y.year, t.seat_label, t.role,
       p.name_canonical AS person,
       t.entry_mode, t.exit_mode,
       t.source_url, t.retrieval_method, t.confidence,
       'sourced' AS status
FROM tenures t
JOIN cities  c ON c.city_id   = t.city_id
JOIN persons p ON p.person_id = t.person_id
JOIN years   y ON y.year >= CAST(substr(t.start_date, 1, 4) AS INTEGER)
              AND y.year <= COALESCE(CAST(substr(t.end_date, 1, 4) AS INTEGER), 9999)

UNION ALL

SELECT c.city, c.state, g.year, g.seat_label, NULL,
       NULL,
       NULL, NULL,
       NULL, NULL, NULL,
       CASE WHEN g.reason = 'vacant' THEN 'vacant' ELSE 'unrecoverable' END
FROM gaps g
JOIN cities c ON c.city_id = g.city_id;

-- What a flagged cycle costs, computed rather than stored. Drives escalation triage.
CREATE VIEW cycle_cost AS
SELECT cy.cycle_id, c.city, c.state, cy.election_date, cy.status, cy.seats_up,
       cy.seats_up * COALESCE(
         (SELECT CAST(substr(MIN(n.election_date), 1, 4) AS INTEGER)
            FROM cycles n
           WHERE n.city_id = cy.city_id AND n.election_date > cy.election_date)
         - CAST(substr(cy.election_date, 1, 4) AS INTEGER),
         (SELECT MAX(year) FROM years) - CAST(substr(cy.election_date, 1, 4) AS INTEGER) + 1
       ) AS blast_radius_seat_years
FROM cycles cy
JOIN cities c ON c.city_id = cy.city_id;

-- Coverage summary for honest reporting.
-- pct_sourced measures the share of the KNOWABLE record that was recovered, so
-- 'vacant' seat-years are excluded from the denominator rather than counted as
-- misses. A council seat nobody held is a complete finding, not a failed search.
CREATE VIEW coverage AS
SELECT city, state,
       SUM(status = 'sourced')       AS seat_years_sourced,
       SUM(status = 'unrecoverable') AS seat_years_unrecoverable,
       SUM(status = 'vacant')        AS seat_years_vacant,
       SUM(confidence = 'low')       AS low_confidence_rows,
       ROUND(100.0 * SUM(status = 'sourced')
             / NULLIF(SUM(status IN ('sourced','unrecoverable')), 0), 1) AS pct_sourced
FROM panel
GROUP BY city, state;
