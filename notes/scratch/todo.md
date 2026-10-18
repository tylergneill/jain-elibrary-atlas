# todo

The spine of the backlog: every open item. Decisions that closed an item live
in `CLAUDE.md` (scope, tiers, sources, the audit) and `notes/site-structure.md`
(how the two sites behave); figures live in the audit and the About page.

**Terms** (shared with the other Atlases, stated in rivulet's `CLAUDE.md`):
single-threaded, one request per 2 s start-to-start, contact-bearing UA, stop
on 429/5xx, resumable cache. The one login is the owner's, by hand, for the
library's OCR files only (`make library-login`).

## Text

- [ ] **Furniture audit.** Sample 50 extracted texts and list the recurring
      non-content lines the patterns miss (running headers, the
      "Shri Mahavir Jain Aradhana Kendra" variants OCR'd with Devanāgarī
      noise, which the Indic-character guard currently keeps).
- [ ] **Confirm whether the booktext route ignores the title segment.** If it
      does, URLs can be derived from `srno` alone.

## Scope and browsing

- [ ] **Badges on the main page** for the eLibrary-text books (owner
      reviewing, 2026-10-17). Proposed: "docx" → "OCR docx", and a tag for
      text that came from the library's login-gated file.
- [ ] **Any-Sanskrit as a third tier** (7,588 items, mostly "Sanskrit,
      Hindi"). The Prakrit tier is done; this one needs language
      identification inside Devanāgarī before a Sanskrit byte figure means
      anything, and the `language` convention shifted around 2023 (plain
      `Sanskrit` → `Sanskrit, Hindi`), so most recent accessions sit here.
- [ ] **Author-name fold**, mechanical only: the catalogue spells one person
      several ways ("Dipratnasagar, Deepratnasagar"; "Hemchandracharya" vs
      "Hemchandrasuri"). Fold obvious variants with a table; do not merge on
      guesswork.
- [ ] **Classification tokens as an AND-filter panel** in the Sanskrit
      Documents style — the library's tags as published, with only mechanical
      cleanup (trailing commas, comma-joined pairs; the audit lists the empty
      slots) and a short documented exclusion list for the format tokens
      (`Book_Devnagari`…) and internal codes (`A000`…). No subject fold.
- [ ] **The Āgama index.** `api/agam/` is 60,880 sutra rows pointing at
      mool/translation docx files by `sr_no`. Enumerating its distinct files
      (~120 requests) would give the canon's file list and the Prakrit mool
      texts; not yet pulled. Decide whether it is a branch or a separate axis.

## Acquisition

- [ ] **Promote the recon pull script** at
      `rivulet/notes/scratch/jain-elibrary-metadata-pull.py` into
      `rivulet/extract/jainelibrary/fetch_metadata.py`, behind the shared
      `http`/`pacing`/`cache`/`journal` machinery, with a shim here. Dedupe on
      `id` (ordering is not stable across pages — see `site-structure.md`).
- [ ] **Dedupe check**: 2 books ids were never seen across the 44 pages;
      refetch with a stable `ordering=` parameter if DRF exposes one
      (`?ordering=id` untested).
