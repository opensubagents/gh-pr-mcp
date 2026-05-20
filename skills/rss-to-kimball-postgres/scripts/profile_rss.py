#!/usr/bin/env python3
"""profile_rss.py — read a feed and tell you what's actually in it.

Always run this BEFORE writing any DDL. The skill's whole point is "model the
data you have, not the data you imagine."

Usage:
    python3 profile_rss.py <url-or-path>
    python3 profile_rss.py https://code.claude.com/docs/en/whats-new/rss.xml
    python3 profile_rss.py path/to/feed.xml

Output: a plain-text profile printed to stdout. Pipe to a file to commit
alongside the schema:
    python3 profile_rss.py <url> > examples/<feed>/profile.txt

Pattern inference caveat (ISSUE-8 from the 2026-05-09 session manifest):
The "value pattern" lines collapse digit runs to `9` and letter runs to `a`
to reveal structured shapes (e.g. `9999-99-99` for ISO dates). This is a
useful first signal — it tells you "this field looks like a date" or "these
ids are all 8-char hex" — but it is NOT a substitute for human review:
  * It cannot tell apart "ISO-8601 date" from "comma-less integer-tuple".
  * It loses non-ASCII structure (Unicode letters all map to `a`).
  * Whitespace and punctuation pass through literally, so trailing periods
    or trailing whitespace will show up as separate "patterns" for the
    same logical value.
Use it to spot which fields ARE structured. Do not rely on it for choosing
column types.
"""
from __future__ import annotations
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc":      "http://purl.org/dc/elements/1.1/",
    "atom":    "http://www.w3.org/2005/Atom",
    "media":   "http://search.yahoo.com/mrss/",
}
HTML_TAG_RE = re.compile(r"<[^>]+>")
LINK_RE = re.compile(r'<a\s+[^>]*href="([^"]+)"', re.I)
STRONG_RE = re.compile(r"<strong>(.*?)</strong>", re.I | re.S)
CODE_RE = re.compile(r"<code>(.*?)</code>", re.I | re.S)


def fetch(src: str) -> bytes:
    if src.startswith(("http://", "https://")):
        req = urllib.request.Request(src, headers={"User-Agent": "rss-profiler/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    return Path(src).read_bytes()


def localname(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def infer_pattern(value: str) -> str:
    """Crude regex inference for value patterns — useful for spotting
    structured strings like 'v2.1.128–v2.1.136'."""
    if not value:
        return "<empty>"
    s = value.strip()
    if len(s) > 80:
        return f"<long text, {len(s)} chars>"
    pat = []
    for c in s:
        if c.isdigit():
            pat.append("9")
        elif c.isalpha():
            pat.append("A" if c.isupper() else "a")
        else:
            pat.append(c)
    # collapse runs
    out = []
    for c in pat:
        if out and out[-1].endswith(c) and c in "9aA":
            out[-1] += c
        else:
            out.append(c)
    return "".join(out)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    src = sys.argv[1]
    raw = fetch(src)
    root = ET.fromstring(raw)

    # Detect format
    is_atom = root.tag.endswith("}feed") or root.tag == "feed"
    is_rss = root.tag == "rss" or "rss" in root.tag.lower()
    fmt = "Atom 1.0" if is_atom else ("RSS 2.0" if is_rss else "unknown")

    # Channel / feed level
    channel = root.find("channel") if not is_atom else root
    item_tag = "entry" if is_atom else "item"
    items = channel.findall(item_tag) if channel is not None else []

    print(f"=== source ===")
    print(f"  {src}")
    print(f"  {len(raw):,} bytes, {fmt}")
    print()

    # Channel-level fields
    print(f"=== feed-level fields ===")
    if channel is not None:
        for c in channel:
            if localname(c.tag) == item_tag:
                continue
            text = (c.text or "").strip()
            if text:
                preview = text if len(text) <= 80 else text[:77] + "..."
                print(f"  {localname(c.tag):<20} {preview}")
            elif c.attrib:
                print(f"  {localname(c.tag):<20} attrs={dict(c.attrib)}")
            else:
                print(f"  {localname(c.tag):<20} <empty>")
    print()

    # Item count + tag inventory
    print(f"=== items: {len(items)} ===")
    print()

    if not items:
        print("(no items found — check the feed format / parser)")
        return 0

    # Tag presence + value patterns across all items
    tag_count: Counter = Counter()
    tag_attrs: dict[str, set[str]] = defaultdict(set)
    tag_patterns: dict[str, Counter] = defaultdict(Counter)
    for it in items:
        seen_in_item = set()
        for c in it:
            n = localname(c.tag)
            seen_in_item.add(n)
            for k in c.attrib:
                tag_attrs[n].add(k)
            text = (c.text or "").strip()
            if text and len(text) <= 80:
                tag_patterns[n][infer_pattern(text)] += 1
        for n in seen_in_item:
            tag_count[n] += 1

    print(f"=== item-level fields (presence: N of {len(items)}) ===")
    for n in sorted(tag_count, key=lambda x: (-tag_count[x], x)):
        attrs = f" attrs={sorted(tag_attrs[n])}" if tag_attrs[n] else ""
        print(f"  {n:<20} {tag_count[n]:>2}/{len(items)}{attrs}")
    print()

    # Value patterns for short fields
    print(f"=== inferred value patterns (short fields) ===")
    for n in sorted(tag_patterns):
        pats = tag_patterns[n]
        if not pats:
            continue
        top = pats.most_common(3)
        rendered = ", ".join(f"{p}×{c}" for p, c in top)
        print(f"  {n:<20} {rendered}")
    print()

    # pubDate range
    dates = []
    for it in items:
        for tag in ("pubDate", "{http://www.w3.org/2005/Atom}published",
                    "{http://www.w3.org/2005/Atom}updated"):
            el = it.find(tag)
            if el is not None and el.text:
                try:
                    dates.append(parsedate_to_datetime(el.text))
                except (TypeError, ValueError):
                    pass
                break
    if dates:
        dates.sort()
        print(f"=== date range ===")
        print(f"  earliest: {dates[0].isoformat()}")
        print(f"  latest:   {dates[-1].isoformat()}")
        print(f"  span:     {(dates[-1] - dates[0]).days} days, {len(dates)} dates")
        print()

    # content:encoded analysis
    bodies = []
    for it in items:
        ce = it.find("content:encoded", NS)
        if ce is None and is_atom:
            ce = it.find("{http://www.w3.org/2005/Atom}content")
        if ce is not None and ce.text:
            bodies.append(ce.text)
    if bodies:
        text_lens = [len(unescape(HTML_TAG_RE.sub("", b))) for b in bodies]
        link_counts = [len(LINK_RE.findall(b)) for b in bodies]
        strong_counts = [len(STRONG_RE.findall(b)) for b in bodies]
        code_counts = [len(CODE_RE.findall(b)) for b in bodies]
        print(f"=== content:encoded analysis ===")
        print(f"  bodies present: {len(bodies)}/{len(items)}")
        print(f"  text length:    min={min(text_lens)}, max={max(text_lens)}, "
              f"avg={sum(text_lens)//len(text_lens)}")
        print(f"  links per body: min={min(link_counts)}, max={max(link_counts)}, "
              f"total={sum(link_counts)}")
        print(f"  <strong> per:   min={min(strong_counts)}, max={max(strong_counts)}, "
              f"total={sum(strong_counts)}")
        print(f"  <code> per:     min={min(code_counts)}, max={max(code_counts)}, "
              f"total={sum(code_counts)}")
        print()

    # Sample first item
    print(f"=== first item (verbatim, namespaces stripped) ===")
    first = items[0]
    for c in first:
        n = localname(c.tag)
        text = (c.text or "").strip()
        if text:
            preview = text if len(text) <= 200 else text[:197] + "..."
            print(f"  {n}: {preview}")
        elif c.attrib:
            print(f"  {n}: <attrs={dict(c.attrib)}>")
    print()

    # Suggested next steps
    print(f"=== suggested next steps ===")
    print(f"  1. Read references/kimball-cheatsheet.md for terminology.")
    print(f"  2. Pick a grain for the fact table (default: one row per item per snapshot).")
    print(f"  3. List dimensions: dim_date, dim_release (SCD2), dim_feed_source (SCD1).")
    print(f"  4. Add bridge / extra dims ONLY if a query needs them.")
    print(f"  5. Generate DDL using references/postgres16-idioms.md as the template.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
