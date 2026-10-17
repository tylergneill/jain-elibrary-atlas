"""Where the pipeline reads from and writes to.

Paths resolve relative to this file, never to the working directory, so every
stage behaves the same wherever it is invoked from. Everything under `data/` is
gitignored working state; only `docs/data/` is published.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
DOCS_DIR = REPO_ROOT / "docs"
DOCS_DATA_DIR = DOCS_DIR / "data"

# jainqq.org -- the text face. Behind Cloudflare; see pipeline/fetch.py.
SITE_ROOT = "https://jainqq.org/"
CLEARANCE_PATH = DATA_DIR / "clearance.json"
CLEARANCE_PROFILE_DIR = DATA_DIR / "clearance_profile"

# The catalog, one JSON file per page as the site served it, and the one-row-
# per-item file parsed from it (the scrape list for the text tier).
CATALOG_CACHE_DIR = DATA_DIR / "metadata_cache" / "jainqq"
CATALOG_LOG_PATH = DATA_DIR / "catalog_fetch_log.jsonl"
CATALOGUE_PATH = DATA_DIR / "catalogue.jsonl"

# jainelibrary.org -- the metadata face. Open REST API, no clearance. Fetched
# by the recon pull on 2026-10-07; its fetcher is not yet in rivulet.
API_CACHE_DIR = DATA_DIR / "metadata_cache" / "jainelibrary"

# The library's own OCR Word files, for the items OCR'd after Quantum's text
# stopped (mid-2020 to mid-2022). Fetched through a Chrome the owner logs in to
# by hand (`make library-login`); kept as served, text derived offline.
LIBRARY_PROFILE_DIR = DATA_DIR / "library_profile"
OCR_DOCX_CACHE_DIR = DATA_DIR / "ocr_docx_cache"    # <srno>.docx as served
OCR_LOG_PATH = DATA_DIR / "ocr_fetch_log.jsonl"
OCR_SIZES_PATH = DATA_DIR / "ocr_sizes.jsonl"       # make count-sizes, the docx half

# The two directories every Atlas shares.
FULLTEXT_CACHE_DIR = DATA_DIR / "fulltext_cache"    # what the site served
TEXT_EXTRACT_DIR = DATA_DIR / "text_extract"        # clean text derived from it
TEXT_LOG_PATH = DATA_DIR / "text_fetch_log.jsonl"
SIZES_PATH = DATA_DIR / "sizes.jsonl"               # make count-sizes

TREE_PATH = DOCS_DATA_DIR / "tree.json"
CHANGELOG_PATH = DOCS_DATA_DIR / "changelog.json"
