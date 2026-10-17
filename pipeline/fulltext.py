"""The one place this repo names `rivulet` for text output, and it never requires it.

Writing the corpus out as files is a publishing act and lives in the private
package. This Atlas is public and **runs to completion without it**: the
catalog, the sizes and the tree are here. What rivulet adds is
`data/text_extract/`.

Every rule about the text -- the page splitter, the furniture patterns -- is
in this repo's `pipeline/text_measure.py`, which rivulet imports. So
`count_sizes` measures exactly what the extractor would write, whether or not
the extractor is installed.

    0   it worked
    1   it ran and failed
    2   the machinery is not installed
"""

import sys

EXIT_NOT_INSTALLED = 2

_MISSING = """\
fulltext machinery not installed.

Text extraction lives in the private `rivulet` package, which is not present
in this environment. Everything else runs without it: `make parse-catalog`,
`make count-sizes` and the tree are unaffected.

To enable it:  pip install -e ../../rivulet
"""


def load_extractor():
    try:
        from rivulet.extract.jainquantum.text_extractor import extract_cache
    except ImportError:
        print(_MISSING, file=sys.stderr)
        raise SystemExit(EXIT_NOT_INSTALLED)
    return extract_cache


def load_docx_extractor():
    """The same, for the library's OCR Word files."""
    try:
        from rivulet.extract.jainquantum.text_extractor import extract_docx_cache
    except ImportError:
        print(_MISSING, file=sys.stderr)
        raise SystemExit(EXIT_NOT_INSTALLED)
    return extract_docx_cache


def available() -> bool:
    try:
        import rivulet  # noqa: F401
    except ImportError:
        return False
    return True
