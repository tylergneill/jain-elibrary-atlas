# recon/

Research material from the 2026-10-07 reconnaissance that seeded this repo.
Evidence behind `../site-structure.md` and the sizing items in
`../scratch/todo.md`. Not maintained; kept so a figure can be re-derived rather
than re-guessed.

All scripts are **offline**: they read `data/metadata_cache/jainelibrary/`
(gitignored, ~100 MB, the five item endpoints at 500 rows a page) and write
nothing outside `notes/recon/`. Run from the repo root:

    python -I notes/recon/analyze_jel.py books       # fields, file types, sizes, categories
    python -I notes/recon/analyze_lang.py books manuscripts magazines articles audio
    python -I notes/recon/sizes_by_group.py          # total file sizes per language group

| File | What it is |
| --- | --- |
| `figures-2026-10-07.md` | the numbers as measured that day, both sites, with the Quantum catalog aggregates that exist nowhere else |
| `analyze_jel.py` | per-endpoint summary: file types, parsed sizes, classification, categories, languages → `summary_<endpoint>.json` |
| `analyze_lang.py` | language groups (any Sanskrit, Sanskrit-only, any Prakrit) from the `language` string, with OCR-docx availability |
| `sizes_by_group.py` | total file size per language group and file type, per endpoint and combined |
| `analyze_sample.py` | the first look at one 500-row page; superseded by the two above |
| `summary_*.json` | `analyze_jel.py` output for each endpoint |

The networked pull that produced the cache is not here (nothing that crosses
the network belongs in an Atlas); it is parked at
`rivulet/notes/scratch/jain-elibrary-metadata-pull.py`.

## `calibrate_docx.py`

Compares the API's `OCR docx` byte size against the plaintext length Quantum's
booktext route returned for the 20 items sampled on 2026-10-07 (the measured
lengths are hard-coded in the script; they exist nowhere else). Result: for
items above ~100 KB of docx, **1.5–2.1 plaintext characters per docx byte**
(median 1.67; 1.84 pooled), and ~1.2 Devanāgarī characters per byte on
Sanskrit-tagged items. Small items fall to 0.4–0.5 because a docx carries
~40–50 KB of fixed overhead. So docx bytes are a usable surface proxy for text
volume, with a floor to subtract — not a measurement.

## `ocr_compare.py`

Quantum's cleaned booktext against the library's own OCR Word file for the
same item, on five items that have both (fetched 2026-10-17 into
`data/ocr_docx_compare/`, apart from the real cache): 008422, 600178, 020470,
034357, 600400, one per accession era. Needs `data/text_extract/` and that
folder. Result: **the same scans, a different OCR pass.** Lengths agree to a
few percent (600400: 6% fewer characters, more words), but only 63–97% of
words match in order, through word division (`श्री हेमचंद्राचार्य` vs
`श्रीहेमचंद्राचार्य…`) and different misreadings; neither is clearly better.
Every library file's note says it was made on 2022-07-30.
