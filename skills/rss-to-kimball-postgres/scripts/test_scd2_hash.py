#!/usr/bin/env python3
"""test_scd2_hash.py — pin the canonical SCD2 row-hash protocol.

Resolves ISSUE-7 from the 2026-05-09 session manifest: the SQL example in
references/postgres16-idioms.md uses `digest($2 || '|' || coalesce($3,''),
'sha256')` — pipe separator, 2 fields. The actual Python loader in
examples/claude-code-whats-new/load.py uses `'\\u241F'.join([title,
content_html, category, pub_date])` then SHA-256. They produce different
hashes for the same row.

This test pins the **Python** protocol as canonical for this skill. If you
ever migrate to a SQL-side hash (or want both ETL paths to coexist), you
must mirror this exact byte sequence in SQL. Anything else will mark every
existing row as 'changed' on the first run.

Canonical contract:
  separator: U+241F SYMBOL FOR UNIT SEPARATOR  (utf-8: 0xE2 0x90 0x9F)
  fields, in order: title, content_html, category, pub_date_string
  null fields: empty string (NOT the literal "None" or NULL)
  encoding: UTF-8, no BOM, no trailing newline
  hash: SHA-256, 32-byte digest (bytea in Postgres)

Run:
    python3 -m pytest scripts/test_scd2_hash.py -v
    # or
    python3 scripts/test_scd2_hash.py
"""
import hashlib

SEP = "\u241F"  # SYMBOL FOR UNIT SEPARATOR


def canonical_hash(title: str, content_html: str, category: str, pub_date: str) -> bytes:
    """The one and only canonical row hash. Matches load.py exactly."""
    payload = SEP.join([title or "", content_html or "", category or "", pub_date or ""])
    return hashlib.sha256(payload.encode("utf-8")).digest()


def test_separator_is_u241f():
    assert SEP == "\u241f"
    assert SEP.encode("utf-8") == b"\xe2\x90\x9f"


def test_known_canonical_bytes():
    """Pin the SHA-256 for a fixture row. If this changes, every SCD2 row in
    every existing database becomes a 'changed' row on next load. Don't.
    """
    h = canonical_hash(
        "Plugins land",
        "<p>Plugins are here.</p>",
        "Release",
        "Mon, 06 May 2026 12:00:00 GMT",
    )
    assert h.hex() == "bc179e9a6a3188e89fdcb43c8c6ddb5f8bb74b69dc73632c9687db815ae71c49"


def test_empty_fields_collapse_to_empty_string():
    """None and '' should hash identically — neither path should leak the
    literal string 'None' into the payload."""
    h_none = canonical_hash(None, None, None, None)
    h_empty = canonical_hash("", "", "", "")
    assert h_none == h_empty


def test_field_order_matters():
    """Swapping title and category must produce a different hash."""
    h1 = canonical_hash("A", "body", "B", "date")
    h2 = canonical_hash("B", "body", "A", "date")
    assert h1 != h2


def test_pipe_protocol_is_incompatible():
    """The SQL example in references/postgres16-idioms.md uses '|' as
    separator. Confirm it produces a different digest — this is why the
    two protocols cannot coexist without explicit alignment."""
    title, body = "x", "y"
    pipe_hash = hashlib.sha256(f"{title}|{body}".encode("utf-8")).digest()
    canonical = hashlib.sha256(f"{title}{SEP}{body}{SEP}{SEP}".encode("utf-8")).digest()
    assert pipe_hash != canonical


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except AssertionError as e:
                print(f"FAIL  {name}: {e}")
                raise
