"""The two catalogues + the sizes -> docs/data/tree.json. Offline.

**The universe is the union of the two catalogues on `srno`**: every item the
jainelibrary.org API lists, plus the rows only Quantum has (the Āgama shelf,
audio, JAINA material). Provisional -- the todo's phase-0 item is still open
-- but it is the sibling pattern: E-bhāratīsampat counts its PDF-only works
and lets `text_count` fall below `count`, and this collection has the same
shape, with the post-2022 accessions standing where the scans stand there.

One work per item:

    id, serial        the six-digit sr_no (serial as int, for sort order)
    title             the API's English title, else Quantum's; `title_native`
                      the Devanāgarī/Gujarati one where either has it
    domain            the item type (Books, Manuscripts, Magazines, Articles,
                      Audio, Āgama shelf, JAINA Education, Other)
    sub_domain        the catalogue's `language` string
    author            API author, else sutra_author, else Quantum's
    text              "quantum" when Quantum has a booktext for it -- a sized
                      catalog row whose booktext is not empty
                      (`empty_booktexts`) -- else "elibrary"
                      when the library's own OCR Word file was fetched and has
                      text (behind its login; see `make fetch-ocr-docx`), else null
    pdf               the API lists a Standard PDF, or Quantum's file is a .pdf
    sizes             from data/sizes.jsonl (Quantum) or data/ocr_sizes.jsonl (library
                      OCR), where the text was fetched and measured
    ocr_created       library OCR only: the date the library's OCR file was made
    has_text          the clean text is on this machine (data/text_extract/)
    added             web_date as YYYY-MM-DD
    ocr_docx          the API lists an OCR Word doc (login-gated, not fetched)
    sources           ["api", "quantum"] -- which catalogues know the item

The tree holds the Sanskrit tier and, flagged `prakrit: true`, the books
whose language string is Prakrit or Sanskrit-and-Prakrit; every axis node
carries `stats` (Sanskrit) and `stats_prakrit` (both), and the reader's
"include Prakrit" pill chooses between them.

`all_stats` -- the Sanskrit tier, the aggregator's contract -- is `shape.summarize`
plus `quantum_text_count`, `elibrary_text_count`, `prakrit_count`, `api_count`,
`quantum_count`, `last_changed` (the newest web_date) and `sourced` (the
newest fetch: when our copy was taken, the same date docs/VERSION carries).

    make build
"""

import argparse
import glob
import json
import re
from datetime import date
from pathlib import Path

from pipeline.config import (API_CACHE_DIR, CATALOG_LOG_PATH, CATALOGUE_PATH, DOCS_DIR,
                             OCR_LOG_PATH, OCR_SIZES_PATH, SIZES_PATH, TEXT_EXTRACT_DIR,
                             TEXT_LOG_PATH, TREE_PATH)
from pipeline.shape import build_axes, report, split_tier_stats, summarize, write

# The library's "manuscripts" folder holds block prints and horizontal-format
# printed books, not manuscripts, so it merges into Books and the work carries
# `horizontal: true` instead (decided 2026-10-07).
DOMAIN_OF_ENDPOINT = {"books": "Books", "articles": "Articles", "magazines": "Magazines",
                      "manuscripts": "Books", "audio": "Audio"}
DOMAIN_OF_FOLDER = {"book": "Books", "article": "Articles", "magazine": "Magazines",
                    "manuscript": "Books", "audio_file": "Audio",
                    "agam": "Books", "jaina_edu": "JAINA Education"}

_SIZE_RE = re.compile(r"^\s*([\d.]+)\s*(B|K|KB|M|MB|G|GB)\s*$", re.I)

# The three types that carry Sanskrit texts. Articles, magazines, audio, the
# JAINA education material and the folderless rows are almost entirely
# Gujarati, Hindi and English, and are not e-texts in the sense the aggregator
# counts. "Manuscripts" is the library's folder name; what it holds are block
# prints and horizontal-format printed books, so the label says so.
# Quantum's `agam` folder is sutra-level editions of the same kind the API
# files under books, so it is Books too; "type" survives only as a filter on
# what enters the tree, never as a shelf or a badge (two buckets is no axis).
PUBLISHED_TYPES = {"Books"}

# The canon axis, from the library's own `agam_*` slugs. The slug names the
# canonical text; the class it belongs to is the standard Śvetāmbara
# Mūrtipūjaka arrangement of the 45 Āgamas, which is reference knowledge
# rather than a reading of this collection. Display names are the IAST forms
# of the site's romanisations. A slug not listed here still gets a canon node,
# under "Āgama (other)", with its slug prettified -- nothing is dropped.
CANON_CLASSES = ("Aṅga", "Upāṅga", "Chedasūtra", "Mūlasūtra", "Cūlikāsūtra",
                 "Prakīrṇaka", "Āgama (other)", "Āgama indexes and digests")
CANON = {
    # Aṅga
    "agam_acharang": ("Aṅga", "Ācārāṅga"), "agam_sutrakritang": ("Aṅga", "Sūtrakṛtāṅga"),
    "agam_sthanang": ("Aṅga", "Sthānāṅga"), "agam_samvayang": ("Aṅga", "Samavāyāṅga"),
    "agam_bhagwati": ("Aṅga", "Bhagavatī (Vyākhyāprajñapti)"),
    "agam_gyatadharmkatha": ("Aṅga", "Jñātādharmakathā"), "agam_upasakdasha": ("Aṅga", "Upāsakadaśā"),
    "agam_antkrutdasha": ("Aṅga", "Antakṛddaśā"), "agam_anuttaropapatikdasha": ("Aṅga", "Anuttaropapātikadaśā"),
    "agam_prashnavyakaran": ("Aṅga", "Praśnavyākaraṇa"), "agam_vipakshrut": ("Aṅga", "Vipākaśruta"),
    # Upāṅga
    "agam_aupapatik": ("Upāṅga", "Aupapātika"), "agam_rajprashniya": ("Upāṅga", "Rājapraśnīya"),
    "agam_jivabhigam": ("Upāṅga", "Jīvābhigama"), "agam_jivajivabhigam": ("Upāṅga", "Jīvājīvābhigama"),
    "agam_pragyapana": ("Upāṅga", "Prajñāpanā"),
    "agam_suryapragnapti": ("Upāṅga", "Sūryaprajñapti"), "agam_chandrapragnapti": ("Upāṅga", "Candraprajñapti"),
    "agam_jambudwipapragnapti": ("Upāṅga", "Jambūdvīpaprajñapti"), "agam_nirayavalika": ("Upāṅga", "Nirayāvalikā"),
    "agam_kalpavatansika": ("Upāṅga", "Kalpāvataṃsikā"), "agam_pushpika": ("Upāṅga", "Puṣpikā"),
    "agam_pushpachulika": ("Upāṅga", "Puṣpacūlikā"), "agam_vrushnidasha": ("Upāṅga", "Vṛṣṇidaśā"),
    # Chedasūtra
    "agam_nishith": ("Chedasūtra", "Niśītha"), "agam_bruhatkalpa": ("Chedasūtra", "Bṛhatkalpa"),
    "agam_vyavahara": ("Chedasūtra", "Vyavahāra"), "agam_dashashrutaskandh": ("Chedasūtra", "Daśāśrutaskandha"),
    "agam_panchakalpa": ("Chedasūtra", "Pañcakalpa"), "agam_panchakalpa_bhashya": ("Chedasūtra", "Pañcakalpa"),
    "agam_kalpsutra": ("Chedasūtra", "Kalpasūtra"), "agam_jitkalpa": ("Chedasūtra", "Jītakalpa"),
    "agam_mahanishith": ("Chedasūtra", "Mahāniśītha"),
    # Mūlasūtra
    "agam_aavashyak": ("Mūlasūtra", "Āvaśyaka"), "agam_oghniryukti": ("Mūlasūtra", "Oghaniryukti"),
    "agam_pindniryukti": ("Mūlasūtra", "Piṇḍaniryukti"), "agam_dashvaikalik": ("Mūlasūtra", "Daśavaikālika"),
    "agam_uttaradhyayan": ("Mūlasūtra", "Uttarādhyayana"),
    # Cūlikā
    "agam_nandisutra": ("Cūlikāsūtra", "Nandīsūtra"), "agam_anuyogdwar": ("Cūlikāsūtra", "Anuyogadvāra"),
    # Prakīrṇaka
    "agam_chatusharan": ("Prakīrṇaka", "Catuḥśaraṇa"), "agam_aaturpratyakhyan": ("Prakīrṇaka", "Āturapratyākhyāna"),
    "agam_bhaktaparigna": ("Prakīrṇaka", "Bhaktaparijñā"), "agam_sanstarak": ("Prakīrṇaka", "Saṃstāraka"),
    "agam_tandulvaicharik": ("Prakīrṇaka", "Tandulavaicārika"), "agam_chandravedhyak": ("Prakīrṇaka", "Candravedhyaka"),
    "agam_devendrastav": ("Prakīrṇaka", "Devendrastava"), "agam_devendrastava": ("Prakīrṇaka", "Devendrastava"),
    "agam_maransamadhi": ("Prakīrṇaka", "Maraṇasamādhi"), "agam_ganividya": ("Prakīrṇaka", "Gaṇividyā"),
    "agam_mahapratyakhyan": ("Prakīrṇaka", "Mahāpratyākhyāna"), "agam_virastav": ("Prakīrṇaka", "Vīrastava"),
    "agam_gacchachar": ("Prakīrṇaka", "Gacchācāra"),
    # the library's own general buckets
    "agam": ("Āgama (other)", "Āgama, text unspecified"), "agam,-canon": ("Āgama (other)", "Āgama, text unspecified"),
    "agam_anykaalin": ("Āgama (other)", "Other canonical-period texts"),
    "agam_index": ("Āgama indexes and digests", "Indexes"), "agam_aagam_saar": ("Āgama indexes and digests", "Digests"),
    "agam_related_other_literature": ("Āgama indexes and digests", "Related literature"),
}
NOT_CANON = "Other works"


def canon_of(tokens: set[str]) -> tuple[str, str] | None:
    """(class, text) for the first `agam_*` token in canonical order; None if no canon slug."""
    hits = [CANON.get(t) or ("Āgama (other)", t.removeprefix("agam_").replace("_", " ").title())
            for t in tokens if t == "agam" or t.startswith("agam")]
    if not hits:
        return None
    order = list(CANON.values())
    hits.sort(key=lambda h: (CANON_CLASSES.index(h[0]) if h[0] in CANON_CLASSES else 99,
                             order.index(h) if h in order else 999))
    return hits[0]


def canon_tokens(api: dict | None, q: dict | None) -> set[str]:
    t: set[str] = set()
    for c in (api or {}).get("categories") or []:
        t.add(c["slug"].lower())
    for src in ((api or {}).get("classification"), (q or {}).get("classification")):
        for x in (src or "").split(","):
            if x.strip():
                t.add(x.strip().lower())
    return t


def language_tokens(work: dict) -> set[str]:
    return {t.strip() for t in (work.get("language") or "").split(",") if t.strip()}


def in_tier(work: dict, prakrit: bool = False) -> bool:
    """Tier 1: the language string is exactly Sanskrit. With `prakrit`, tier 2:
    only Sanskrit and/or Prakrit, which brings the Āgama shelf in."""
    tokens = language_tokens(work)
    if not tokens:
        return False
    allowed = {"Sanskrit", "Prakrit"} if prakrit else {"Sanskrit"}
    return tokens <= allowed


def load_api(cache: Path) -> dict[str, dict]:
    items: dict[str, dict] = {}
    for ep, domain in DOMAIN_OF_ENDPOINT.items():
        for f in sorted(glob.glob(str(cache / f"{ep}_p*.json"))):
            for r in json.load(open(f, encoding="utf-8"))["results"]:
                r["_domain"] = domain
                items.setdefault(str(r["id"]), r)
    return items


def load_quantum(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    return {r["srno"]: r for r in (json.loads(l) for l in path.open(encoding="utf-8") if l.strip())}


def load_sizes(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out = {}
    for line in path.open(encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[r["srno"]] = r
    return out


def empty_from_journal(path: Path) -> set[str]:
    """Items whose booktext came back empty: a sized catalog row with no text."""
    empties = set()
    if not path.exists():
        return empties
    for line in path.open(encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            if "chars" in r:
                (empties.add if r["chars"] == 0 else empties.discard)(r["srno"])
    return empties


def empty_booktexts(journal: Path, sizes: dict[str, dict]) -> set[str]:
    """Quantum booktexts with nothing in them: journalled empty, or measured empty.

    The journal counts characters as served, so a booktext whose pages hold
    only a byte-order mark (034068: 25 page markers, a BOM under each) passes
    it; the measurement, which drops furniture and the BOM, does not.
    """
    measured = {s for s, r in sizes.items() if r.get("chars") and not r.get("transliterated_bytes")}
    return empty_from_journal(journal) | measured


def web_date(v) -> str | None:
    s = str(int(v)) if isinstance(v, (int, float)) else str(v or "")
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if re.fullmatch(r"(19|20)\d{6}", s) else None


def make_work(srno: str, api: dict | None, q: dict | None, sizes: dict | None,
              empty: set[str], on_disk: set[str], ocr: dict | None = None) -> dict:
    title = (api or {}).get("title_en") or (q or {}).get("title") or srno
    native = (api or {}).get("title_native") or (q or {}).get("title_lang")
    language = (api or {}).get("language") or (q or {}).get("language") or ""
    domain = (api or {}).get("_domain") or DOMAIN_OF_FOLDER.get((q or {}).get("master_folder") or "", "Other")
    # The classical author first: the catalogue's `author` is usually the
    # modern editor or publisher, and `sutra_author` the person a Sanskritist
    # means. The editor is kept on the work as `editor`.
    author = ((api or {}).get("sutra_author") or (q or {}).get("sutra_author")
              or (api or {}).get("author") or (q or {}).get("author") or None)
    editor = ((api or {}).get("author") or (q or {}).get("author") or None) if (
        (api or {}).get("sutra_author") or (q or {}).get("sutra_author")) else None
    # The catalogue writes the literal "Unknown" for some; the tree's own
    # absence bucket (`unknown_author`) is where those belong.
    if author and author.strip().lower() in ("unknown", "-", "none", "n/a"):
        author = None
    q_sized = bool(q and (q.get("file_size") or "").strip())
    text = "quantum" if (q_sized and srno not in empty) else None
    # The library's own OCR stands in only where Quantum has no text; the
    # fetcher never takes it for an item that has one.
    if text is None and ocr and ocr.get("chars"):
        text, sizes = "elibrary", ocr
    api_files = [it["file_type"] for it in ((api or {}).get("download_items") or [])]
    pdf = ("Standard PDF" in api_files) or bool(q and (q.get("filename") or "").lower().endswith(".pdf"))
    canon = canon_of(canon_tokens(api, q))
    # The Indic-script title is the title (97.9% of the Sanskrit tier has one;
    # the frontend transliterates it into the reader's scheme, as the sibling
    # Atlases do). The library's romanisation is kept as `title_en` for the
    # Quantum URL slug and as a fallback where no native title exists.
    native_title = native if native and native.strip() else None
    work = {
        "id": srno, "serial": int(srno) if srno.isdigit() else 0,
        "title": native_title or title,
        "title_en": title,
        # The browsing axis is the canon: class -> canonical text, from the
        # library's own agam_* slugs; everything else sits under one bucket.
        # The item type (Books / Agama shelf) is kept as `type` for the row.
        "domain": canon[0] if canon else NOT_CANON,
        "sub_domain": canon[1] if canon else None,
        "type": domain,
        "author": author or None,
        "editor": editor,
        "script": (api or {}).get("script") or (q or {}).get("script") or None,
        "language": language or None,
        "text": text, "pdf": pdf,
        "sources": [s for s, present in (("api", api), ("quantum", q)) if present],
    }
    if "manuscript" in ((api or {}).get("master_folder"), (q or {}).get("master_folder")):
        work["horizontal"] = True
    if api:
        if api.get("publication_year"):
            work["publish_year"] = str(api["publication_year"])
        if api.get("pages"):
            work["pages"] = int(api["pages"])
        if api.get("classification"):
            work["classification"] = api["classification"]
        if web_date(api.get("web_date")):
            work["added"] = web_date(api.get("web_date"))
        if "OCR docx" in api_files:
            work["ocr_docx"] = True
        if api.get("publisher_name"):
            work["publisher"] = api["publisher_name"]
    elif q:
        if q.get("pub_year"):
            work["publish_year"] = str(q["pub_year"])
        if q.get("num_pages"):
            work["pages"] = int(q["num_pages"])
        if q.get("classification"):
            work["classification"] = q["classification"]
    if text and sizes and sizes.get("chars"):
        work["sizes"] = {k: sizes[k] for k in ("raw_bytes", "content_bytes", "transliterated_bytes")}
        work["sizes"]["pages"] = sizes.get("pages")
        work["sizes"]["devanagari_chars"] = sizes.get("devanagari_chars")
    if text == "elibrary" and ocr.get("ocr_created"):
        work["ocr_created"] = ocr["ocr_created"]
    if srno in on_disk:
        work["has_text"] = True
    return work


def newest_fetch(*journals: Path) -> str:
    """The newest `fetched_at` across the fetch journals, "" if none is on disk.

    Error rows count too: a failed request still says the fetcher ran that day.
    """
    newest = ""
    for path in journals:
        if not path.exists():
            continue
        for line in path.open(encoding="utf-8"):
            if line.strip():
                fetched = json.loads(line).get("fetched_at") or ""
                if fetched > newest:
                    newest = fetched
    return newest


def stamp_version(stats: dict) -> str | None:
    """docs/VERSION and `all_stats.sourced`: when our copy was taken.

    `__content_version__` is the newest `fetched_at` across the two fetch
    journals, the Quantum catalog's and the booktexts' -- counts come from the
    catalogues and sizes from the texts, so either being re-fetched makes the
    published figures newer. (The jainelibrary.org API pull keeps no journal.)
    That is what the field means in every Atlas, "data last sourced"; the
    collection's own newest accession is `all_stats.last_changed`, and until
    2026-10-08 this carried that instead.

    The same date goes into `stats["sourced"]` (the `all_stats` block), beside
    the figures it dates, which is where Sāgarasaṅgama reads it (its
    CONTRACT.md). One value, one function, so the two cannot disagree. Call
    it before the tree is written. Without a journal on this machine the date
    already in docs/VERSION is reused and the file is left alone.
    """
    path = DOCS_DIR / "VERSION"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    kv = {l.split("=")[0].strip(): l for l in lines if "=" in l}
    newest = newest_fetch(TEXT_LOG_PATH, CATALOG_LOG_PATH, OCR_LOG_PATH)[:10]
    content = newest or kv.get("__content_version__", "").partition("=")[2].strip().strip("\"'")
    if not content:
        return None
    stats["sourced"] = content
    if not newest:
        return content
    kv.setdefault("__code_version__", '__code_version__ = "0.1.0"')
    kv["__data_version__"] = f'__data_version__ = "{date.today().isoformat()}"'
    kv["__content_version__"] = f'__content_version__ = "{content}"'
    path.write_text("\n".join(kv[k] for k in ("__code_version__", "__data_version__", "__content_version__")) + "\n",
                    encoding="utf-8")
    return content


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--api-cache", type=Path, default=API_CACHE_DIR)
    parser.add_argument("--catalogue", type=Path, default=CATALOGUE_PATH)
    parser.add_argument("--sizes", type=Path, default=SIZES_PATH)
    parser.add_argument("--out", type=Path, default=TREE_PATH)
    args = parser.parse_args()

    api = load_api(args.api_cache)
    quantum = load_quantum(args.catalogue)
    sizes = load_sizes(args.sizes)
    ocr_sizes = load_sizes(OCR_SIZES_PATH)
    empty = empty_booktexts(TEXT_LOG_PATH, sizes)
    on_disk = {p.stem for p in TEXT_EXTRACT_DIR.glob("*.txt")} if TEXT_EXTRACT_DIR.is_dir() else set()
    if not api and not quantum:
        raise SystemExit("neither the API cache nor data/catalogue.jsonl is present")
    print(f"api items {len(api)}   quantum rows {len(quantum)}   sized {len(sizes)}   "
          f"eLibrary OCR measured {len(ocr_sizes)}   "
          f"empty booktexts {len(empty)}   text on disk {len(on_disk)}")

    srnos = sorted(set(api) | set(quantum))
    library = [make_work(s, api.get(s), quantum.get(s), sizes.get(s), empty, on_disk, ocr_sizes.get(s))
               for s in srnos]
    # THE CONTRACT: what this Atlas publishes -- and so what Sāgarasaṅgama
    # reads -- is the Sanskrit tier only: items whose catalogued language is
    # exactly "Sanskrit", of the three text-bearing types. The rest of the
    # library (Gujarati and Hindi books, articles, magazines, audio, the
    # mixed-language editions) is counted into `all_stats.library_*` for the
    # About page and dropped from the tree. See notes/scratch/todo.md, phase 0.
    # The Prakrit tier rides along: books whose language string is Prakrit, or
    # Sanskrit and Prakrit, are in the tree flagged `prakrit: true`, and every
    # node carries both tiers' figures (`stats`, `stats_prakrit`); the reader's
    # "include Prakrit" pill chooses. `all_stats` stays the Sanskrit tier, the
    # contract above; `all_stats_prakrit` is the wider one.
    works = [w for w in library if in_tier(w, prakrit=True) and w["type"] in PUBLISHED_TYPES]
    for w in works:
        if not in_tier(w):
            w["prakrit"] = True
    sanskrit = [w for w in works if not w.get("prakrit")]

    def tier_stats(ws: list[dict]) -> dict:
        return {
            "canon_count": sum(1 for w in ws if w["domain"] != NOT_CANON),
            "quantum_text_count": sum(1 for w in ws if w["text"] == "quantum"),
            "elibrary_text_count": sum(1 for w in ws if w["text"] == "elibrary"),
            "last_changed": max((w.get("added") or "" for w in ws), default=None) or None,
        }

    extra = {
        "library_count": len(library),
        "library_text_count": sum(1 for w in library if w["text"]),
        "sanskrit_prakrit_count": len(works),
        "any_sanskrit_count": sum(1 for w in library if "Sanskrit" in language_tokens(w)
                                  and w["type"] in PUBLISHED_TYPES),
        "prakrit_count": len(works) - len(sanskrit),
        "api_count": len(api),
        "quantum_count": len(quantum),
        **tier_stats(sanskrit),
    }
    canon_order = list(CANON.values())

    def domain_order(d: str):
        return (CANON_CLASSES.index(d) if d in CANON_CLASSES else 98) if d != NOT_CANON else 99

    def sub_order(d: str, s: str):
        return (canon_order.index((d, s)) if (d, s) in canon_order else 999, s)

    tree = build_axes(works, "api+quantum", extra, domain_order, sub_order)
    # build_axes summed over both tiers; the headline and every node default to
    # the Sanskrit tier, with the wider figures kept beside them.
    tree["all_stats_prakrit"] = {**tree["all_stats"], **tier_stats(works)}
    tree["all_stats"] = {**summarize(sanskrit), **extra}
    split_tier_stats(tree, lambda w: not w.get("prakrit"))
    # Before `write`: the date lands in the tree as well as in docs/VERSION.
    stamped = stamp_version(tree["all_stats"])
    tree["all_stats_prakrit"]["sourced"] = tree["all_stats"].get("sourced")
    write(tree, args.out)
    report(tree, args.out)
    if stamped:
        print(f"  content version: {stamped} (newest fetch; also all_stats.sourced)")


if __name__ == "__main__":
    main()
