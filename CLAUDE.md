# jain-elibrary-atlas

A browsable atlas over the **Jain eLibrary** collection (jainelibrary.org),
read through both of its faces: the library's own API and files, and
**jainqq.org** ("Jain Quantum"), its full-text search engine. One of the
`sagara-sangama` atlases. Renamed from `jain-quantum-atlas` on 2026-10-17,
once the library's own OCR files were fetched and Quantum stopped being the
only text source. A
`pipeline/` emits `docs/data/tree.json`; a single-page frontend in `docs/`
browses it.

This repo **hosts no text of its own.** It indexes metadata and structure and
links out to jainqq.org and jainelibrary.org.

Read `notes/scratch/todo.md` for what is open, and `notes/site-structure.md`
before touching either site. The figures in `notes/recon/` are from the
seeding day — re-derive, don't quote.

## Commands

| Command | Does |
|---|---|
| `make clearance` | **NETWORKED. NEEDS `rivulet`** (exits 2 without it). Cloudflare clearance for jainqq.org → `data/clearance.json`. Opens a separate Chrome; leave it visible |
| `make fetch-catalog` | **NETWORKED. NEEDS `rivulet`.** 34 catalog pages → `data/metadata_cache/jainqq/` |
| `make parse-catalog` | cached pages → `data/catalogue.jsonl` + the language-slice table (no network) |
| `make fetch-text` | **NETWORKED. NEEDS `rivulet`.** One booktext JSON per item with text → `data/fulltext_cache/<srno>.json`. `ARGS="--languages <selector>"`, default `sanskrit-only`; resumable |
| `make library-login` | **NEEDS `rivulet`.** Opens a Chrome with its own profile (`data/library_profile/`) on jainelibrary.org; the owner logs in by hand and leaves it open |
| `make fetch-ocr-docx` | **NETWORKED. NEEDS `rivulet` and the logged-in window.** The library's OCR Word file for each tier item Quantum has no text for → `data/ocr_docx_cache/<srno>.docx`, as served. Stops at the library's daily cap; resumable |
| `make extract-text` | **NEEDS `rivulet`** (exits 2 without it; nothing else does). Cache → `data/text_extract/<srno>.txt`, furniture removed, pages separated by form feeds. Seconds |
| `make count-sizes` | cache → `data/sizes.jsonl`: raw / content / IAST bytes, pages, script breakdown per item. Pure function of the cache, no rivulet. ~15 min single-threaded for the Sanskrit-only slice; `WORKERS=n` |
| `make build` / `make changelog` | caches → `docs/data/tree.json` / `changelog.json` (no network) |
| `make audit` | the Data Quality checks → a report; writes nothing. Offline, no rivulet |
| `make audit-update-about` | ...and rewrite the About page's AUDIT region and every `data-stat` figure |

**Every rule about the text lives in `pipeline/text_measure.py`** — the page
splitter, the furniture patterns (the digitising libraries' OCR'd stamps,
page numbers, the `________________` marker), the script counters. rivulet's
extractor imports them and only writes files, so `count-sizes` measures
exactly what `extract-text` would write, with or without rivulet installed.

The selectors (`all`, `sanskrit-only`, `any-sanskrit`, `any-prakrit`,
`sanskrit-or-prakrit`) and the has-text rule are defined once, in
`pipeline/parse_catalog.py`, which rivulet imports — so the fetch queue and
any count this Atlas publishes about a slice come from the same definition.

Run the networked targets from an environment with rivulet installed
(`~/venvs/sagara-sangama-311` on the seeding machine).

## `notes/` — structure, research, and tasks in flight

**The shape is the same in all five repos:**

    notes/*.md        non-trivial notes on structure -- why it is built this
                      way, what will bite you. NOT a record of how a decision
                      was reached or what the state of play was on some date.
    notes/<topic>/    folders of research material: samples, one-off analysis
                      scripts, measurements kept so a figure can be re-derived
                      rather than re-guessed. Each carries its own README.
    notes/scratch/    tasks in flight -- plans, scoped designs, measurements
                      under way, and the backlog itself.

**The lifecycle.** A new task is written into `scratch/`. When it finishes, any
insight worth keeping is **promoted** into a top-level note (or into a code
comment beside the thing it explains) and **the scratch file is deleted**.
Nothing is kept because it was expensive to write.

### When asked what's left

On "what do the notes say we need to work on" (or any variant), **read the
notes and answer from them.** `notes/scratch/todo.md` is the spine — every open
`- [ ]` item. Top-level notes are reference, not backlog.

### Two cautions

- **Don't cite a notes figure as fact — re-derive it.** Both sites change under
  us; the cache under `data/` is the only thing a figure can be checked against,
  and it is dated by its fetch.
- **Don't promote note prose into README or UI copy** without re-checking it.

## The contract is the Sanskrit tier, nothing else

What `build_tree` publishes -- and so what Sāgarasaṅgama reads -- is the
items whose catalogued `language` string is exactly `Sanskrit` and that are
books. "Books" absorbs two of the library's storage folders: "manuscripts",
which holds block prints and horizontal-format printed books (each flagged
`horizontal`), and Quantum's `agam` folder of sutra-level editions. Type is
a filter on what enters the tree and nothing more -- not an axis, not a
badge. Decided
2026-10-07: this is an Atlas about Sanskrit first, Prakrit second, and the
Gujarati, Hindi and English majority of the library is not what the
aggregator counts. The whole library is still built in memory and summarised
into `all_stats.library_count` / `library_text_count` /
`sanskrit_prakrit_count` / `any_sanskrit_count` for the About page, then
dropped from the tree.

**The Prakrit tier is in the tree as an option** (2026-10-17): the books whose
language string is Prakrit or Sanskrit-and-Prakrit (573, mostly the Āgama
canon) ride along flagged `prakrit: true`. Every axis node carries `stats`
(Sanskrit) and `stats_prakrit` (both); `all_stats` stays Sanskrit -- the
contract -- with `all_stats_prakrit` beside it, and the changelog has
`periods` and `periods_prakrit`. The reader chooses with an "include Prakrit"
pill (tree page, off by default, persisted) and a checkbox over the About
page's chart. Modelled on the Wikisource Atlas's "improperly categorized"
pill: two totals published, the reader picks. The About page's prose and
audits stay Sanskrit.

Two consequences worth knowing: the Sanskrit tier with text is exactly the
slice that has been fetched and measured, so `sized == text_count` and the
byte figures are complete rather than a floor; and the post-2022 convention
shift (`Sanskrit, Hindi`) means recent accessions mostly fall outside the
tier -- and Quantum's text for the tier had already stopped by then (the
newest item with one went online in mid-2020; its catalog runs to 2022), so
little that had text is lost.

## The About page's figures are generated, not typed

Every number in `docs/about.html` sits in a `data-stat` tag that
`make audit-update-about` rewrites, and the Data Quality lists are the region
between its AUDIT markers -- the sibling Atlases' arrangement, adopted
2026-10-17 (until then `about.js` computed both in the browser). **The tag is
strict both ways**: a tag naming a figure `audit.intro_stats()` does not
compute fails the run, and so does a computed figure with no tag. Run it after
every `build` and `changelog`. `about.js` now draws only the chart.

**Anything that defies expectation goes into the audit as a check**, not into
prose: if it should be fixed upstream it is published; if it is ours (a
counted text that measures empty) it prints to the console only.

## Two sources, one catalogue

jainelibrary.org and jainqq.org ("Jain Quantum") are the same organisation's
two faces over one catalogue, keyed by the same six-digit **`sr_no`**. They are
gated differently and carry different things, so the Atlas reads both:

| | jainelibrary.org | jainqq.org |
| --- | --- | --- |
| what it is | React SPA over an open Django REST API at `/api/` | Next.js full-text search engine |
| gate | metadata open; **file downloads need an account**; robots.txt disallows all | **Cloudflare managed challenge** on every HTML/JSON route; a real browser session passes |
| per-item metadata | rich: per-file `file_size` strings, `pages`, `classification`, `categories[]`, `language`, `script`, authors, publisher, year | thinner: `file_size`, `num_pages`, `classification` (comma list), `master_folder` |
| plaintext | "OCR docx" / "TOC docx" download entries — behind login | `/booktext/<Title>/<srno>` serves the **full OCR text**, page-delimited, no login |

**The division of labour is fixed by the gates.** Metadata comes from the
API (no login, no challenge, 500 per page). Text comes from Quantum's booktext
pages, which need a browser-earned clearance cookie but no account.

**One exception, decided by the owner 2026-10-17: the library's own OCR Word
files** for the tier items Quantum has no text for (the books OCR'd after
Quantum's text stopped in mid-2020, plus older ones whose Quantum booktext is
empty -- `build_tree.empty_booktexts`, which also catches pages holding only a
byte-order mark; the audit lists both). These need a jainelibrary.org account. The owner logs in **by hand**
in a Chrome that `make library-login` opens with its own profile under
`data/library_profile/`; `make fetch-ocr-docx` (rivulet) works through that
window and never handles the password or the session token. OCR files only,
nothing else behind the login; the library's daily download cap stops the run
and the next run resumes. The tree marks these texts `text: "elibrary"`
and the chart gives them their own colour.

**Items that have text are the items with a non-blank `file_size` in the
Quantum catalog** — a 22-item sample found the rule exact in both directions.
Treat it as a hypothesis the fetcher confirms, and record the first exception
in `site-structure.md`.

## Language is a string, not the array

The API's `languages[]` array folds the *script* in: a Sanskrit-only book
lists `Hindi` too because it is printed in Devanāgarī. The `language` string
(`"Sanskrit"`, `"Sanskrit, Hindi"`, …) is the honest field, and the `script`
field is separate. Group by the string; never by the array.

`classification` is mostly script too (`Book_Devnagari`, `Book_Gujarati`,
`Book_English`), with a long tail of typos (`Book_Englsih`, `Book_Guajrati`).
The 634 `categories[].slug` values are the finer axis, including per-Āgama
slugs, but ~5% of items carry two or more and some slugs are themselves
comma-joined pairs (`philosophy,-religion`). Normalise in the pipeline, as the
sibling Atlas does for its free-text `Category`; never in the frontend.

## Acquisition lives in rivulet

**No code that crosses the network belongs here.** Fetchers, the Cloudflare
clearance, and any liveness check go in `rivulet/extract/jainelibrary/` and
`rivulet/verify/jainelibrary/`, reached through a guarded `pipeline/fetch.py`
shim that exits 2 when the package is absent. The recon pull script is parked
at `rivulet/notes/scratch/jain-elibrary-metadata-pull.py` until that package
exists.

Terms, shared with the other Atlases and stated in rivulet's own `CLAUDE.md`:
single-threaded; start-to-start pacing, default 2s; stop rather than retry on
429/5xx; a contact-bearing User-Agent; cache written `.part` + rename;
resumable from the cache alone.

What stays here: parsing the caches, byte counting, `build_tree`, the
changelog, the audit, serving.

## Where things land

    data/metadata_cache/jainelibrary/   API pages, <endpoint>_pNNNN.json (recon pull, 2026-10-07)
    data/metadata_cache/jainqq/         Quantum catalog pages, catalog_pNNNN.json
    data/catalogue.jsonl                one row per distinct srno (make parse-catalog)
    data/fulltext_cache/<srno>.json     the booktext data route's JSON, as served
    data/text_extract/<srno>.txt        clean text, pages separated by \f (make extract-text)
    data/sizes.jsonl                    per-item bytes and script counts (make count-sizes)
    data/text_fetch_log.jsonl           every text fetch: bytes, chars, pages, errors
    data/clearance.json, clearance_profile/   the Cloudflare cookie and the Chrome profile that earned it

The same two text directories every Atlas uses. `data/` is gitignored.

**The fulltext cache is JSON with escaped Unicode**, so a file is ~2.5× the
text's character count in bytes (a 2.1 M-character book is 5.4 MB). It is
kept as served; `text_extract/` is where the decoded, de-furnitured text
goes, and byte counts belong to that stage, not to the cache.
