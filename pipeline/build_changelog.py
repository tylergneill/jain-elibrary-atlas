"""web_date -> docs/data/changelog.json: the library's accession series, monthly.

Every API item records the day it went online, so growth here is **measured**
from the catalogue's own stamps rather than inferred -- the one thing this
collection does better than the sibling Atlases. Monthly periods, cumulative,
in E-bhāratīsampat's dict shape, which the aggregator already reads:

    {"granularity": "month", "periods": [
        {"date": "2007-03-01",
         "cumulative_count": ...,            every catalogued item
         "cumulative_text_count": ...,       items with a text, from either source
         "cumulative_quantum_text_count": ..., of which Quantum's public booktext
         "cumulative_elibrary_text_count": ...,  of which the library's own OCR file (eLibrary)
         "cumulative_sized_count": ...,      items whose text was fetched and measured
         "cumulative_iast_bytes_total": ...} IAST bytes over the sized items -- a FLOOR
     ], "undated_works": N}

**Quantum's text stops with items added in June 2020** (its catalog runs on to
2022), and the library's own OCR, fetched behind its login, carries the count
on to July 2022. Both are in `cumulative_text_count`, and split out beside it
so the chart can show which is which. After July 2022 no item has text. The byte
series covers only what has been fetched (the Sanskrit-only slice on the
seeding day) and is published as the floor it is.

Items only Quantum knows carry no date and are counted under `undated_works`.

    make changelog
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from pipeline.config import CHANGELOG_PATH, TREE_PATH


def series(works: list[dict]) -> tuple[list[dict], int]:
    """Monthly cumulative periods over `works`, and how many had no date."""
    by_month: dict[str, list[dict]] = defaultdict(list)
    undated = 0
    for w in works:
        added = w.get("added")
        if not added:
            undated += 1
            continue
        by_month[added[:7]].append(w)

    periods = []
    c_all = c_text = c_quantum = c_library = c_sized = c_bytes = c_library_bytes = 0
    for month in sorted(by_month):
        ws = by_month[month]
        c_all += len(ws)
        c_text += sum(1 for w in ws if w.get("text"))
        c_quantum += sum(1 for w in ws if w.get("text") == "quantum")
        c_library += sum(1 for w in ws if w.get("text") == "elibrary")
        sized = [w for w in ws if w.get("sizes")]
        c_sized += len(sized)
        c_bytes += sum(w["sizes"].get("transliterated_bytes", 0) for w in sized)
        c_library_bytes += sum(w["sizes"].get("transliterated_bytes", 0) for w in sized
                               if w.get("text") == "elibrary")
        periods.append({
            "date": f"{month}-01",
            "added": len(ws),
            "cumulative_count": c_all,
            "cumulative_text_count": c_text,
            "cumulative_quantum_text_count": c_quantum,
            "cumulative_elibrary_text_count": c_library,
            "cumulative_sized_count": c_sized,
            "cumulative_iast_bytes_total": c_bytes,
            "cumulative_elibrary_iast_bytes": c_library_bytes,
        })
    return periods, undated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--tree", type=Path, default=TREE_PATH)
    parser.add_argument("--out", type=Path, default=CHANGELOG_PATH)
    args = parser.parse_args()

    tree = json.loads(args.tree.read_text(encoding="utf-8"))
    # Two series, as the tree has two tiers: `periods` over the Sanskrit tier
    # (what the aggregator reads) and `periods_prakrit` with the Prakrit tier
    # added, for the About page's "include Prakrit" checkbox.
    periods, undated = series([w for w in tree["works"] if not w.get("prakrit")])
    periods_prakrit, undated_prakrit = series(tree["works"])

    out = {
        "granularity": "month",
        "source": "jainelibrary.org API web_date, the day each item went online",
        "periods": periods,
        "undated_works": undated,
        "periods_prakrit": periods_prakrit,
        "undated_works_prakrit": undated_prakrit,
        "note": ("cumulative_text_count counts items with a text from either source: "
                 "Jain Quantum's public booktext (items added to mid-2020) or the library's "
                 "own OCR file, fetched behind its login (to July 2022); the two are split "
                 "out beside it. cumulative_iast_bytes_total covers the items fetched and "
                 "measured. `periods` is the Sanskrit tier; `periods_prakrit` adds the "
                 "Prakrit tier."),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    last = periods[-1] if periods else {}
    print(f"wrote {args.out}: {len(periods)} months, {periods[0]['date'] if periods else '-'} .. "
          f"{last.get('date')}; final count {last.get('cumulative_count')}, text "
          f"{last.get('cumulative_text_count')}, sized {last.get('cumulative_sized_count')}, "
          f"undated {undated}")
    if periods_prakrit:
        print(f"  with Prakrit: final count {periods_prakrit[-1]['cumulative_count']}, text "
              f"{periods_prakrit[-1]['cumulative_text_count']}, undated {undated_prakrit}")


if __name__ == "__main__":
    main()
