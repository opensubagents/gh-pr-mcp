# Postgres 16 idioms — for the dev-loop dimensional warehouse

Patterns this skill leans on. Postgres 16 adds incremental improvements over 15 (logical replication, MERGE refinements, monitoring) but for warehouse modeling the key features have been there since 12.

## `IF EXISTS` / `IF NOT EXISTS` everywhere

Dev scripts are re-run constantly. Both halves of the loop must be idempotent.

### Drop scripts

```sql
-- drop_all.sql — dev only
SET client_min_messages = WARNING;

DROP TABLE IF EXISTS event_release_seen        CASCADE;
DROP TABLE IF EXISTS event_feed_snapshot       CASCADE;
DROP TABLE IF EXISTS bridge_release_term       CASCADE;
DROP TABLE IF EXISTS bridge_release_link       CASCADE;
DROP TABLE IF EXISTS bridge_release_version    CASCADE;
DROP TABLE IF EXISTS fact_release_announcement CASCADE;
DROP TABLE IF EXISTS dim_term                  CASCADE;
DROP TABLE IF EXISTS dim_link                  CASCADE;
DROP TABLE IF EXISTS dim_version               CASCADE;
DROP TABLE IF EXISTS dim_release               CASCADE;
DROP TABLE IF EXISTS dim_date                  CASCADE;
DROP TABLE IF EXISTS dim_feed_source           CASCADE;
```

Drop in reverse-FK order. `CASCADE` covers anything the dev attached (views, indexes via dependencies). For prod migrations use Liquibase / Flyway / Atlas, not this.

### Create scripts

```sql
CREATE TABLE IF NOT EXISTS dim_date (
  date_key   integer PRIMARY KEY,             -- yyyymmdd
  full_date  date    NOT NULL UNIQUE,
  year       smallint NOT NULL,
  quarter    smallint NOT NULL,
  month      smallint NOT NULL,
  day        smallint NOT NULL,
  iso_year   smallint NOT NULL,
  iso_week   smallint NOT NULL,
  day_of_week smallint NOT NULL,
  is_weekend boolean NOT NULL
);
```

Indexes get `IF NOT EXISTS` too:

```sql
CREATE INDEX IF NOT EXISTS ix_fact_release_date
  ON fact_release_announcement (date_key);
```

## Surrogate keys — `GENERATED ALWAYS AS IDENTITY`

Use this, not `serial`. `IDENTITY` is the SQL-standard form, prevents accidental inserts of explicit values, and survives `pg_dump --restore` more cleanly.

```sql
release_sk bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

Use `bigint` for surrogate keys even on tiny dims; you cannot grow `int` → `bigint` without a rewrite.

## `dim_date` — generate once, never touch

```sql
INSERT INTO dim_date
SELECT
  to_char(d, 'YYYYMMDD')::int  AS date_key,
  d                             AS full_date,
  extract(year     FROM d)::smallint,
  extract(quarter  FROM d)::smallint,
  extract(month    FROM d)::smallint,
  extract(day      FROM d)::smallint,
  extract(isoyear  FROM d)::smallint,
  extract(week     FROM d)::smallint,
  extract(isodow   FROM d)::smallint,
  extract(isodow   FROM d) IN (6, 7) AS is_weekend
FROM generate_series('2000-01-01'::date, '2050-12-31'::date, '1 day') AS d
ON CONFLICT (date_key) DO NOTHING;
```

50 years × 365 = ~18K rows. Trivial. Run once after `create_all.sh`; thereafter `ON CONFLICT DO NOTHING` makes it a no-op.

## SCD2 with row hash + close-and-insert

```sql
-- Find changes via hash diff
WITH incoming AS (
  SELECT $1::text AS guid, $2::text AS title, $3::text AS link,
         digest($2 || '|' || coalesce($3,''), 'sha256') AS new_hash
),
current AS (
  SELECT release_sk, row_hash FROM dim_release
   WHERE guid = (SELECT guid FROM incoming) AND is_current
),
to_close AS (
  UPDATE dim_release SET valid_to = now(), is_current = false
   WHERE release_sk IN (
     SELECT release_sk FROM current
     WHERE row_hash IS DISTINCT FROM (SELECT new_hash FROM incoming)
   )
  RETURNING release_sk
)
INSERT INTO dim_release (guid, title, link, valid_from, row_hash)
SELECT i.guid, i.title, i.link, now(), i.new_hash
FROM incoming i
WHERE NOT EXISTS (
  SELECT 1 FROM dim_release d
  WHERE d.guid = i.guid AND d.is_current AND d.row_hash = i.new_hash
);
```

`digest()` requires `CREATE EXTENSION IF NOT EXISTS pgcrypto;` — put that in `create_all.sql`.

> **⚠ Hash protocol parity.** The example above uses `'|'` as a separator and only two fields — it illustrates Postgres SCD2 syntax, **not** the canonical row-hash this skill's loader uses. The actual loader (`examples/claude-code-whats-new/load.py`) computes the hash in Python with separator `'\u241F'` (U+241F SYMBOL FOR UNIT SEPARATOR) over four fields in fixed order: `title`, `content_html`, `category`, `pub_date`. If you migrate any portion of the ETL to SQL-side hashing, mirror the Python protocol exactly or every existing row will be marked changed on the first run. The contract is pinned by `scripts/test_scd2_hash.py`.

## Upserts — `INSERT … ON CONFLICT … DO UPDATE`

For SCD1 dims:

```sql
INSERT INTO dim_link (url, host, path)
VALUES ($1, $2, $3)
ON CONFLICT (url) DO UPDATE
  SET host = EXCLUDED.host, path = EXCLUDED.path
RETURNING link_sk;
```

`MERGE` works in 15+ but `INSERT … ON CONFLICT … RETURNING` is more idiomatic for single-row upserts that return the surrogate.

## Foreign keys

Always declare them. `NOT VALID` initially is fine if loading historical data:

```sql
ALTER TABLE fact_release_announcement
  ADD CONSTRAINT fk_fact_release_release
  FOREIGN KEY (release_sk) REFERENCES dim_release(release_sk) NOT VALID;
ALTER TABLE fact_release_announcement
  VALIDATE CONSTRAINT fk_fact_release_release;
```

Never skip them in dev — the bugs you'll catch (orphaned facts, mistyped joins) are exactly what FKs exist for.

## Schema-per-feed

```sql
CREATE SCHEMA IF NOT EXISTS whats_new_dev;
SET search_path TO whats_new_dev;
```

Lets multiple feeds coexist in one database during development. Drop the schema with `DROP SCHEMA IF EXISTS … CASCADE` for a true clean slate when needed.

## Connection from bash + Python

Bash:
```bash
psql -v ON_ERROR_STOP=1 -f scripts/dev/drop_all.sql
psql -v ON_ERROR_STOP=1 -f scripts/dev/create_all.sql
```

Python (`psycopg[binary]`):
```python
import psycopg, os
conn = psycopg.connect(  # reads PG* env vars by default
    autocommit=False,
    options=f"-c search_path={os.environ.get('DEV_SCHEMA','public')}"
)
```

`ON_ERROR_STOP=1` ensures `psql` returns non-zero on the first failure so bash `set -e` actually catches errors.

## Postgres-version pinning

This skill targets Postgres 16. Patterns above also work on 14/15. They will *not* work on 11 or earlier (no `IDENTITY` syntax, no `MERGE`).
