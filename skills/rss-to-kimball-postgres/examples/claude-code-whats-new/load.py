#!/usr/bin/env python3
"""load.py — fetch the Claude Code 'What's new' RSS feed and load it into the
Kimball model defined in ddl/create_all.sql.

This file is BOTH the worked example for this feed AND the template for any
similar feed. To adapt to a different feed:
  1. Run `scripts/profile_rss.py <new-url>` and read the profile.
  2. Adjust EXTRACT_VERSIONS_FROM_CATEGORY (or remove it) to match the new
     feed's category semantics.
  3. Adjust the schema if the new feed has fields this one doesn't.

Usage:
    python3 load.py <feed-url-or-path>

Env:
    PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE   psycopg defaults
    DEV_SCHEMA   schema to write into (default: rss_dev)

Dependencies: psycopg[binary] >= 3.1
"""
from __future__ import annotations
import hashlib
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.parse import urlparse

import psycopg

NS = {
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc":      "http://purl.org/dc/elements/1.1/",
    "atom":    "http://www.w3.org/2005/Atom",
}
HTML_TAG_RE = re.compile(r"<[^>]+>")
LINK_RE     = re.compile(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
STRONG_RE   = re.compile(r"<strong>(.*?)</strong>", re.I | re.S)
CODE_RE     = re.compile(r"<code>(.*?)</code>", re.I | re.S)

VERSION_RE  = re.compile(r"v(\d+)\.(\d+)\.(\d+)")


def fetch_bytes(src: str) -> bytes:
    if src.startswith(("http://", "https://")):
        req = urllib.request.Request(src, headers={"User-Agent": "rss-loader/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    with open(src, "rb") as f:
        return f.read()


def html_to_text(html: str) -> str:
    return unescape(HTML_TAG_RE.sub("", html or ""))


def explode_version_range(category: str) -> list[tuple[str, int, int, int]]:
    """'v2.1.128–v2.1.136' → [('v2.1.128',2,1,128), ('v2.1.129',...), ...].

    For non-range categories returns whatever versions are present
    (or [] if none). The range expansion only triggers when there are exactly
    two version tokens with the same major.minor."""
    matches = VERSION_RE.findall(category or "")
    if not matches:
        return []
    if len(matches) == 2 and matches[0][0] == matches[1][0] and matches[0][1] == matches[1][1]:
        major, minor = int(matches[0][0]), int(matches[0][1])
        lo, hi = int(matches[0][2]), int(matches[1][2])
        if lo > hi:
            lo, hi = hi, lo
        return [(f"v{major}.{minor}.{p}", major, minor, p) for p in range(lo, hi + 1)]
    return [(f"v{a}.{b}.{c}", int(a), int(b), int(c)) for (a, b, c) in matches]


def canonicalize_for_hash(title: str, content_html: str, category: str, pub_date: str) -> bytes:
    payload = "\u241F".join([title or "", content_html or "", category or "", pub_date or ""])
    return hashlib.sha256(payload.encode("utf-8")).digest()


def parse_feed(raw: bytes) -> tuple[dict, list[dict]]:
    root = ET.fromstring(raw)
    ch = root.find("channel")
    feed_meta = {
        "title":      (ch.findtext("title") or "").strip(),
        "desc":       (ch.findtext("description") or "").strip(),
        "link":       (ch.findtext("link") or "").strip(),
        "generator":  (ch.findtext("generator") or "").strip(),
        "copyright":  (ch.findtext("copyright") or "").strip(),
        "last_build": ch.findtext("lastBuildDate"),
        "self_url":   None,
    }
    for atom_link in ch.findall("{http://www.w3.org/2005/Atom}link"):
        if atom_link.attrib.get("rel") == "self":
            feed_meta["self_url"] = atom_link.attrib.get("href")
            break

    items = []
    for it in ch.findall("item"):
        items.append({
            "guid":         (it.findtext("guid") or "").strip(),
            "title":        (it.findtext("title") or "").strip(),
            "link":         (it.findtext("link") or "").strip(),
            "category":     (it.findtext("category") or "").strip(),
            "pub_date":     it.findtext("pubDate"),
            "content_html": (it.find("content:encoded", NS).text
                             if it.find("content:encoded", NS) is not None else ""),
        })
    return feed_meta, items


def upsert_feed_source(cur, feed_url: str, m: dict) -> int:
    cur.execute("""
        INSERT INTO dim_feed_source (feed_url, channel_title, channel_desc,
                                     channel_link, generator, copyright)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (feed_url) DO UPDATE SET
            channel_title = EXCLUDED.channel_title,
            channel_desc  = EXCLUDED.channel_desc,
            channel_link  = EXCLUDED.channel_link,
            generator     = EXCLUDED.generator,
            copyright     = EXCLUDED.copyright,
            updated_at    = now()
        RETURNING feed_sk
    """, (feed_url, m["title"], m["desc"], m["link"], m["generator"], m["copyright"]))
    return cur.fetchone()[0]


def insert_snapshot(cur, feed_sk: int, last_build: str | None, n_items: int, n_bytes: int) -> int:
    lb = parsedate_to_datetime(last_build) if last_build else None
    cur.execute("""
        INSERT INTO event_feed_snapshot (feed_sk, last_build_date, n_items, bytes, http_status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING snapshot_id
    """, (feed_sk, lb, n_items, n_bytes, 200))
    return cur.fetchone()[0]


def upsert_release_scd2(cur, feed_sk: int, item: dict) -> tuple[int, str]:
    """Returns (release_sk, change_type) where change_type ∈ {new, updated, unchanged}."""
    new_hash = canonicalize_for_hash(
        item["title"], item["content_html"], item["category"], item["pub_date"] or "")
    pub_dt = parsedate_to_datetime(item["pub_date"]) if item["pub_date"] else None
    content_text = html_to_text(item["content_html"])

    cur.execute("""
        SELECT release_sk, row_hash
          FROM dim_release
         WHERE feed_sk = %s AND guid = %s AND is_current
    """, (feed_sk, item["guid"]))
    row = cur.fetchone()

    if row is None:
        cur.execute("""
            INSERT INTO dim_release (feed_sk, guid, title, link, category_raw,
                                     content_html, content_text, pub_date,
                                     valid_from, row_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now(), %s)
            RETURNING release_sk
        """, (feed_sk, item["guid"], item["title"], item["link"], item["category"],
              item["content_html"], content_text, pub_dt, new_hash))
        return cur.fetchone()[0], "new"

    current_sk, current_hash = row
    if bytes(current_hash) == new_hash:
        return current_sk, "unchanged"

    # Close current, insert new
    cur.execute("""
        UPDATE dim_release SET valid_to = now(), is_current = false
         WHERE release_sk = %s
    """, (current_sk,))
    cur.execute("""
        INSERT INTO dim_release (feed_sk, guid, title, link, category_raw,
                                 content_html, content_text, pub_date,
                                 valid_from, row_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, now(), %s)
        RETURNING release_sk
    """, (feed_sk, item["guid"], item["title"], item["link"], item["category"],
          item["content_html"], content_text, pub_dt, new_hash))
    return cur.fetchone()[0], "updated"


def upsert_version(cur, version: str, major: int, minor: int, patch: int) -> int:
    cur.execute("""
        INSERT INTO dim_version (version, major, minor, patch)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (version) DO UPDATE SET version = EXCLUDED.version
        RETURNING version_sk
    """, (version, major, minor, patch))
    return cur.fetchone()[0]


def upsert_link(cur, url: str) -> int:
    p = urlparse(url)
    cur.execute("""
        INSERT INTO dim_link (url, scheme, host, path)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE SET url = EXCLUDED.url
        RETURNING link_sk
    """, (url, p.scheme, p.hostname or "", p.path or ""))
    return cur.fetchone()[0]


def upsert_term(cur, term: str, kind: str) -> int:
    cur.execute("""
        INSERT INTO dim_term (term, kind)
        VALUES (%s, %s)
        ON CONFLICT (kind, term) DO UPDATE SET term = EXCLUDED.term
        RETURNING term_sk
    """, (term, kind))
    return cur.fetchone()[0]


def link_release_versions(cur, release_sk: int, versions: list[tuple]):
    cur.execute("DELETE FROM bridge_release_version WHERE release_sk = %s", (release_sk,))
    for pos, (v, mj, mn, p) in enumerate(versions):
        version_sk = upsert_version(cur, v, mj, mn, p)
        cur.execute("""
            INSERT INTO bridge_release_version (release_sk, version_sk, position_in_range)
            VALUES (%s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (release_sk, version_sk, pos))


def link_release_links(cur, release_sk: int, content_html: str):
    cur.execute("DELETE FROM bridge_release_link WHERE release_sk = %s", (release_sk,))
    for pos, (url, text) in enumerate(LINK_RE.findall(content_html or "")):
        link_sk = upsert_link(cur, url)
        cur.execute("""
            INSERT INTO bridge_release_link (release_sk, link_sk, position, link_text)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (release_sk, link_sk, pos, html_to_text(text)))


def link_release_terms(cur, release_sk: int, content_html: str):
    cur.execute("DELETE FROM bridge_release_term WHERE release_sk = %s", (release_sk,))
    counts: Counter = Counter()
    for term in STRONG_RE.findall(content_html or ""):
        counts[("strong", html_to_text(term).strip())] += 1
    for term in CODE_RE.findall(content_html or ""):
        counts[("code", html_to_text(term).strip())] += 1
    for (kind, term), n in counts.items():
        if not term:
            continue
        term_sk = upsert_term(cur, term, kind)
        cur.execute("""
            INSERT INTO bridge_release_term (release_sk, term_sk, mention_count)
            VALUES (%s, %s, %s)
            ON CONFLICT (release_sk, term_sk) DO UPDATE SET
                mention_count = EXCLUDED.mention_count
        """, (release_sk, term_sk, n))


def insert_fact(cur, release_sk: int, feed_sk: int, snapshot_id: int, item: dict, versions: list):
    pub_dt = parsedate_to_datetime(item["pub_date"]) if item["pub_date"] else None
    date_key = int(pub_dt.strftime("%Y%m%d")) if pub_dt else None
    content_text = html_to_text(item["content_html"])
    cur.execute("""
        INSERT INTO fact_release_announcement
          (release_sk, feed_sk, date_key, snapshot_id,
           content_text_len, content_html_len, n_links,
           n_strong_terms, n_code_terms, n_versions_in_range)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        release_sk, feed_sk, date_key, snapshot_id,
        len(content_text), len(item["content_html"] or ""),
        len(LINK_RE.findall(item["content_html"] or "")),
        len(STRONG_RE.findall(item["content_html"] or "")),
        len(CODE_RE.findall(item["content_html"] or "")),
        len(versions),
    ))


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    src = sys.argv[1]
    feed_url = src if src.startswith(("http://", "https://")) else f"file://{os.path.abspath(src)}"
    schema = os.environ.get("DEV_SCHEMA", "rss_dev")

    raw = fetch_bytes(src)
    feed_meta, items = parse_feed(raw)
    print(f"fetched {len(raw):,} bytes, {len(items)} items from {src}")

    with psycopg.connect(autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET search_path TO {schema}")

            feed_sk = upsert_feed_source(cur, feed_url, feed_meta)
            snapshot_id = insert_snapshot(cur, feed_sk, feed_meta["last_build"],
                                          len(items), len(raw))

            counts = {"new": 0, "updated": 0, "unchanged": 0}
            for item in items:
                release_sk, change_type = upsert_release_scd2(cur, feed_sk, item)
                counts[change_type] += 1

                cur.execute("""
                    INSERT INTO event_release_seen (snapshot_id, feed_sk, release_sk,
                                                    guid, change_type)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (snapshot_id, guid) DO NOTHING
                """, (snapshot_id, feed_sk, release_sk, item["guid"], change_type))

                if change_type == "unchanged":
                    continue

                versions = explode_version_range(item["category"])
                link_release_versions(cur, release_sk, versions)
                link_release_links(cur, release_sk, item["content_html"])
                link_release_terms(cur, release_sk, item["content_html"])
                insert_fact(cur, release_sk, feed_sk, snapshot_id, item, versions)

        conn.commit()

    print(f"snapshot {snapshot_id}: "
          f"new={counts['new']}, updated={counts['updated']}, unchanged={counts['unchanged']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
