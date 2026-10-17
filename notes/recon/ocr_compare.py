"""Quantum's cleaned booktext vs. the library's OCR Word file, for the same items."""
import difflib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from pipeline.text_measure import clean_docx, library_note_fields  # noqa: E402

WORD = re.compile(r"[\wऀ-෿]+")

for path in sorted((REPO / "data/ocr_docx_compare").glob("*.docx")):
    srno = path.stem
    data = path.read_bytes()
    lib = "\n".join(clean_docx(data))
    qtext = (REPO / "data/text_extract" / f"{srno}.txt").read_text(encoding="utf-8")
    a, b = WORD.findall(qtext), WORD.findall(lib)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    same = sum(m.size for m in sm.get_matching_blocks())
    note = library_note_fields(data)
    print(f"{srno}  Quantum {len(qtext):>8,} chars {len(a):>7,} words | eLibrary {len(lib):>8,} chars {len(b):>7,} words"
          f" | shared words in order: {same / max(len(a), 1):.3f} of Quantum, {same / max(len(b), 1):.3f} of eLibrary"
          f" | OCR made {note.get('ocr_created')}")
    diffs = [(a[i1:i2], b[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op == "replace"][:4]
    for x, y in diffs:
        print(f"      {' '.join(x)[:50]!r} -> {' '.join(y)[:50]!r}")
