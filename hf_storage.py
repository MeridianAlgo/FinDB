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

``pull`` is deliberately forgiving: on a first run the repo or file may not
exist yet, and the scraper can start from an empty database. ``push`` is
strict, because silently failing to persist a run would lose that day's data.
"""
import argparse
import logging
import os
import sys

from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.errors import (
    EntryNotFoundError,
    HfHubHTTPError,
    RepositoryNotFoundError,
)

logger = logging.getLogger(__name__)

HF_REPO_ID = os.getenv("HF_DATASET_REPO", "MeridianAlgo/FinDB")
HF_TOKEN = os.getenv("HF_TOKEN")
DB_FILENAME = "financial_news.db"
REPO_TYPE = "dataset"


def _api() -> HfApi:
    return HfApi(token=HF_TOKEN)


def pull_database(dest: str = DB_FILENAME) -> bool:
    """Download the database from the dataset repo.

    Returns True if a database was fetched, False if none exists yet (a valid
    first-run state). Never raises for a missing repo/file.
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
            "This is expected on the first run.", HF_REPO_ID
        )
        return False
    except HfHubHTTPError as exc:
        logger.warning("Could not download database from %s: %s", HF_REPO_ID, exc)
        return False

    # hf_hub_download returns a cache path; copy so the app writes its own file
    # rather than mutating the shared cache blob.
    import shutil
    if os.path.abspath(path) != os.path.abspath(dest):
        shutil.copyfile(path, dest)

    size_mb = os.path.getsize(dest) / (1024 * 1024)
    logger.info("Pulled %s from %s (%.1f MB)", DB_FILENAME, HF_REPO_ID, size_mb)
    return True


def _ensure_repo() -> None:
    _api().create_repo(
        repo_id=HF_REPO_ID, repo_type=REPO_TYPE, exist_ok=True, private=False
    )


def push_database(src: str = DB_FILENAME) -> None:
    """Upload the database to the dataset repo. Raises on failure."""
    if not HF_TOKEN:
        raise RuntimeError(
            "HF_TOKEN is not set; cannot push. Add it as a repository secret."
        )
    if not os.path.exists(src):
        raise FileNotFoundError(f"{src} does not exist; nothing to push")

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
    args = parser.parse_args()

    try:
        if args.action == "pull":
            pull_database(args.db)
        elif args.action == "push":
            push_database(args.db)
            push_exports()
        else:
            push_exports()
    except Exception as exc:
        logger.error("%s failed: %s", args.action, exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
