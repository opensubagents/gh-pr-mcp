-- examples/claude-code-whats-new/ddl/create_all.sql
-- Idempotent. Safe to re-run. Uses CREATE … IF NOT EXISTS throughout.
-- Target: Postgres 16. Compatible with 14/15.
--
-- Model: star schema for the Claude Code "What's new" RSS feed
-- (https://code.claude.com/docs/en/whats-new/rss.xml)
-- Profile: 7 items, all 6 fields populated, weekly cadence, version ranges in
-- category, ~444 chars body avg, 1 outbound link / 2.7 strong / 3.4 code per item.
--
-- See examples/claude-code-whats-new/model.md for the per-table rationale.

CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- for digest() in SCD2 hashing

-- ---------------------------------------------------------------------------
-- DIMENSIONS
-- ---------------------------------------------------------------------------

-- dim_feed_source — SCD1
-- Why SCD1: feed identity (channel/title, channel/description) changes rarely
-- and historical values aren't a query target. Overwrite is fine.
CREATE TABLE IF NOT EXISTS dim_feed_source (
  feed_sk        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  feed_url       text   NOT NULL UNIQUE,           -- atom:link rel=self, the natural key
  channel_title  text   NOT NULL,
  channel_desc   text,
  channel_link   text,
  generator      text,
  copyright      text,
  inserted_at    timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz NOT NULL DEFAULT now()
);

-- dim_date — conformed dim, generated once
CREATE TABLE IF NOT EXISTS dim_date (
  date_key      integer  PRIMARY KEY,             -- yyyymmdd
  full_date     date     NOT NULL UNIQUE,
  year          smallint NOT NULL,
  quarter       smallint NOT NULL,
  month         smallint NOT NULL,
  day           smallint NOT NULL,
  iso_year      smallint NOT NULL,
  iso_week      smallint NOT NULL,
  day_of_week   smallint NOT NULL,                -- 1=Mon … 7=Sun (isodow)
  is_weekend    boolean  NOT NULL
);

-- dim_release — SCD2
-- Why SCD2: title and (especially) content can be edited after publication.
-- We want history so that "what did Week 19 say on May 9 vs May 16?" is
-- answerable. row_hash drives change detection.
CREATE TABLE IF NOT EXISTS dim_release (
  release_sk    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  feed_sk       bigint NOT NULL REFERENCES dim_feed_source(feed_sk),
  guid          text   NOT NULL,                  -- natural key
  title         text   NOT NULL,
  link          text,
  category_raw  text,                              -- e.g. 'v2.1.128–v2.1.136'
  content_html  text,
  content_text  text,                              -- HTML-stripped, for measuring
  pub_date      timestamptz NOT NULL,
  valid_from    timestamptz NOT NULL DEFAULT now(),
  valid_to      timestamptz,                       -- NULL = current
  is_current    boolean NOT NULL DEFAULT true,
  row_hash      bytea   NOT NULL,                  -- digest(canonicalized SCD2 attrs)
  UNIQUE (feed_sk, guid, valid_from)
);
CREATE INDEX IF NOT EXISTS ix_dim_release_current
  ON dim_release (feed_sk, guid) WHERE is_current;

-- dim_version — SCD1
-- Why SCD1: a version string ('v2.1.128') is a fact about the world; it doesn't
-- change after the fact. Storing one row per version is enough.
CREATE TABLE IF NOT EXISTS dim_version (
  version_sk    bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  version       text   NOT NULL UNIQUE,           -- 'v2.1.128'
  major         smallint NOT NULL,
  minor         smallint NOT NULL,
  patch         smallint NOT NULL
);

-- dim_link — SCD1
-- Why SCD1: a URL is what it is. If the host or path is "wrong" it's a parse
-- bug, not a historical change worth versioning.
CREATE TABLE IF NOT EXISTS dim_link (
  link_sk       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  url           text   NOT NULL UNIQUE,
  scheme        text   NOT NULL,
  host          text   NOT NULL,
  path          text
);

-- dim_term — SCD1
-- Why SCD1: terms extracted from <strong>/<code> are content snippets; we treat
-- the term itself as identity. (kind, term) is the natural key.
CREATE TABLE IF NOT EXISTS dim_term (
  term_sk       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  term          text   NOT NULL,
  kind          text   NOT NULL CHECK (kind IN ('strong', 'code')),
  UNIQUE (kind, term)
);

-- ---------------------------------------------------------------------------
-- FACTS
-- ---------------------------------------------------------------------------

-- fact_release_announcement — event-grained
CREATE TABLE IF NOT EXISTS fact_release_announcement (
  fact_sk            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  release_sk         bigint NOT NULL REFERENCES dim_release(release_sk),
  feed_sk            bigint NOT NULL REFERENCES dim_feed_source(feed_sk),
  date_key           integer NOT NULL REFERENCES dim_date(date_key),
  snapshot_id        bigint NOT NULL,                 -- FK added below after event table exists
  -- additive measures
  content_text_len   integer NOT NULL,
  content_html_len   integer NOT NULL,
  n_links            integer NOT NULL,
  n_strong_terms     integer NOT NULL,
  n_code_terms       integer NOT NULL,
  n_versions_in_range integer NOT NULL,
  inserted_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_fact_release_release ON fact_release_announcement (release_sk);
CREATE INDEX IF NOT EXISTS ix_fact_release_date    ON fact_release_announcement (date_key);

COMMENT ON TABLE fact_release_announcement IS
  'Grain: one row per RSS item per feed-snapshot load. '
  'A re-load against an unchanged item produces a new row only when the '
  'companion event_release_seen.change_type is in (new, updated). '
  'change_type=unchanged does not insert a new fact row.';

-- ---------------------------------------------------------------------------
-- BRIDGES
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS bridge_release_version (
  release_sk         bigint NOT NULL REFERENCES dim_release(release_sk),
  version_sk         bigint NOT NULL REFERENCES dim_version(version_sk),
  position_in_range  smallint NOT NULL,                -- 0 = range start, ascending
  PRIMARY KEY (release_sk, version_sk)
);

CREATE TABLE IF NOT EXISTS bridge_release_link (
  release_sk         bigint NOT NULL REFERENCES dim_release(release_sk),
  link_sk            bigint NOT NULL REFERENCES dim_link(link_sk),
  position           smallint NOT NULL,                -- order in body
  link_text          text,
  PRIMARY KEY (release_sk, link_sk, position)
);

CREATE TABLE IF NOT EXISTS bridge_release_term (
  release_sk         bigint NOT NULL REFERENCES dim_release(release_sk),
  term_sk            bigint NOT NULL REFERENCES dim_term(term_sk),
  mention_count      smallint NOT NULL,
  PRIMARY KEY (release_sk, term_sk)
);

-- ---------------------------------------------------------------------------
-- EVENTS
-- ---------------------------------------------------------------------------

-- event_feed_snapshot — one row per feed fetch
CREATE TABLE IF NOT EXISTS event_feed_snapshot (
  snapshot_id      bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  feed_sk          bigint NOT NULL REFERENCES dim_feed_source(feed_sk),
  observed_at      timestamptz NOT NULL DEFAULT now(),
  last_build_date  timestamptz,
  n_items          integer NOT NULL,
  bytes            integer NOT NULL,
  http_status      smallint
);

COMMENT ON TABLE event_feed_snapshot IS
  'Grain: one row per feed fetch. observed_at is when WE saw it; '
  'last_build_date is what the feed claimed in <lastBuildDate>.';

-- event_release_seen — one row per (snapshot, release)
CREATE TABLE IF NOT EXISTS event_release_seen (
  event_id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  snapshot_id      bigint NOT NULL REFERENCES event_feed_snapshot(snapshot_id),
  feed_sk          bigint NOT NULL REFERENCES dim_feed_source(feed_sk),
  release_sk       bigint NOT NULL REFERENCES dim_release(release_sk),
  guid             text   NOT NULL,
  change_type      text   NOT NULL CHECK (change_type IN ('new', 'updated', 'unchanged')),
  observed_at      timestamptz NOT NULL DEFAULT now(),
  UNIQUE (snapshot_id, guid)
);

COMMENT ON TABLE event_release_seen IS
  'Grain: one row per (snapshot_id, release natural key). '
  'change_type=new on first sight, updated when row_hash differs from prior, '
  'unchanged otherwise. Drives whether fact_release_announcement gets a row.';

-- Belated FK: facts reference snapshots
ALTER TABLE fact_release_announcement
  DROP CONSTRAINT IF EXISTS fk_fact_snapshot;
ALTER TABLE fact_release_announcement
  ADD CONSTRAINT fk_fact_snapshot
  FOREIGN KEY (snapshot_id) REFERENCES event_feed_snapshot(snapshot_id);
