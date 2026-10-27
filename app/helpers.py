from datetime import datetime, timezone
import sqlite3
from .config import DB_PATH


def now_utc_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def print_db_snapshot(limit: int = 20):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM reviews")
    total = cur.fetchone()[0]
    print(f"\n=== DB SNAPSHOT: reviews (total={total}) ===")

    cur.execute("""
        SELECT reviewId, placeTitle, branch_city, stars, publishedAtDate, substr(text,1,80)
        FROM reviews
        ORDER BY publishedAtDate DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()

    for rid, title, city, stars, dt, txt in rows:
        print(f"- {dt} | {title} | {city} | {stars}⭐ | {rid} | {txt}")

    print("=== END DB SNAPSHOT ===\n")
    con.close()
