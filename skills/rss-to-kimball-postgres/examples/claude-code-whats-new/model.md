# Model decisions — Claude Code "What's new" feed

Source: <https://code.claude.com/docs/en/whats-new/rss.xml>
Profile: see `profile.txt` in this directory.

## What the profile told us

- **7 items**, every one with all 6 fields populated. No nullability headaches.
- `category` is always a structured **version range** (`v2.1.128–v2.1.136`), not a free-form tag. Worth exploding into individual versions via a bridge.
- `pubDate` cadence is roughly weekly; the feed identifier is `(feed_url, guid)`.
- `content:encoded` averages 444 chars of text, with **1 outbound link / 2.7 strong / 3.4 code per item** — enough mass that link / term dimensions earn their place.

## Grain (the most important sentence in this doc)

> **One row per RSS item per feed-snapshot load**, conditional on the item being new or updated since the previous snapshot.

`event_release_seen.change_type` is the gate: a fact row is inserted only when `change_type ∈ {new, updated}`. An `unchanged` row stays in the event log but does not duplicate the fact.

## Tables and why each exists

### Dimensions

| Table | SCD | Why |
|---|---|---|
| `dim_feed_source` | SCD1 | Channel metadata (title, description) changes rarely; history isn't a query target. |
| `dim_date` | conformed | Standard. Generated 50 years ahead by `scripts/gen_dim_date.sql`. |
| `dim_release` | **SCD2** | Title and content can be edited post-publication; historical comparison ("what did Week 19 say last month vs now?") is a real question. |
| `dim_version` | SCD1 | A version string is immutable. One row per version observed. |
| `dim_link` | SCD1 | URLs are what they are; corrections are bug fixes, not historical events. |
| `dim_term` | SCD1 | Terms (`<strong>`/`<code>` snippets) are content; identity is `(kind, term)`. |

### Facts

`fact_release_announcement` is the one fact table. Event-grained. Six measures:

- `content_text_len`, `content_html_len` — body weight
- `n_links`, `n_strong_terms`, `n_code_terms` — markup density
- `n_versions_in_range` — derived from the category range (e.g. `v2.1.128–v2.1.136` → 9)

All measures are additive across releases — sum, avg, percentile all make sense.

### Bridges

Each justifies itself with the profile:

- `bridge_release_version` — categories average 7 versions per range × 7 items = 49 rows. Lets you ask "which release announced v2.1.130?"
- `bridge_release_link` — 7 outbound links across 7 items today, but the body could grow. Position-preserving.
- `bridge_release_term` — 19 strong + 24 code = 43 mentions. Lets you ask "which weeks mentioned `--plugin-dir`?"

### Events

- `event_feed_snapshot` — one row per fetch. Captures `lastBuildDate` so we can detect feed-level changes without rescanning items.
- `event_release_seen` — one row per (snapshot, item). `change_type ∈ {new, updated, unchanged}` is the audit trail.

## What we deliberately did NOT model

- **`dim_author`** — feed has no `dc:creator`. Adding a placeholder dim would be ceremony.
- **`dim_geography`** — irrelevant to release announcements.
- **A separate `dim_category`** — `category_raw` lives on `dim_release` as a degenerate column; the structured exploded form is in `dim_version` + `bridge_release_version`. Keeping a `dim_category` *and* the bridge would duplicate the same information.
- **A junk dimension for flags** — there are no boolean flags in the source today.

If any of these become useful (a feed redesign adds authors; we want to bucket categories beyond version ranges), add them then. Don't reserve space speculatively.

## Sample queries the model supports

```sql
-- Most recent release per week
SELECT d.iso_year, d.iso_week, r.title
FROM fact_release_announcement f
JOIN dim_release r USING (release_sk)
JOIN dim_date d   USING (date_key)
WHERE r.is_current
ORDER BY d.iso_year DESC, d.iso_week DESC
LIMIT 10;

-- Which releases mentioned a specific feature?
SELECT r.title, br.mention_count
FROM dim_term t
JOIN bridge_release_term br USING (term_sk)
JOIN dim_release r          USING (release_sk)
WHERE t.term = '--plugin-dir' AND r.is_current
ORDER BY br.mention_count DESC;

-- Did Week 19 ever change?
SELECT title, valid_from, valid_to, is_current,
       length(content_text) AS body_len
FROM dim_release
WHERE guid = '2f9e72f35dcf5dae'
ORDER BY valid_from;

-- Versions covered per week
SELECT r.title,
       min(v.version) AS first_version,
       max(v.version) AS last_version,
       count(*)       AS n_versions
FROM dim_release r
JOIN bridge_release_version brv USING (release_sk)
JOIN dim_version v              USING (version_sk)
WHERE r.is_current
GROUP BY r.title, r.pub_date
ORDER BY r.pub_date DESC;
```

## Iteration

```bash
export PGHOST=localhost PGUSER=dev PGDATABASE=warehouse
export DEV_SCHEMA=whats_new_dev
psql -v ON_ERROR_STOP=1 -c "CREATE SCHEMA IF NOT EXISTS $DEV_SCHEMA;"
psql -v ON_ERROR_STOP=1 -c "SET search_path TO $DEV_SCHEMA;" \
     -f ddl/drop_all.sql \
     -f ddl/create_all.sql \
     -f ../../scripts/gen_dim_date.sql
python3 load.py https://code.claude.com/docs/en/whats-new/rss.xml
```

Or use the wrapper: `../../scripts/dev_loop.sh https://code.claude.com/docs/en/whats-new/rss.xml`.
