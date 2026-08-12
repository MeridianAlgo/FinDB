"""Sync the SQLite database and exports with a Hugging Face dataset repo.

The database is no longer tracked in git: at ~5.6 KB/row with 90-day retention
it grows past GitHub's hard 100 MB per-file limit, at which point pushes are
rejected outright. It lives in a Hugging Face dataset instead, which also makes
the corpus directly consumable by anyone training on it.

The daily workflow does:

    python hf_storage.py pull     # fetch the DB so dedup sees prior URLs
    python scraper.py             # ... scrape, export, prune ...
    python hf_storage.py push     # upload DB + exports

Configuration (environment):
    HF_TOKEN            write token; required to push, optional to pull a
                        public dataset
    HF_DATASET_REPO     dataset repo id, default "MeridianAlgo/FinDB"

``pull`` tolerates exactly one thing: a dataset that has no database yet, which
is the genuine first-run state. Every other fetch failure raises, because
carrying on would let the scraper build a database from nothing and then upload
it over a healthy one. ``push`` is strict for the mirror-image reason -- failing
to persist a run silently would lose that day's articles -- and additionally
refuses to upload a database that has collapsed in size.
"""
import argparse
import logging
import os
import sqlite3
import sys

from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.errors import (
    EntryNotFoundError,
    HfHubHTTPError,
    RepositoryNotFoundError,
)

logger = logging.getLogger(__name__)

HF_REPO_ID = os.getenv("HF_DATASET_REPO", "MeridianAlgo/FinDB")
# An unset GitHub Actions secret arrives as "" rather than being absent, and an
# empty token builds an "Authorization: Bearer " header that the HTTP layer
# rejects outright. Normalise it to None so anonymous access is used instead.
HF_TOKEN = os.getenv("HF_TOKEN") or None
DB_FILENAME = "financial_news.db"
REPO_TYPE = "dataset"

# Written by pull, read by push, to catch a run that would replace a healthy
# dataset with a nearly empty one (see push_database).
STATE_FILE = ".hf_pull_state"

# Retention pruning legitimately removes rows each run (~1/90th at steady
# state), so only a collapse this large is treated as a fault.
MIN_RETAINED_FRACTION = 0.5


def _api() -> HfApi:
    return HfApi(token=HF_TOKEN)


def _row_count(path: str) -> int:
    """Number of stored articles, or 0 if the file is absent/unreadable."""
    if not os.path.exists(path):
        return 0
    try:
        conn = sqlite3.connect(path)
        try:
            return conn.execute("SELECT COUNT(*) FROM financial_news").fetchone()[0]
        finally:
            conn.close()
    except sqlite3.Error:
        return 0


def pull_database(dest: str = DB_FILENAME) -> bool:
    """Download the database from the dataset repo.

    Returns True if a database was fetched, False only when the dataset
    genuinely has no database yet (a valid first-run state).

    Any other failure raises. Continuing past a transient fetch error would let
    the scraper build a fresh database from nothing and then push it over a
    healthy one, so it is far better to abandon the run and keep the data.
    """
    try:
        path = hf_hub_download(
            repo_id=HF_REPO_ID,
            repo_type=REPO_TYPE,
            filename=DB_FILENAME,
            token=HF_TOKEN,
        )
    except (RepositoryNotFoundError, EntryNotFoundError):
        logger.warning(
            "No database found at %s yet; starting from an empty database. "
            "This is expected only on the first run.", HF_REPO_ID
        )
        _write_state(0)
        return False

    # hf_hub_download returns a cache path; copy so the app writes its own file
    # rather than mutating the shared cache blob.
    import shutil
    if os.path.abspath(path) != os.path.abspath(dest):
        shutil.copyfile(path, dest)

    rows = _row_count(dest)
    size_mb = os.path.getsize(dest) / (1024 * 1024)
    logger.info("Pulled %s from %s (%.1f MB, %s rows)",
                DB_FILENAME, HF_REPO_ID, size_mb, f"{rows:,}")
    _write_state(rows)
    return True


def _write_state(rows: int) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as fh:
        fh.write(str(rows))


def _read_state() -> int | None:
    try:
        with open(STATE_FILE, encoding="utf-8") as fh:
            return int(fh.read().strip())
    except (OSError, ValueError):
        return None


def _ensure_repo() -> None:
    _api().create_repo(
        repo_id=HF_REPO_ID, repo_type=REPO_TYPE, exist_ok=True, private=False
    )


def push_database(src: str = DB_FILENAME, force: bool = False) -> None:
    """Upload the database to the dataset repo. Raises on failure."""
    if not HF_TOKEN:
        raise RuntimeError(
            "HF_TOKEN is not set or is empty; cannot push. Add it as a "
            "repository secret (Settings > Secrets and variables > Actions)."
        )
    if not os.path.exists(src):
        raise FileNotFoundError(f"{src} does not exist; nothing to push")

    # Refuse to replace a healthy dataset with a collapsed one. Without this,
    # any path that leaves the scraper with a fresh database would quietly
    # destroy the corpus on the next upload.
    pulled = _read_state()
    current = _row_count(src)
    if not force and pulled and current < pulled * MIN_RETAINED_FRACTION:
        raise RuntimeError(
            f"Refusing to push: database has {current:,} rows but {pulled:,} "
            f"were pulled at the start of this run. That is a loss of "
            f"{100 * (1 - current / pulled):.0f}%, which looks like a fault "
            f"rather than retention pruning. Re-run with --force to override."
        )

    _ensure_repo()
    size_mb = os.path.getsize(src) / (1024 * 1024)
    logger.info("Pushing %s (%.1f MB) to %s ...", src, size_mb, HF_REPO_ID)
    _api().upload_file(
        path_or_fileobj=src,
        path_in_repo=DB_FILENAME,
        repo_id=HF_REPO_ID,
        repo_type=REPO_TYPE,
        commit_message="Update database",
    )
    logger.info("Pushed database to %s", HF_REPO_ID)


def push_exports(exports_dir: str = "exports") -> None:
    """Upload the exports directory. Non-fatal: the DB is the source of truth."""
    if not HF_TOKEN:
        logger.warning("HF_TOKEN not set; skipping exports upload")
        return
    if not os.path.isdir(exports_dir):
        logger.warning("No %s directory; skipping exports upload", exports_dir)
        return

    files = [f for f in os.listdir(exports_dir) if not f.startswith(".")]
    if not files:
        logger.info("No exports to upload")
        return

    try:
        _ensure_repo()
        _api().upload_folder(
            folder_path=exports_dir,
            path_in_repo=exports_dir,
            repo_id=HF_REPO_ID,
            repo_type=REPO_TYPE,
            commit_message="Update exports",
        )
        logger.info("Pushed %d export file(s) to %s", len(files), HF_REPO_ID)
    except HfHubHTTPError as exc:
        logger.error("Failed to upload exports (continuing): %s", exc)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["pull", "push", "push-exports"])
    parser.add_argument("--db", default=DB_FILENAME)
    parser.add_argument("--force", action="store_true",
                        help="push even if the database shrank sharply")
    args = parser.parse_args()

    try:
        if args.action == "pull":
            pull_database(args.db)
        elif args.action == "push":
            push_database(args.db, force=args.force)
            push_exports()
        else:
            push_exports()
    except Exception as exc:
        logger.error("%s failed: %s", args.action, exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
