.PHONY: clearance fetch-catalog parse-catalog fetch-text library-login fetch-ocr-docx extract-text count-sizes build changelog audit audit-update-about serve serve-fulltext

# ============================================================================
# Acquisition. NETWORKED; needs the private `rivulet` package (exit 2 without
# it). Run from an environment where it is installed:
#     pip install -e ../../rivulet[selenium]
# Terms, shared with the other Atlases: single-threaded, one request per 2s
# start-to-start, contact-bearing UA, stop on 429/5xx, atomic cache writes,
# resumable from the cache alone.
# ============================================================================

# Earn Cloudflare clearance for jainqq.org -> data/clearance.json. Opens a
# separate Chrome (its own profile under data/) which must stay VISIBLE until
# it clears. Session-lived; the fetchers re-earn it themselves when it lapses.
#   make clearance
#   make clearance ARGS="--check"          # is the saved cookie still live?
#   make clearance ARGS="--reset-profile"
clearance:
	python -m pipeline.clearance $(ARGS)

# The Quantum catalog, 34 pages of 1000 rows -> data/metadata_cache/jainqq/.
# ~34 requests. Cached pages are skipped; ARGS="--refresh" refetches.
fetch-catalog:
	python -m pipeline.fetch_catalog $(ARGS)

# Cached catalog pages -> data/catalogue.jsonl, one row per distinct srno, and
# a table of the language slices. No network.
parse-catalog:
	python -m pipeline.parse_catalog $(ARGS)

# One booktext JSON per catalogued item with text -> data/fulltext_cache/.
# Default slice is sanskrit-only (~2k items, ~1.2h at 2s). Resumable; Ctrl-C
# stops cleanly.
#   make fetch-text
#   make fetch-text ARGS="--languages sanskrit-only --limit 20"
#   make fetch-text ARGS="--languages any-sanskrit"
fetch-text:
	python -m pipeline.fetch_text $(ARGS)

# The library's own OCR Word files, for the tier items OCR'd after Quantum's
# text stopped (mid-2020 to mid-2022). Needs a jainelibrary.org account: the
# login is done BY HAND in the window `library-login` opens (its own profile
# under data/), which must stay open while the fetcher runs. The library caps
# downloads per day; the fetcher stops at the cap and resumes on the next run.
#   make library-login
#   make fetch-ocr-docx
#   make fetch-ocr-docx ARGS="--limit 5"
library-login:
	python -m pipeline.library_login $(ARGS)

fetch-ocr-docx:
	python -m pipeline.fetch_ocr_docx $(ARGS)

# ============================================================================
# Offline, from the cache.
# ============================================================================

# data/fulltext_cache/ -> data/text_extract/<srno>.txt, furniture removed,
# pages separated by form feeds. NEEDS rivulet (exits 2 without it); the
# rules it applies live here in pipeline/text_measure.py.
#   make extract-text
#   make extract-text ARGS="--transliterate"
extract-text:
	python -m pipeline.extract_text $(ARGS)

# data/fulltext_cache/ -> data/sizes.jsonl: raw / content / IAST bytes per
# item plus the script breakdown. Pure function of the cache; no rivulet.
# Transliteration dominates: ~15 min single-threaded for the Sanskrit-only
# slice, less with workers.
#   make count-sizes
#   make count-sizes WORKERS=4
WORKERS ?=
count-sizes:
	python -m pipeline.count_sizes $(if $(WORKERS),--workers $(WORKERS)) $(ARGS)

# The two catalogues + sizes -> docs/data/tree.json (and docs/VERSION).
build:
	python -m pipeline.build_tree $(ARGS)

# web_date -> docs/data/changelog.json, monthly, cumulative.
changelog:
	python -m pipeline.build_changelog $(ARGS)

# What the two catalogues get wrong, published to the About page, and every
# data-stat figure in its prose. Offline: reads docs/data/ and the text
# journal, so run it after `build` and `changelog`. Never mutates anything but
# its own region of docs/about.html; strict both ways about the data-stat tags.
#   make audit                  # report only, writes nothing
#   make audit-update-about     # ...and rewrite the About region and figures
audit:
	python -m pipeline.audit $(ARGS)

audit-update-about:
	python -m pipeline.audit --update-about $(ARGS)

# Serve docs/ on :8004. `serve-fulltext` also serves data/text_extract/ at
# /text/<srno> for the txt badge -- localhost only, never published.
serve:
	python serve_docs.py

serve-fulltext:
	python serve_docs.py --fulltext
