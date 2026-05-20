# RSS / Atom anatomy — what to expect from feeds

A practical field reference for parsing feeds for warehouse loading. Focused on the gotchas, not on RFC completeness.

## The two formats

| | RSS 2.0 | Atom 1.0 |
|---|---|---|
| Root | `<rss version="2.0"><channel>` | `<feed xmlns="http://www.w3.org/2005/Atom">` |
| Item | `<item>` | `<entry>` |
| ID | `<guid>` (string, optional `isPermaLink`) | `<id>` (URI, required, must be unique forever) |
| Date | `<pubDate>` (RFC 822) | `<published>` and/or `<updated>` (RFC 3339) |
| Body | `<description>` (often summary) + `<content:encoded>` (full HTML) | `<content type="html">` |
| Author | `<dc:creator>` (Dublin Core) | `<author><name>…</name></author>` |
| Tag | `<category>` (1+) | `<category term="…">` |

Most "RSS" feeds in the wild are RSS 2.0 with namespaced extensions (`content:`, `dc:`, `atom:`). Plan for both shapes; your parser should accept either with minor branching.

## Item fields you'll typically need

- **id / guid** — the natural key. Prefer it over `link` because links can change.
- **pubDate / published** — primary date dimension link. Always parse to a timezone-aware timestamp; Postgres `timestamptz` handles the rest.
- **updated** — distinct from `pubDate`. If present, drives change detection alongside content hash.
- **title** — usually short; SCD2 candidate.
- **link** — primary outbound URL for the item; fragment-y in some feeds.
- **content:encoded / content** — HTML body. Where most of the real signal lives.
- **category** — repeatable. Sometimes a controlled tag, sometimes free text, sometimes (as in the Claude Code feed) a structured value range.
- **enclosure** (RSS) / `link rel="enclosure"` (Atom) — media attachments. Often omitted; build a dim only if present.

## Namespaces — handle them

Python's `xml.etree.ElementTree` requires explicit namespace mapping:

```python
NS = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'dc':      'http://purl.org/dc/elements/1.1/',
    'atom':    'http://www.w3.org/2005/Atom',
    'media':   'http://search.yahoo.com/mrss/',
}
item.find('content:encoded', NS)
```

Skipping namespaces silently drops fields. The profiler always shows tag names with namespace stripped — useful for inventory but not for parsing.

## `content:encoded` gotchas

- It's HTML, not text. Strip with `bs4` (or `html.parser`) before measuring `len`.
- It's wrapped in `<![CDATA[…]]>` — `ElementTree` returns the inner text directly.
- Inline `<code>`, `<strong>`, `<a href>` are signal. Mention counts of these can become measures.
- HTML entities (`&amp;`, `&#8211;`) are decoded by the parser. Don't double-decode.
- Some feeds emit Markdown wrapped in `<![CDATA[…]]>` and call it HTML. Detect by absence of `<` after `[CDATA[`.

## Date parsing

RSS 2.0 uses RFC 822: `Sat, 09 May 2026 02:56:31 GMT`. Atom uses RFC 3339: `2026-05-09T02:56:31Z`.

```python
from email.utils import parsedate_to_datetime  # RFC 822
from datetime import datetime                   # RFC 3339 via fromisoformat after Z→+00:00
```

Always store as `timestamptz` with TZ preserved; never strip to naive timestamps before Postgres sees them.

## Idempotency keys for upserts

The right composite for RSS items:
- **Natural key:** `(feed_url, guid)`. If `guid` is missing, fall back to `(feed_url, link)` — many feeds without `guid` have stable links per item.
- **Change detection key:** SHA-256 over canonicalized `(title, content_html, category, pub_date)`. Store as `row_hash` on the SCD2 dim.

## Feed-level fields

- **`channel/title`**, **`channel/description`**, **`channel/link`** — feed identity. Lives on `dim_feed_source` (SCD1).
- **`channel/lastBuildDate`** — capture in `event_feed_snapshot` to detect feed-level updates without re-parsing items.
- **`atom:link rel="self"`** — the feed's canonical URL, useful as the deduping key in `dim_feed_source`.

## Anti-patterns

- **Trusting the `description` field.** Some feeds put summaries there, some put full HTML, some leave it empty. Always check both `description` and `content:encoded`.
- **Treating `link` as a key.** Links rewrite (CMS migrations, tracking params, fragment changes). `guid` first, link second.
- **Ignoring updates.** A feed that re-publishes an item with a fixed typo will silently drift from your warehouse if you skip change detection.
- **Hard-coding namespace prefixes.** The prefix is per-document; the URL is the constant. Always look up by URL.
