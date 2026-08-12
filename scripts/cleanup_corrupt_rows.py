"""Remove rows whose stored 'content' is not article prose.

Background
----------
The retired ``google_finance`` source scraped news.google.com RSS, whose links
are opaque redirect stubs (``/rss/articles/CBMi...``). Those pages are empty JS
shells to a plain HTTP client, so extraction always failed and the scraper fell
back to storing the raw RSS summary markup. clean_text() then mangled that
markup into strings like::

    a hrefhttps:news.google.comrssarticlesCBMi... target_blankHeadlinea

Every such row also carries a ``sentiment_score`` and ``mentioned_*`` entity
lists computed over that string, so anything reading FinDB's analytics was
reading noise for those rows.

This script deletes those rows plus any row with empty content.

Usage
-----
    python scripts/cleanup_corrupt_rows.py --dry-run   # report only (default)
    python scripts/cleanup_corrupt_rows.py --apply     # delete, after backup
"""
import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "financial_news.db")

# Rows matching any of these are unusable. Kept as SQL so the script has no
# dependency on the application code.
CORRUPT_PREDICATE = """
    content IS NULL
    OR TRIM(content) = ''
    OR content LIKE 'a href%'
    OR content LIKE '%news.google.com%'
    OR content LIKE '<%'
    OR content LIKE 'http://%'
    OR content LIKE 'https://%'
"""


def summarize(conn):
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM financial_news").fetchone()[0]
    doomed = cur.execute(
        f"SELECT COUNT(*) FROM financial_news WHERE {CORRUPT_PREDICATE}").fetchone()[0]
    print(f"total rows:      {total}")
    print(f"corrupt rows:    {doomed}  ({100 * doomed / total:.1f}%)")
    print(f"rows remaining:  {total - doomed}\n")

    print("corrupt rows by source:")
    for src, n in cur.execute(
        f"SELECT source, COUNT(*) FROM financial_news WHERE {CORRUPT_PREDICATE} "
        "GROUP BY source ORDER BY 2 DESC"
    ):
        print(f"  {src:<22} {n}")

    print("\nsample of what will be deleted:")
    for src, snippet in cur.execute(
        f"SELECT source, SUBSTR(content, 1, 70) FROM financial_news "
        f"WHERE {CORRUPT_PREDICATE} AND TRIM(COALESCE(content,'')) != '' LIMIT 3"
    ):
        print(f"  [{src}] {snippet!r}")
    return total, doomed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="actually delete (default is a dry run)")
    ap.add_argument("--db", default=DB_PATH)
    args = ap.parse_args()

    if not os.path.exists(args.db):
        sys.exit(f"database not found: {args.db}")

    conn = sqlite3.connect(args.db)
    total, doomed = summarize(conn)

    if not doomed:
        print("\nnothing to do.")
        return

    if not args.apply:
        print("\n[dry run] re-run with --apply to delete these rows.")
        return

    backup = f"{args.db}.backup-{datetime.now():%Y%m%d-%H%M%S}"
    print(f"\nbacking up to {backup} ...")
    conn.close()
    shutil.copy2(args.db, backup)

    conn = sqlite3.connect(args.db)
    cur = conn.cursor()
    cur.execute(f"DELETE FROM financial_news WHERE {CORRUPT_PREDICATE}")
    deleted = cur.rowcount
    conn.commit()
    print(f"deleted {deleted} rows.")

    print("reclaiming space (VACUUM) ...")
    conn.execute("VACUUM")
    conn.commit()
    conn.close()
    print("done.")


if __name__ == "__main__":
    main()
