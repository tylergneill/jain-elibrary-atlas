"""Open the library's own Chrome so its owner can log in by hand.

**The implementation lives in `rivulet`**; see `pipeline/fetch.py`.
"""

from pipeline.fetch import library_login_main

if __name__ == "__main__":
    library_login_main()()
