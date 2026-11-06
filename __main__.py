"""Allow ``python3 -m codeforge``."""

import sys

from .app import main

if __name__ == "__main__":
    sys.exit(main())
