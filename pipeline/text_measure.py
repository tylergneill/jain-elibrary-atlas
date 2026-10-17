"""Pure text handling: the cached booktext JSON -> pages -> clean text -> counts.

No network, no I/O. Everything that knows what Quantum's text looks like is
here, once, so that the two consumers cannot drift apart:

    pipeline/count_sizes.py                              measures (this repo, public)
    rivulet/extract/jainquantum/text_extractor.py        writes the text out (private)

rivulet imports from this module; this repo never imports rivulet. That is
the same publishing boundary E-bhāratīsampat draws with its `text_measure.py`.

## What a cached file holds

The data route's `pageProps.fullText`: one string, pages introduced by an
anchor and a dashed rule, and each page body opening with a BOM and a run of
underscores -- the OCR vendor's page marker:

    <a href="https://jainqq.org/explore/<srno>/<n>">Page #n</a>
    ------------------------------------------------------------
    ﻿________________\r\n
    <the page's OCR text>

## What is furniture

Measured over 40 random Sanskrit-only items, 12,443 pages (2026-10-07). The
page marker is on 93% of pages. The rest of the recurring lines are the
digitising libraries' stamps, OCR'd from the scans and therefore spelled
several ways each:

    Shri Mahavir Jain Aradhana Kendra        (also "Jan")
    www.kobatirth.org
    Acharya Shri Kailassagarsuri Gyanmandir  (also "Kailashsagarsuri", "Kalassagarsun")
    For Private and Personal Use Only        (also "And Personal", "Personel", "& Private")
    Jain Education International
    www.umaragyanbhandar.com
    Aho ! Shrutgyanam

and bare page numbers (a line of ASCII digits, 10,176 of them in the sample).
These are removed by **tolerant whole-line patterns**: a line is furniture
when it consists of nothing but one of these stamps, allowing for OCR
variation. Lines that merely contain a stamp alongside text are kept, because
cutting them would cut content. Verse numbers in Devanāgarī digits (`॥१२॥`)
are content and are kept; so is every line with any Indic character.

**Nothing here is a positive test for Devanāgarī.** Many of these books carry
Gujarati-script or Latin-script passages that are content, and the mixed
"Sanskrit, Hindi" books are the majority of the collection.
"""

import re

PAGE_SPLIT_RE = re.compile(
    r'<a href="[^"]*/explore/\d+/(\d+)">Page #\d+</a>\s*\n-{10,}\s*\n?')

# Whole-line furniture. Each pattern is anchored to the whole (stripped) line
# and written loosely enough to absorb the OCR misreadings seen in the sample.
FURNITURE_RES = tuple(re.compile(p, re.I) for p in (
    r"^[﻿_\s]*_{4,}[\s_]*$",                                   # the page marker
    r"^﻿?$",                                                   # a bare BOM
    r"^shri\s+mahavir\s+ja[i]?n\s+aradhana\s+kendra\W*$",
    r"^(www\.)?kobatirth\.org\W*$",
    r"^acharya\s+shri\s+ka[il]+a[s]+agar\s*sur[in]\s+gyanmandir\W*$",
    r"^for\s+(private\s+(and|&)\s+personal|personal\s+(and|&)\s+private)(\s+use\s+only)?\W*$",
    r"^for\s+private\s+(and|&)\s+persone?l\s+use\s+only\W*$",
    r"^jain\s+education\s+international\W*$",
    r"^(www\.)?umaragyanbhandar\.com\W*$",
    r"^aho\s*!?\s*shrutgyanam\W*$",
    r"^[\d\s.\-()\[\]|/]+$",                                        # a page number, bare or in brackets
    r"^[\W_]+$",                                                    # punctuation only: - . , \"
))

INDIC_RE = re.compile(r"[ऀ-ൿ]")  # Devanāgarī through Malayalam


def pages_from_fulltext(full_text: str) -> list[str]:
    """Split the route's `fullText` into page bodies, in page order.

    Text before the first anchor (normally empty) is discarded. A file with
    no anchors yields `[]`, which is how the twelve sized-but-empty items
    present.
    """
    parts = PAGE_SPLIT_RE.split(full_text or "")
    # split() interleaves the captured page numbers: [pre, n1, body1, n2, body2, ...]
    bodies = parts[2::2]
    return [b.replace("\r\n", "\n").replace("\r", "\n") for b in bodies]


def is_furniture(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if INDIC_RE.search(stripped):
        # Indic text is never furniture here; the stamps are all Latin. This
        # keeps Devanāgarī verse numbers and anything OCR'd alongside a stamp.
        return False
    return any(p.match(stripped) for p in FURNITURE_RES)


def clean_page(page: str) -> str:
    """A page body with the furniture lines removed and blank runs collapsed."""
    kept = [ln.rstrip() for ln in page.split("\n") if not is_furniture(ln)]
    text = "\n".join(kept)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def clean_pages(full_text: str) -> list[str]:
    return [clean_page(p) for p in pages_from_fulltext(full_text)]


def devanagari_chars(text: str) -> int:
    return sum(1 for ch in text if "ऀ" <= ch <= "ॿ")


def gujarati_chars(text: str) -> int:
    return sum(1 for ch in text if "઀" <= ch <= "૿")


def latin_letters(text: str) -> int:
    return sum(1 for ch in text if ("a" <= ch <= "z") or ("A" <= ch <= "Z"))


_transliterator = None


def to_iast(text: str) -> str:
    """Devanāgarī -> IAST via skrutable, for `transliterated_bytes`.

    Only the Devanāgarī is transliterated; Gujarati-script and Latin passages
    pass through unchanged. That makes the figure "bytes if the Devanāgarī
    were IAST", which is the comparable quantity across the Atlases, where
    the other collections are Devanāgarī or IAST throughout.
    """
    global _transliterator
    if not text.strip():
        return ""
    if _transliterator is None:
        from skrutable.transliteration import Transliterator
        _transliterator = Transliterator()
    return _transliterator.transliterate(text, from_scheme="DEV", to_scheme="IAST")


def measure(full_text: str, raw_bytes: int) -> dict:
    """The sibling trio plus this corpus's script breakdown, for one item."""
    return _measure_pages(clean_pages(full_text), raw_bytes)


# ---------------------------------------------------------------------------
# The library's own OCR Word files (`data/ocr_docx_cache/<srno>.docx`), for the
# items OCR'd after Quantum's text stopped. Same cleaning, different container.
#
# A file is a normal .docx: the text is in `word/document.xml`, one `<w:p>`
# per OCR'd line or paragraph. It carries **no page boundaries** to speak of
# (an explicit page break or two at most), so its `pages` count is the
# number of page-break-separated segments, not the book's page count. It opens
# with the library's boilerplate, "OCR Unicode Note." through "Please provide
# feed back on this book at the following link: ...", which is cut.
# ---------------------------------------------------------------------------

_W_P_RE = re.compile(r"<w:p[ >].*?</w:p>|<w:p/>", re.S)
_W_TOKEN_RE = re.compile(r'<w:t(?: [^>]*)?>(.*?)</w:t>|<w:tab/>|<w:br w:type="page"/>|<w:br/>|<w:br [^>]*/>', re.S)
_PAGE_BREAK = "\x0c"
_NOTE_START_RE = re.compile(r"^\s*OCR\s+Unicode\s+Note", re.I)
_NOTE_END_RE = re.compile(r"feed\s*back\s+on\s+this\s+book", re.I)
_NOTE_MAX_PARAGRAPHS = 40


def docx_text(data: bytes) -> str:
    """The document's paragraphs as lines, page breaks as form feeds. No cleaning."""
    import html
    import zipfile
    from io import BytesIO

    xml = zipfile.ZipFile(BytesIO(data)).read("word/document.xml").decode("utf-8", "replace")
    lines = []
    for para in _W_P_RE.findall(xml):
        out = []
        for m in _W_TOKEN_RE.finditer(para):
            token = m.group(0)
            if m.group(1) is not None:
                out.append(html.unescape(m.group(1)))
            elif token == "<w:tab/>":
                out.append("\t")
            elif 'w:type="page"' in token:
                out.append("\n" + _PAGE_BREAK + "\n")
            else:
                out.append("\n")
        lines.append("".join(out))
    return "\n".join(lines)


_NOTE_FIELDS_RE = {
    "pdf_pages": re.compile(r"Pdf Page Count:\s*(\d+)", re.I),
    "ocr_pages": re.compile(r"OCR Page Count:\s*(\d+)", re.I),
    "ocr_created": re.compile(r"Create Time:\s*(\d{4}-\d{2}-\d{2})", re.I),
}


def split_library_note(text: str) -> tuple[str, str]:
    """(the library's opening "OCR Unicode Note", the rest). Note is "" if absent.

    The note is the file's whole first page: it ends at the first explicit
    page break, after "Please provide feed back on this book ..." and a block
    giving the PDF and OCR page counts and the OCR's creation time. Where no
    page break follows (not yet seen), it ends after that feedback link line.
    """
    lines = text.split("\n")
    first = next((i for i, ln in enumerate(lines) if ln.strip()), None)
    if first is None or not _NOTE_START_RE.match(lines[first]):
        return "", text
    head = text[:4000]
    if _PAGE_BREAK in head:
        cut = text.index(_PAGE_BREAK)
        return text[:cut], text[cut + 1:]
    for i in range(first, min(len(lines), first + _NOTE_MAX_PARAGRAPHS)):
        if _NOTE_END_RE.search(lines[i]):
            end = i + 2 if i + 1 < len(lines) and lines[i + 1].startswith("http") else i + 1
            return "\n".join(lines[:end]), "\n".join(lines[end:])
    return "", text


def library_note_fields(data: bytes) -> dict:
    """The note's own record: PDF and OCR page counts, OCR creation date."""
    note, _ = split_library_note(docx_text(data))
    out = {}
    for key, pattern in _NOTE_FIELDS_RE.items():
        m = pattern.search(note)
        if m:
            out[key] = int(m.group(1)) if key.endswith("pages") else m.group(1)
    return out


def clean_docx(data: bytes) -> list[str]:
    """A library OCR file -> clean pages (segments between explicit page breaks)."""
    _, text = split_library_note(docx_text(data))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    pages = [clean_page(p) for p in text.split(_PAGE_BREAK)]
    return [p for p in pages if p]


def measure_docx(data: bytes) -> dict:
    """`measure` for a library OCR Word file, plus the note's own record.

    `pages` is the note's OCR page count where it gives one: the file itself
    has no page boundaries to count.
    """
    rec = _measure_pages(clean_docx(data), len(data))
    note = library_note_fields(data)
    rec.update(note)
    if note.get("ocr_pages"):
        rec["pages"] = note["ocr_pages"]
    return rec


def _measure_pages(pages: list[str], raw_bytes: int) -> dict:
    text = "\n\n".join(pages)
    content = text.encode("utf-8")
    return {
        "raw_bytes": raw_bytes,
        "content_bytes": len(content),
        "transliterated_bytes": len(to_iast(text).encode("utf-8")) if text else 0,
        "pages": len(pages),
        "chars": len(text),
        "devanagari_chars": devanagari_chars(text),
        "gujarati_chars": gujarati_chars(text),
        "latin_letters": latin_letters(text),
    }
