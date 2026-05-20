-- examples/claude-code-whats-new/ddl/drop_all.sql
-- DEV ONLY. NEVER run this in production.
-- Drops every object in the current schema's warehouse model so create_all.sql
-- can rebuild from scratch. Reverse-FK order, IF EXISTS + CASCADE.

SET client_min_messages = WARNING;

-- Events (no incoming FKs) drop first
DROP TABLE IF EXISTS event_release_seen        CASCADE;
DROP TABLE IF EXISTS event_feed_snapshot       CASCADE;

-- Bridges
DROP TABLE IF EXISTS bridge_release_term       CASCADE;
DROP TABLE IF EXISTS bridge_release_link       CASCADE;
DROP TABLE IF EXISTS bridge_release_version    CASCADE;

-- Facts
DROP TABLE IF EXISTS fact_release_announcement CASCADE;

-- Dimensions
DROP TABLE IF EXISTS dim_term                  CASCADE;
DROP TABLE IF EXISTS dim_link                  CASCADE;
DROP TABLE IF EXISTS dim_version               CASCADE;
DROP TABLE IF EXISTS dim_release               CASCADE;
DROP TABLE IF EXISTS dim_date                  CASCADE;
DROP TABLE IF EXISTS dim_feed_source           CASCADE;
