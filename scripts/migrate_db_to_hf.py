"""One-time cutover: move financial_news.db from git to a Hugging Face dataset.

Ordering matters. Untracking the database before Hugging Face holds a copy
would leave the next scheduled run with nothing to pull, and it would silently
start from an empty database. So this script refuses to untrack anything until
it has verified the upload by downloading it back and comparing row counts.

Usage:
    export HF_TOKEN=hf_...            # write token, from huggingface.co/settings/tokens
    python scripts/migrate_db_to_hf.py            # verify only, changes nothing
    python scripts/migrate_db_to_hf.py --untrack  # also stop tracking it in git
"""
import argparse
import os
import sqlite3
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hf_storage  # noqa: E402

DB = hf_storage.DB_FILENAME


def row_count(path: str) -> int:
    conn = sqlite3.connect(path)
    try:
        return conn.execute("SELECT COUNT(*) FROM financial_news").fetchone()[0]
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--untrack", action="store_true",
                    help="after verifying, stop tracking the DB in git")
    args = ap.parse_args()

    if not os.path.exists(DB):
        sys.exit(f"{DB} not found; run from the repository root")
    if not hf_storage.HF_TOKEN:
        sys.exit("HF_TOKEN is not set. Create a write token at "
                 "https://huggingface.co/settings/tokens and export it.")

    local_rows = row_count(DB)
    size_mb = os.path.getsize(DB) / (1024 * 1024)
    print(f"local database: {local_rows:,} rows, {size_mb:.1f} MB")
    print(f"target dataset: {hf_storage.HF_REPO_ID}\n")

    print("uploading ...")
    hf_storage.push_database(DB)

    print("\nverifying by downloading it back ...")
    with tempfile.TemporaryDirectory() as tmp:
        check = os.path.join(tmp, "verify.db")
        if not hf_storage.pull_database(check):
            sys.exit("FAILED: uploaded database could not be downloaded back")
        remote_rows = row_count(check)

    print(f"remote database: {remote_rows:,} rows")
    if remote_rows != local_rows:
        sys.exit(f"FAILED: row count mismatch (local {local_rows}, "
                 f"remote {remote_rows}). Nothing was untracked.")
    print("verified: local and remote row counts match.\n")

    if not args.untrack:
        print("Upload verified. Re-run with --untrack to stop tracking the "
              "database in git.")
        return 0

    print("removing the database from git tracking (the local file stays) ...")
    subprocess.run(["git", "rm", "--cached", DB], check=True)

    gitignore = ".gitignore"
    with open(gitignore, "r", encoding="utf-8") as fh:
        content = fh.read()
    if DB not in content:
        with open(gitignore, "a", encoding="utf-8") as fh:
            fh.write(
                "\n# Database lives in the Hugging Face dataset, not in git\n"
                "# (it exceeds GitHub's 100 MB per-file limit). See hf_storage.py\n"
                f"{DB}\n"
            )
        print(f"added {DB} to {gitignore}")

    print("\nDone. Commit the result:")
    print(f'  git commit -am "Move database to Hugging Face dataset"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
