"""令 `python -m cloudsams_tools ...` 等同 `cloudsams ...`。"""
import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
