"""The flat tree shape: a `works` list plus two axes of ids into it.

Adopted from E-bhāratīsampat's `pipeline/shape.py`, because the frontend is
adopted from there too: `docs/app.js` renders a flat work list four ways
(category flat or grouped by author, author flat or grouped by category) and
grouping at render time is what keeps one copy of the data.

    category  domain -> sub_domain -> works
    author    author -> works, authorless works under `unknown`

`summarize()` is the contract with Sāgarasaṅgama: `all_stats` carries
`count`, `text_count`, `pdf_count`, `sized` and the three byte totals, summed
only over works that have `sizes`. `sized` below `text_count` means the byte
figures are a floor, and the aggregator says so.
"""

import json
from collections import defaultdict
from pathlib import Path

UNKNOWN_AUTHOR = "unknown"
UNCATEGORIZED_SUB = "uncategorized"
SIZE_KEYS = ("raw_bytes", "content_bytes", "transliterated_bytes")


def summarize(works: list[dict]) -> dict:
    stats = {
        "count": len(works),
        "text_count": sum(1 for w in works if w.get("text")),
        "pdf_count": sum(1 for w in works if w.get("pdf")),
    }
    sized = [w["sizes"] for w in works if w.get("sizes")]
    stats["sized"] = len(sized)
    if sized:
        for key in SIZE_KEYS:
            if any(key in s for s in sized):
                stats[key] = sum(s.get(key, 0) for s in sized)
    return stats


def build_category_axis(works: list[dict], by_id: dict[str, dict],
                        domain_order=None, sub_order=None) -> list[dict]:
    """`domain_order` / `sub_order`: optional sort keys, so a canon can be
    listed in its traditional order rather than alphabetically. Default is
    alphabetical with the absence bucket last."""
    domains: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for work in works:
        sub = work.get("sub_domain") or UNCATEGORIZED_SUB
        domains[work["domain"]][sub].append(work["id"])
    out = []
    for domain in sorted(domains, key=domain_order or (lambda d: d)):
        subs = [
            {
                "title": sub,
                "work_ids": domains[domain][sub],
                "stats": summarize([by_id[i] for i in domains[domain][sub]]),
                **({"uncategorized": True} if sub == UNCATEGORIZED_SUB else {}),
            }
            for sub in sorted(domains[domain],
                              key=lambda s: (s == UNCATEGORIZED_SUB,
                                             sub_order(domain, s) if sub_order else s))
        ]
        ids = [i for s in subs for i in s["work_ids"]]
        out.append({"title": domain, "children": subs,
                    "stats": summarize([by_id[i] for i in ids])})
    return out


def build_author_axis(works: list[dict], by_id: dict[str, dict]) -> list[dict]:
    authors: dict[str, list[str]] = defaultdict(list)
    for work in works:
        authors[work.get("author") or UNKNOWN_AUTHOR].append(work["id"])
    out = []
    for author in sorted(authors, key=lambda a: (a == UNKNOWN_AUTHOR, a)):
        ids = authors[author]
        entry = {
            "title": author,
            "work_ids": ids,
            "stats": summarize([by_id[i] for i in ids]),
            "domains": sorted({by_id[i]["domain"] for i in ids}),
        }
        if author == UNKNOWN_AUTHOR:
            entry["unknown"] = True
        out.append(entry)
    return out


def build_axes(works: list[dict], source: str, extra_stats: dict | None = None,
               domain_order=None, sub_order=None) -> dict:
    works.sort(key=lambda w: w["serial"])
    by_id = {w["id"]: w for w in works}
    stats = summarize(works)
    if extra_stats:
        stats.update(extra_stats)
    return {
        "source": source,
        "works": works,
        "axes": {
            "category": build_category_axis(works, by_id, domain_order, sub_order),
            "author": build_author_axis(works, by_id),
        },
        "all_stats": stats,
        "unknown_author": UNKNOWN_AUTHOR,
        "uncategorized_sub": UNCATEGORIZED_SUB,
    }


def split_tier_stats(tree: dict, in_default) -> None:
    """Give every axis node two sets of figures: the default tier's and the wider one's.

    The tree carries the wider tier's works (with `in_default(work)` false for
    the extras), so `build_axes` has summed over all of them. Afterwards each
    node's `stats` is re-derived from its default-tier works alone, and the
    wider figures are kept beside them as `stats_prakrit`. A node with no
    default-tier work gets `count` 0 and the frontend hides it until the reader
    widens the tier. The Wikisource Atlas's "improperly categorized" pill is
    the model: two totals published, the reader chooses.
    """
    by_id = {w["id"]: w for w in tree["works"]}

    def ids_of(node: dict) -> list[str]:
        if "work_ids" in node:
            return node["work_ids"]
        return [i for child in node.get("children", []) for i in ids_of(child)]

    def walk(nodes: list[dict]) -> None:
        for node in nodes:
            node["stats_prakrit"] = node["stats"]
            node["stats"] = summarize([by_id[i] for i in ids_of(node) if in_default(by_id[i])])
            walk(node.get("children", []))

    for nodes in tree["axes"].values():
        walk(nodes)


def write(tree: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tree, ensure_ascii=False, separators=(",", ":")),
                    encoding="utf-8")


def report(tree: dict, path: Path) -> None:
    stats = tree["all_stats"]
    cats, auths = tree["axes"]["category"], tree["axes"]["author"]
    print(f"wrote {path} ({path.stat().st_size / 1e6:.1f} MB) from {tree['source']}")
    print(f"  {stats['count']} works, {stats['text_count']} with text, "
          f"{stats['pdf_count']} with pdf, sizes for {stats['sized']}")
    if stats.get("transliterated_bytes"):
        print(f"  IAST bytes over the sized works: {stats['transliterated_bytes']/1e6:.1f} MB")
    print(f"  category axis: {len(cats)} domains, "
          f"{sum(len(c['children']) for c in cats)} sub-domains")
    print(f"  author axis:   {len(auths)} entries")
