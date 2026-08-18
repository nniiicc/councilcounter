"""Export the panel view to gui/src/data/panel.json for the GUI.

Run after any re-ingest; CI runs it on every deploy so the published site
always reflects the committed councilcounter.db.
"""

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent
DB = ROOT / "councilcounter.db"
OUT = ROOT / "gui" / "src" / "data" / "panel.json"

KEYS = ["city", "state", "year", "seat", "role", "person", "status", "confidence", "url"]


def main() -> None:
    """Read the panel view and write the GUI's data file."""
    con = sqlite3.connect(DB)
    rows = con.execute(
        """
        SELECT city, state, year, seat_label, role, person, status, confidence, source_url
        FROM panel ORDER BY state, city, year,
          CASE role WHEN 'mayor' THEN 0 WHEN 'vice_mayor' THEN 1 ELSE 2 END,
          seat_label, person
        """
    ).fetchall()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps([dict(zip(KEYS, r)) for r in rows]))
    print(f"wrote {len(rows)} rows to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
