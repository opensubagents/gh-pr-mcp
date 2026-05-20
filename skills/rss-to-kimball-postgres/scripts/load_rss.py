#!/usr/bin/env python3
"""load_rss.py — INTENTIONAL STUB (not a generic loader).

================================================================
THIS FILE IS A STUB. IT WILL NOT LOAD YOUR FEED IF YOU RUN IT.
================================================================

The skill ships no monolithic generic loader because every RSS feed is
shaped slightly differently — a "one size fits all" loader either drops
signal or carries dead code. The intended workflow is:

    1. Run scripts/profile_rss.py <your-feed-url>
    2. Copy examples/claude-code-whats-new/ to your project dir
    3. Specialize the copied load.py per the new profile
    4. Run YOUR copy of load.py (not this file)

Running this file directly prints the usage banner and exits with code 2.
Importing this file as a module raises RuntimeError so a test suite can't
silently treat it as the production loader.
"""
from __future__ import annotations
import sys

USAGE = """\
load_rss.py is a stub that points at the per-feed loader in examples/.

To load the Claude Code 'What\\'s new' feed:
    python3 examples/claude-code-whats-new/load.py <feed-url-or-path>

To create a loader for a new feed:
    1. python3 scripts/profile_rss.py <new-feed-url> > path/to/profile.txt
    2. cp -r examples/claude-code-whats-new/ path/to/your-project/
    3. edit path/to/your-project/{ddl/create_all.sql, load.py} per the new profile.
    4. python3 path/to/your-project/load.py <new-feed-url>
"""


def main() -> int:
    print(USAGE, file=sys.stderr)
    return 2


def __getattr__(name: str):  # noqa: N807
    """Trip any caller that tries to import this stub as a real loader."""
    raise RuntimeError(
        "load_rss is an intentional stub — see module docstring. "
        "Use examples/claude-code-whats-new/load.py or your specialized copy."
    )


if __name__ == "__main__":
    sys.exit(main())
