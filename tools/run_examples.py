# -*- coding: utf-8 -*-
import sys
from textwrap import dedent


if __name__ == "__main__":
    print(
        dedent(
            """Nipype examples have been moved to niflow-nipype1-examples.

Install with: pip install niflow-nipype1-examples"""
        )
    )
    if sys.argv[1:]:
        print(
            "Run this command with: niflow-nipype1-examples " + " ".join(sys.argv[1:])
        )
    sys.exit(1)
