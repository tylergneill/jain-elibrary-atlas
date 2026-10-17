"""The text caches -> data/text_extract/<srno>.txt, clean page-delimited text. No network.

Both sources: Quantum's booktexts (data/fulltext_cache/) and the library's OCR
Word files (data/ocr_docx_cache/), which cover disjoint items.

The extraction itself lives in the private `rivulet` package (see
`pipeline/fulltext.py`); the rules it applies live here in `text_measure.py`.
This module resolves the paths, calls in, and reports.

    make extract-text
    make extract-text ARGS="--transliterate"     # Devanāgarī written as IAST
"""

import argparse
from pathlib import Path

from pipeline.config import FULLTEXT_CACHE_DIR, OCR_DOCX_CACHE_DIR, TEXT_EXTRACT_DIR
from pipeline.fulltext import load_docx_extractor, load_extractor


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--cache", type=Path, default=FULLTEXT_CACHE_DIR)
    parser.add_argument("--out", type=Path, default=TEXT_EXTRACT_DIR)
    parser.add_argument("--transliterate", action="store_true",
                        help="write Devanāgarī as IAST (default: the script as served)")
    args = parser.parse_args()

    extract_cache = load_extractor()
    if not args.cache.is_dir():
        raise SystemExit(f"no cache at {args.cache} -- run `make fetch-text` first.")
    summary = extract_cache(args.cache, args.out, transliterate=args.transliterate)
    print(f"written:    {summary['written']} items ({summary['script']})")
    if summary["empty"]:
        print(f"empty:      {summary['empty']} (the route returned no text)")
    if summary["unreadable"]:
        print(f"unreadable: {summary['unreadable']}")
    print(f"content:    {summary['content_bytes']:,} bytes")
    docx = load_docx_extractor()(OCR_DOCX_CACHE_DIR, args.out, transliterate=args.transliterate)
    print(f"library OCR: {docx['written']} items written, {docx['empty']} empty, "
          f"{docx['unreadable']} unreadable, {docx['content_bytes']:,} bytes")
    print(f"wrote:      {args.out}")


if __name__ == "__main__":
    main()
