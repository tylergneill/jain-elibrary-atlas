"""Every networked entry point this Atlas has, and none of them live here.

Acquisition lives in the private `rivulet` package. This module is the one
place this repo names it, and it never requires it.

## What this repo can still do alone

Everything that reads a cache already on disk:

    make parse-catalog    (and, once written: count-sizes, build, changelog,
                           audit, serve)

What needs rivulet is anything that crosses the network:

    make clearance        earn Cloudflare clearance for jainqq.org in a browser
    make fetch-catalog    the 34-page Quantum catalog
    make fetch-text       one booktext JSON per item with text

**A checkout without rivulet cannot acquire anything.** That is accepted and
deliberate. If `data/` is already populated, every offline target works.

## The exit code

    0   it worked
    1   it ran and failed
    2   the machinery is not installed
"""

import sys

EXIT_NOT_INSTALLED = 2

_MISSING = """\
acquisition machinery not installed.

Fetching lives in the private `rivulet` package, which is not present in this
environment. Everything that reads the existing cache still runs.

To enable it:  pip install -e ../../rivulet[selenium]
"""


def _load(dotted: str, name: str):
    """Import `name` from a rivulet module, or exit 2 if the package is absent.

    Imported at the point of use rather than at module load, so that merely
    importing this shim never depends on rivulet being installed.
    """
    try:
        module = __import__(dotted, fromlist=[name])
    except ImportError:
        print(_MISSING, file=sys.stderr)
        raise SystemExit(EXIT_NOT_INSTALLED)
    return getattr(module, name)


def clearance_main():
    return _load("rivulet.extract.jainquantum.clearance_cli", "main")


def fetch_catalog_main():
    return _load("rivulet.extract.jainquantum.fetch_catalog", "main")


def fetch_text_main():
    return _load("rivulet.extract.jainquantum.fetch_fulltext", "main")


def library_login_main():
    return _load("rivulet.extract.jainelibrary.login_cli", "main")


def fetch_ocr_docx_main():
    return _load("rivulet.extract.jainelibrary.fetch_ocr_docx", "main")


def available() -> bool:
    """Whether networked work is possible here. Asks, rather than exits."""
    try:
        import rivulet  # noqa: F401
    except ImportError:
        return False
    return True
