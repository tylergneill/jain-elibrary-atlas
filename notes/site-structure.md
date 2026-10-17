# site structure

What we have learned about jainelibrary.org and jainqq.org **from the sites
themselves** — routes, gates, field semantics, and the conventions that will
break a parser. Reference: add to it; prune only what is disproven. Observed
2026-10-07 unless marked otherwise.

**Corpus figures are not here.** They belong in the audit and the About page
once those exist; until then `recon/figures-2026-10-07.md` holds the seeding
measurements, dated.

## jainelibrary.org

**A React SPA (Vite build) over Django REST Framework.** `/` and every
unknown path return the same 931-byte shell; the app's state lives at
`/api/`. `robots.txt` is `Disallow: /`. nginx 1.28 on Ubuntu; no CDN, no
challenge.

**`/api/` is an open DRF router root** listing ~30 endpoints. The content
ones, with their 2026-10-07 counts:

| endpoint | count | one row is |
| --- | --- | --- |
| `books` | 21,920 | a book |
| `articles` | 6,145 | a standalone article |
| `magazines` | 9,369 | an **article or issue within a periodical** — classification `Magazine` (8,177) or `Article` (1,191), categories `india_<title>` / `usa_<title>` naming the periodical |
| `audio` | 1,180 | an MP3 with a transcript DOCX |
| `manuscripts` | 977 | a manuscript scan |
| `agam` | 60,880 | **one sutra** of the Āgama canon, pointing at a mool docx and a translation docx (`mool_file`, `trans_file`, `mool_sr_num`, `trans_sr_num`) — a different schema from the other five |

`authors`, `publishers`, `languages`, `catalogues`, `collections` return
`count: 0` anonymously. `user-downloads`, `cart`, `profiles` return 401.

**Pagination.** `?page=N&page_size=M`; `page_size=500` is accepted (the
default page is 100). Ordering is not stable across pages — a 44-page walk of
books returned 20,998 distinct ids in 21,000 rows, and 21,918 distinct of
21,920 overall. Dedupe on `id` and expect the final count to fall a few short.

**Item detail** at `/api/books/<sr_no>/` returns the same record as the list
row — nothing extra.

**Identity.** `id` == `sr_no`, a six-digit zero-padded string, shared with
Quantum's `srno`. Ranges appear to be allocated per folder (books low,
articles 2xxxxx, audio 33xxxx, magazines 5xxxxx/7xxxxx, manuscripts 6xxxxx)
but this is unverified — do not derive the type from the number.

**Files.** `download_items[]` is the authoritative file list: `file_idx`,
`file_name`, `file_type`, `file_size`, `gparam_path` (`wasabipath1` — the
files are on Wasabi object storage). `file_urls` and `pdf_url` are the same
names in an older shape. Types seen: `TOC pdf` (small, with bookmarks),
`Standard PDF`, `HR pdf` (high-res), `OCR docx` (the OCR text), `TOC docx`,
`DOCX`, `PDF`, `PPTX`, `PPT`, `MP3`, `ZIP`. **No download URL is published
anywhere in the metadata**; the `/media/...` path implied by `cover_image_url`
404s for files. Downloads go through the authenticated app.

**`file_size` is a human string**, not bytes: `"120 MB"`, `"227 KB"`, and
also `"128K"` (no B), `"N/A"`, and at least one `"317 ખB"` (Gujarati letter)
and `"13 MKB"`. Parse `^\s*([\d.]+)\s*(B|K|KB|M|MB|G|GB)\s*$` case-insensitively
and count the rest as unsized. Precision is to the unit shown, so sums are
approximate to a few percent.

**Language fields — three of them, and only one is honest.**
- `language`: a comma-joined string as catalogued (`"Sanskrit, Hindi"`).
  **Use this.**
- `languages[]`: `{name, code}` pairs that *add the script* — every
  Sanskrit-only book also lists `Hindi`. Misleading for grouping.
- `script`: `Hindi` (meaning Devanāgarī), `Gujarati`, `English`, and ~20
  minor values including typos (`Englis`, `Punjabji`) and `test_Hindi`.

**Classification and categories.** `classification` is a string, mostly by
script (`Book_Devnagari`, `Book_Gujarati`, `Book_English`, `Book_Other`) plus
type words (`Article`, `Dictionary`, `Catalogue`, `Smruti_Granth`, `Manuscript`,
`Interfaith`, `Seminar`, `Book_Comics`), sometimes comma-joined, with typos.
`categories[]` has `{name, slug}`; 634 distinct slugs over books, 1–4 per
item, and some slugs are comma-joined pairs (`book_devnagari,-book_gujarati`,
`philosophy,-religion`). Per-Āgama slugs (`agam_acharang`, `agam_bhagwati`, …)
are the most useful fine axis for the canon.

**Other fields worth keeping**: `pages` (float), `publication_year`,
`web_date` (YYYYMMDD integer — when the item went online; the natural
changelog axis), `downloads`, `views`, `is_active`, `copyright`,
`master_folder`/`sub_folder` (the storage path), `recommended`/`source`.
Fields `title_en`/`title_english` and `title_native`/`title_language` are
duplicate pairs; `title_translit` is usually null.

## jainqq.org (Jain Quantum)

**Next.js, server-rendered, behind a Cloudflare managed challenge.** curl gets
`403` with `cf-mitigated: challenge` on every route except `robots.txt`
(which allows all). A real Chrome session passes once and then fetches freely,
including the `_next/data` JSON routes — so the fetcher needs rivulet's
browser-attach clearance, and the cookie is bound to the User-Agent that
earned it. The build id in `_next/data/<buildId>/…` changes on each deploy;
read it from `__NEXT_DATA__` on any page rather than hardcoding it.

Analytics go to Google; the Donate and Pathshala links point at
jainelibrary.org; the About page says it is "a Quantum search capability over
the JaineLibrary catalogue" and also holds non-Jain texts.

**Routes.**
- `/browse` — category tiles. Every tile is a search link `/?q=<term>&browse=1`
  where `<term>` is a classification token (`Book_English`, `Article_hindi`,
  `agam canon`, `H000`…). No counts shown.
- `/catalog?page=N` — the whole catalogue, **1000 rows per page, 34 pages**,
  with `pageProps.maxPage`. JSON twin: `/_next/data/<buildId>/catalog.json?page=N`.
  Row fields: `id` (positional, not stable), `srno`, `title`, `title_lang`,
  `language`, `classification` (comma list, trailing commas, with codes like
  `A000`, `H001`, `M015`), `sutra_author`, `author`, `editor`, `translator`,
  `num_pages`, `publisher`, `pub_year`, `file_size`, `filename`, `script`,
  `master_folder`, `sub_folder`, `download_count`. Pages are not exactly
  1000 (999, 998, 992 seen) — count rows, don't multiply.
- `/explore/<srno>/<page>` — the page viewer (not inspected).
- `/booktext/<Title_with_underscores>/<srno>` — **the full OCR plaintext** of
  an item. `pageProps = {bookData, fullText, srno}`. `fullText` is one string
  with `<a href="…/explore/<srno>/<n>">Page #n</a>` anchors followed by a
  dashed rule between pages; the page count in it matches `num_pages` to ±1.
  Text is OCR output with `\r\n` line ends, header boilerplate ("Jain
  Education International … For Private and Personal Use Only"), and the usual
  OCR noise. The title in the URL is only cosmetic as far as observed — the
  `srno` selects the item — but this is untested with a wrong title.
  JSON twin: `/_next/data/<buildId>/booktext/<Title>/<srno>.json?title=<Title>&srno=<srno>`.

**Has-text rule (hypothesis, 22/22 in sample).** An item with a non-blank
`file_size` in the catalog has a booktext page with text; one with a blank
`file_size` returns the page with an empty `fullText`. 6,244 of 33,048 rows
were blank on 2026-10-07.

**`master_folder`** values: `book`, `magazine` (here an *issue*, whereas the
API's `magazines` endpoint lists the articles inside issues — the two sites
do not agree on what a magazine row is), `article`, `agam`, `audio_file`,
`manuscript`, `jaina_edu`, `null`, `test_Master_Folder` (10 test rows; drop).

**The two catalogues are not the same set.** Sampled Quantum rows in the
`agam` and `jaina_edu` folders were absent from all five API item endpoints,
while the API's `magazines` endpoint holds ~9k article rows Quantum files
differently. Join on `srno` and expect unmatched rows on both sides; the
Āgama *books* may be reachable only via Quantum or via the sutra-level
`api/agam/` file names.

**`file_size` is the served PDF**, not a text measure — "10 MB" for a
250-page book whose text ran 272k characters. The API's `OCR docx` size is
the surface proxy for text volume (see `recon/figures-2026-10-07.md`).

**Rate.** Nothing in either site pushed back at one request per 2 s. Both
pulls stayed under 200 requests. Keep it there until there is a reason not to.

## jainqq.org search (observed 2026-10-07, in the browser)

**The search box is a JSON API under `/api/query/`**, Meilisearch-shaped
(`hits`, `nbHits`, `processingTimeMs`), and it answers to the same Cloudflare
clearance as the pages:

    /api/query/catalog?q=<q>&limit=N&offset=M                     catalogue rows
    /api/query/exactpages?q=<q>&limit&offset&facetFilters=&exhaustive=false   page hits, literal
    /api/query/pages?q=<q>&limit&offset&facetFilters=&exhaustive=false        page hits, via transliteration

A page hit carries `srno`, `title`, `authors`, `page_no`, `pub_year` and a
`highlight` with `<em>` marks (non-ASCII escaped as bare `uXXXX`, no
backslash). `exhaustive=true` is the "Exhaustive Results (all pages)" toggle.

**Devanāgarī queries work on both indexes.** `स्याद्वादरत्नाकर` returned 4,726
page hits with the compound tokenised and highlighted, and the catalog query
`स्याद्वाद रत्नाकर` returned all nine Ratnakar/Manjari rows. The catalog index
stores an ASCII folding of `title_lang` (`syaadvaad rtnaakr bhaag 5`) and
folds the query the same way, which is why Devanāgarī, the site's own
romanisation, and near-misses all land.

**Harvard-Kyoto works through the "Search Transliterations" toggle**, which
switches the frontend from `exactpages` to `pages`. The `pages` index holds an
HK transliteration of the OCR text — a highlight reads
`prameyakamalamArtaNDa aura syAdvAdaratnAkara jitanA vizAla hii|` — so an HK
query matches Devanāgarī content (739 hits for `syAdvAdaratnAkara` against
161 literal). Without the toggle an HK query is matched typo-tolerantly
against the romanised titles and the English text, which is why
`syAdvAdaratnAkara` ranks "Syadvada and Statistic" first.

**Search Options exposes two facets, and neither is subject.** "All
languages" and "All Categories", the latter 18 values: Articles, Audio Files,
Comics, Devanagari Books, English Books, Gujarati Books, Other Lang. Books,
Catalogues, Dictionaries, Interfaith Books, JAINA Education, Magazines,
Manuscripts, Presentations, Publishers, Ritual Texts, Seminars, Smruti
Granths. The same script-and-format vocabulary as the Browse tiles. The
subject tokens in `classification` (`Philosophy`, `Nyay`, `Buddhism`, …) are
not offered anywhere in the interface.

**The has-text rule has exceptions.** Twelve of the 1,974 Sanskrit-only
sized rows returned an empty `fullText` (the response is ~550 bytes of
`bookData` alone): the consecutive batch 007833–007843 and 035329. The
fetcher journals `chars: 0` for them, and `text_count` must come from the
journal, not from the catalog. Over the full Sanskrit-only run the text
averaged ~1,720 characters a page (978 M characters, 569,653 pages).

## Growth, and where Quantum stops (measured 2026-10-07)

**Every API item carries `web_date`**, the day it went online (YYYYMMDD
integer; 39,582 of 39,588 parse, the rest are typos like `2023050`). It is a
real accession series, 2007 to the present: roughly 400 items in 2007, a
4,275 spike in 2011, 2,000–2,600 a year since 2021, 1,708 in 2026 up to
2026-10-03 — four days before the measurement. The library is alive at
150–250 items a month. This is the changelog axis.

**Quantum's catalog is a snapshot ending in 2022.** Joining the two on
`srno`: 31,049 items are in both; of the 8,539 API-only items, 8,414 were
accessioned 2023 or later, and only 8 items accessioned after 2022 appear in
Quantum at all. Quantum's 1,999 catalog-only rows are the `agam` folder
(1,483), audio, JAINA education material and 57 books. So Quantum = the
eLibrary as of about the end of 2022, plus the Āgama shelf; everything the
library has added since lives only in the API, with no public plaintext.

**OCR lags accession, or stopped.** Among any-Sanskrit items: 100% of
2007–2015 accessions have an OCR docx, 93% of 2016–2022, **0% of
2023–2026** (14 of 2,586). By month the two routes stop at different times:
Quantum's text ends with items that went online in **June 2020**, while the
library's OCR docx runs to **July 2022** and stops in August 2022. Items from
mid-2020 to mid-2022 are in Quantum's catalog with a blank `file_size` and
no text, but the library OCR'd them (about 4,400 items, ~740 any-Sanskrit,
313 in the Sanskrit tier). So the public text is the library as of mid-2020,
the login-gated OCR the library as of mid-2022, and nothing after that has
text by either route.

**The library's OCR is one batch, run on 2022-07-30.** Each OCR docx opens
with a note ("OCR Unicode Note") giving the PDF and OCR page counts and a
`Create Time`; all 325 fetched for the tier (items accessioned 2016 to July
2022) say 2022-07-30. So the library re-OCR'd its backlog that day and has
not run OCR since, which is the August-2022 cliff. It is a different pass from
Quantum's text: on five items with both, lengths agree to a few percent but
63–97% of words match in order (`recon/ocr_compare.py`). Treat the two as
separate sources of comparable size, never as the same text.

**Fetching it** (owner's decision, 2026-10-17): `make library-login` then
`make fetch-ocr-docx`. The download route is
`POST /api/books/get_signed_download_url/` with `{sr_no, filename,
file_idx: 10, expires_in}`, called from inside the logged-in page (bearer
token in `localStorage.accessToken`), returning a 180-second Wasabi link.
`GET /api/books/<srno>/ocr_content/` would give text directly but answers 404
"content has not been extracted yet" for these items. The library caps
downloads per account per day (`daily_book_download_limit`, HTTP 429); 325 in
one session did not reach it.

**The `language` string changed convention around 2023.** Items accessioned
2007–2015 that involve Sanskrit are tagged plain `Sanskrit` 40% of the time;
from 2023 that falls to 2%, and `Sanskrit, Hindi` takes 74% — the field now
folds the Devanāgarī script in, as the `languages[]` array always did. A
"Sanskrit-only" slice is therefore biased to older accessions and is **not
comparable across eras**; any-Sanskrit is the stable grouping, and the
Sanskrit share of what is being added is rising (811 of 2,361 in 2025, 725
of 1,708 in 2026 so far). The 2026-05 spike (305 Sanskrit items in a month)
is one source, "Raj Salecha", filing a `jain_darshan` batch.

**`sr_no` is only loosely a time axis** (median accession year rises from
2010 in the 000000s to 2026 in the 045000s, but ranges overlap by a decade
and the 7xxxxx magazine articles were all filed in 2018). Date from
`web_date`, never from the serial.
