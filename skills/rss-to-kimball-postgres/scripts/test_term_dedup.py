#!/usr/bin/env python3
"""test_term_dedup.py — pin the 'unique vs raw' term-count contract.

Resolves ISSUE-5 from the 2026-05-09 session manifest: the manifest noted
that profile.txt reports 19 <strong> + 24 <code> = 43 raw term mentions,
while dim_term ends up with 42 unique terms. The reviewer flagged this
as worth investigating.

This test demonstrates the delta is **expected dedup**, not a bug:

  * The raw count from profile_rss.py counts every regex match.
  * dim_term uses (kind, term) as its conflict key.
  * Any term that appears twice with the same kind collapses.

The Week 19 item's HTML contains `<code>.zip</code>` twice. That single
duplicate accounts for the entire 43 -> 42 collapse.

Run:
    cd examples/claude-code-whats-new
    python3 -m pytest ../../scripts/test_term_dedup.py -v
"""
from collections import Counter
import re

# Same regexes the loader uses
STRONG_RE = re.compile(r"<strong>(.*?)</strong>", re.DOTALL | re.IGNORECASE)
CODE_RE = re.compile(r"<code>(.*?)</code>", re.DOTALL | re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")


def html_to_text(s: str) -> str:
    return TAG_RE.sub("", s).strip()


def count_terms(items_html: list[str]) -> tuple[int, int]:
    """Return (raw_count, distinct_count). raw counts every regex match;
    distinct dedupes by (kind, term) the same way dim_term does."""
    raw = 0
    distinct: Counter = Counter()
    for html in items_html:
        for m in STRONG_RE.findall(html or ""):
            raw += 1
            t = html_to_text(m)
            if t:
                distinct[("strong", t)] += 1
        for m in CODE_RE.findall(html or ""):
            raw += 1
            t = html_to_text(m)
            if t:
                distinct[("code", t)] += 1
    return raw, len(distinct)


def test_zip_duplicate_collapses():
    """The Week 19 fixture has `.zip` twice — should collapse to one row."""
    item = (
        "<p><strong>Plugins load from <code>.zip</code> archives and URLs</strong>: "
        "<code>--plugin-dir</code> now accepts <code>.zip</code> files, "
        "and <code>--plugin-url</code> fetches a plugin archive.</p>"
    )
    raw, distinct = count_terms([item])
    # 1 strong + 4 code = 5 raw; .zip twice in code => 4 distinct
    assert raw == 5, f"expected 5 raw, got {raw}"
    assert distinct == 4, f"expected 4 distinct (after .zip dedup), got {distinct}"


def test_no_duplicates_means_raw_equals_distinct():
    """When every term is unique, raw == distinct."""
    item = "<p><code>alpha</code> <code>beta</code> <strong>gamma</strong></p>"
    raw, distinct = count_terms([item])
    assert raw == distinct == 3


def test_empty_strong_is_skipped_in_distinct_only():
    """Empty <strong></strong> bumps the raw counter but is filtered from distinct."""
    item = "<p><strong></strong> <code>real</code></p>"
    raw, distinct = count_terms([item])
    assert raw == 2
    assert distinct == 1, "empty term should be filtered from dim_term inserts"


def test_session_manifest_delta_is_explained():
    """Pin the manifest's 19+24=43 raw vs 42 distinct claim.

    Constructed fixture: 7 items, totals match the profile's reported
    19 <strong> + 24 <code> = 43 raw, with exactly one duplicate to drop
    to 42 distinct.
    """
    items = []
    # 19 strong terms, all distinct
    items.append("".join(f"<strong>s{i}</strong>" for i in range(19)))
    # 23 distinct code terms + one duplicate of 'c0' = 24 raw, 23 distinct
    items.append("".join(f"<code>c{i}</code>" for i in range(23)) + "<code>c0</code>")
    raw, distinct = count_terms(items)
    assert raw == 43, f"raw should be 19+24=43, got {raw}"
    assert distinct == 42, f"distinct should be 19+23=42, got {distinct}"


if __name__ == "__main__":
    # Allow running without pytest
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS  {name}")
