# jain-elibrary-atlas

A more accessible interface for the Sanskrit books of the
[Jain eLibrary](https://jainelibrary.org), one of the
[`Sāgarasaṅgama`](https://github.com/tylergneill/sagara-sangama) Atlases.
(Formerly `jain-quantum-atlas`: it began from [jainqq.org](https://jainqq.org),
"Jain Quantum", the library's full-text face, and now reads both.)

Indexes metadata and structure; hosts no text of its own. Every item links
back to its Jain Quantum page, and to jainelibrary.org where the two
catalogues meet, for the content itself.

**Seeded 2026-10-07; acquisition works, nothing is built yet.** `CLAUDE.md`
has the architecture and the two-site split; `notes/site-structure.md` what
the sites taught us; `notes/scratch/todo.md` the backlog; `notes/recon/` the
seeding-day figures.

# what the collection is

The Jain eLibrary is an online library of Jain literature run by JAINA's
education arm: scanned books, manuscripts, periodical issues and their
articles, audio, and a sutra-level index of the Āgama canon, ~33k items on
Quantum's catalog. Most of it is Gujarati and Hindi; the Sanskrit and Prakrit
minority (~6k items) is what this Atlas is primarily for. Jain Quantum is the
same organisation's search engine over that catalogue, and serves each item's
OCR plaintext on a public page; jainelibrary.org holds the richer metadata
behind an open API, with the files themselves behind a login. Text comes from
Quantum's public pages, and, for the books OCR'd after Quantum's text stopped,
from the library's own OCR files, fetched with an account.

# how it works

A `pipeline/` will emit `docs/data/tree.json`; a single-page frontend in
`docs/` will browse it. The corpus is our own fetch, kept under gitignored
`data/` and never written to by the build.

## acquisition (not in this repo)

Everything that crosses the network lives in `rivulet`, a private package that
is not public and not obtainable. A checkout without it cannot build the
corpus from scratch, and that is deliberate — the networked targets exit 2
("machinery not installed") rather than half-running.

- `make clearance` — earn Cloudflare clearance for jainqq.org in a separate,
  visible Chrome → `data/clearance.json`. The fetchers re-earn it themselves
  when it lapses.
- `make fetch-catalog` — the 34-page Quantum catalog → `data/metadata_cache/jainqq/`.
  ~34 requests.
- `make fetch-text` — one `booktext` JSON per catalogued item with text →
  `data/fulltext_cache/<srno>.json`. `ARGS="--languages sanskrit-only"`
  (the default) is ~2k items, about 1.2 h at the 2 s delay. Resumable.

The jainelibrary.org API metadata under `data/metadata_cache/jainelibrary/`
came from a one-off recon pull; its fetcher is not yet in rivulet.

## building and serving

Offline, from the caches:

- `make parse-catalog` — cached catalog pages → `data/catalogue.jsonl`, one
  row per distinct item, and a table of the language slices.
- not yet written: `extract-text`, `count-sizes`, `build`, `changelog`,
  `audit`, `serve` — the shared vocabulary of the three built Atlases.

# license

[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.en),
matching `Sāgarasaṅgama`. Applies to this atlas's own code and derived
metadata; the texts themselves belong to the Jain eLibrary, its publishers and
contributors.
