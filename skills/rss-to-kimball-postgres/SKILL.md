---
name: rss-to-kimball-postgres
description: "Decompose any RSS / Atom feed into a Kimball-style dimensional model (fact tables, SCD dimensions, event tables) targeting Postgres 16, with a bash-driven dev loop. Use whenever the user wants to turn a feed into a warehouse schema, mentions Kimball / dimensional modeling / star schema in the context of feeds or news data, asks to 'decompose' or 'normalize' an XML/RSS source into Postgres tables, or pastes an `rss.xml` URL and wants tables out the other side. Always profile the feed before designing the schema — the simplest model that fits the actual fields wins."
license: Proprietary
compatibility: "claude.ai web/mobile chat or any environment with bash + Python 3.10+. No DB connection required to design the schema; psycopg[binary] or psql needed only when the user wants to actually run the loaders against Postgres 16."
metadata:
  author: subagentcowork
  version: "1.1.0"
  surface: claude.ai
  scope: rss-to-postgres-dimensional-modeling
---

# rss-to-kimball-postgres

Turn an RSS feed into a Kimball-style dimensional model in Postgres 16. The skill optimizes for two things: (1) **read the actual data before writing any DDL**, and (2) **a tight bash dev loop** so the user can rebuild from scratch in one keystroke while iterating.

## The non-negotiable opening move: profile the feed

Never write DDL based on what RSS *usually* looks like. Different feeds have wildly different shapes — some have `category` as a controlled tag list, some use it for version ranges, some omit it; `content:encoded` may be plain text, sanitized HTML, or markdown-in-HTML; `dc:creator` exists in some feeds and not others.

Run the profiler first:

```bash
python3 scripts/profile_rss.py <url-or-path>
```

It prints: item count, every unique item-level child tag observed, attribute presence per element, value patterns (regex inferred), pubDate range, and a sample item. Use that profile — not assumptions — to drive schema design.

## Designing the model — simplest representation first

For a feed of N items, start with this minimum and *only* add tables when you can name a query that needs them:

| Table | Type | Grain |
|---|---|---|
| `dim_date` | conformed dim | one row per calendar day |
| `dim_release` (or `dim_post`, `dim_article`) | SCD2 | one current + zero-or-more historical rows per `guid` |
| `fact_<feed>_announcement` | event-grained fact | one row per item per snapshot load |
| `event_feed_snapshot` | event | one row per feed fetch (capture `lastBuildDate`, item count) |
| `event_<item>_seen` | event | one row per (item, snapshot) — change type ∈ {new, updated, unchanged} |

That's the floor. Anything else (bridge tables for tags, link dimensions, term dimensions) earns its place by answering a real question. See `references/kimball-cheatsheet.md` for when to add SCD2, bridges, junk dims, and degenerate dims.

### Grain comment is mandatory

Every fact table starts with a `COMMENT ON TABLE` declaring its grain in plain English. If you can't write the comment, you don't know the grain and you're not ready for the DDL.

```sql
COMMENT ON TABLE fact_release_announcement IS
  'Grain: one row per RSS item per feed-snapshot load. '
  'A re-load with an unchanged item produces a new row only if change_type != unchanged.';
```

### SCD choice — justify per dimension

For each dimension, write one line in the DDL header explaining the SCD choice:

- **SCD1 (overwrite)** — attribute changes don't matter historically. `dim_link.host` for example.
- **SCD2 (versioned)** — attribute changes need history. `dim_release.title` and `dim_release.content_len` because feed authors do edit posts.
- **SCD3 (previous-value column)** — rarely the right call. Only when exactly one prior value matters for a known query.

Don't reflexively SCD2 everything — extra rows you'll never query are just noise.

## The bash dev loop

Two scripts, run from the project root, idempotent:

```bash
./scripts/dev/drop_all.sh    # DROP TABLE IF EXISTS … CASCADE — fresh rebuild
./scripts/dev/create_all.sh  # CREATE TABLE IF NOT EXISTS …  — safe to re-run
python3 scripts/load_rss.py <url>   # fetch, parse, upsert
```

Or one wrapper:

```bash
./scripts/dev_loop.sh <url>  # drop → create → load
```

`dev_loop.sh` is for the iteration phase. Once the model stabilizes, drop drops out and the loop becomes `create_all.sh` (idempotent) + `load_rss.py` (idempotent upserts). Production should never call `drop_all.sh`.

### Connection convention

All scripts read `PG*` env vars (`PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`) and a single `DEV_SCHEMA` variable (default `rss_dev`). Schemas keep dev data out of `public` and let multiple feeds coexist.

```bash
export PGHOST=localhost PGPORT=5432 PGUSER=dev PGDATABASE=warehouse
export DEV_SCHEMA=whats_new_dev
./scripts/dev_loop.sh https://code.claude.com/docs/en/whats-new/rss.xml
```

## Workflow per session

1. **Profile the feed** with `scripts/profile_rss.py`. Show the user the inventory.
2. **Propose a model** — start from the minimum table set above; add only what the profile justifies. Walk the user through SCD choice per dimension.
3. **Generate DDL** — write `dev/drop_all.sql` and `dev/create_all.sql` to the user's project. Use the templates in `references/postgres16-idioms.md`.
4. **Wrap in bash** — `dev/drop_all.sh` and `dev/create_all.sh` are thin `psql -f …` wrappers (see `scripts/dev/`). `dev_loop.sh` chains them with the loader.
5. **Generate the loader** — `scripts/load_rss.py` parses the feed and upserts. Use the parser pattern from `examples/claude-code-whats-new/load.py` as the template.
6. **Run the worked example** if the user wants concreteness — pointed at the bundled `examples/claude-code-whats-new/` it produces a working schema and load against any Postgres 16 instance.

## What lives where

```
rss-to-kimball-postgres/
├── SKILL.md                         ← this file
├── references/
│   ├── kimball-cheatsheet.md        ← fact/dim/SCD/bridge/junk dim definitions, when to use
│   ├── rss-anatomy.md               ← RSS 2.0 + Atom field inventory, namespace gotchas
│   └── postgres16-idioms.md         ← IF EXISTS patterns, IDENTITY surrogates, FK/CASCADE, dim_date generator
├── scripts/
│   ├── profile_rss.py               ← profile any feed → field inventory + value patterns
│   ├── load_rss.py                  ← reusable parser + upsert template
│   ├── gen_dim_date.sql             ← seed a 50-year dim_date in one shot
│   ├── dev_loop.sh                  ← drop → create → load wrapper
│   └── dev/
│       ├── drop_all.sh.template     ← copy + edit per project
│       └── create_all.sh.template   ← copy + edit per project
└── examples/
    └── claude-code-whats-new/       ← end-to-end worked example for the Claude Code feed
        ├── profile.txt              ← committed output of profile_rss.py for this feed
        ├── model.md                 ← the schema decisions explained
        ├── ddl/
        │   ├── drop_all.sql
        │   └── create_all.sql
        └── load.py                  ← the loader specialized for this feed
```

## Outcomes — what good looks like

A run is good when:

1. **Profile happens first.** No DDL is proposed before `profile_rss.py` output is shown to the user.
2. **Grain is explicit.** Every fact table has a `COMMENT ON TABLE` declaring its grain.
3. **SCD is justified.** Each dimension's DDL header explains why SCD1 vs SCD2 vs SCD3.
4. **Idempotent dev loop.** `create_all.sh` and `load_rss.py` can run repeatedly without duplicating rows or erroring on existing objects.
5. **`drop_all.sh` is dev-only.** It's never invoked from prod paths and the script header says so.
6. **Simplest model wins.** No table exists in the schema that can't be tied to a real query in the user's head.
7. **Kimball, not Inmon.** Star schema with conformed dims; not third-normal-form everything.

## What never to do

- **Never propose DDL without profiling the feed.** "RSS usually has X" is wrong often enough to matter.
- **Never SCD2 by default.** Pick per dimension with a one-line justification.
- **Never bury grain.** It goes in a `COMMENT ON TABLE`, not in a separate doc the next reader won't open.
- **Never use `DROP TABLE` without `IF EXISTS`** in dev scripts. Crashing midway through `drop_all.sh` shouldn't break the next run.
- **Never use `CREATE TABLE` without `IF NOT EXISTS`** in `create_all.sh`. The script must be re-runnable.
- **Never inline secrets.** Connection always via `PG*` env vars.

## Next reads

- `references/kimball-cheatsheet.md` — terminology and when each pattern applies
- `references/rss-anatomy.md` — RSS / Atom field reference, namespace handling, content:encoded gotchas
- `references/postgres16-idioms.md` — IF EXISTS / IDENTITY / dim_date / surrogate key patterns
- `examples/claude-code-whats-new/model.md` — fully worked example you can copy and adapt
