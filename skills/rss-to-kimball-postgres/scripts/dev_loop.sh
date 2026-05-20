#!/usr/bin/env bash
# dev_loop.sh — drop, create, then load. The "iterate fast" wrapper.
#
# Usage:
#   ./scripts/dev_loop.sh <feed-url-or-path> [path/to/example_dir]
#
# Defaults to examples/claude-code-whats-new/ if no example dir is given.
#
# Env (psycopg / psql will pick up PG* automatically):
#   PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
#   DEV_SCHEMA   schema to drop+create+load (default: rss_dev)
#
# This script is DEV ONLY. Production loaders should never call drop_all.sql.

set -euo pipefail

FEED="${1:?usage: dev_loop.sh <feed-url> [example_dir]}"
if [[ -z "${2:-}" ]]; then
  EXAMPLE_DIR="$(dirname "$0")/../examples/claude-code-whats-new"
  echo "[dev_loop] no example_dir given — using bundled default: $EXAMPLE_DIR"
  echo "[dev_loop] (override with: ./scripts/dev_loop.sh <feed-url> path/to/your-example/)"
else
  EXAMPLE_DIR="$2"
  echo "[dev_loop] using example_dir: $EXAMPLE_DIR"
fi
SCHEMA="${DEV_SCHEMA:-rss_dev}"
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

DROP_SQL="$EXAMPLE_DIR/ddl/drop_all.sql"
CREATE_SQL="$EXAMPLE_DIR/ddl/create_all.sql"
GEN_DATE_SQL="$SCRIPTS_DIR/gen_dim_date.sql"
LOADER_PY="$EXAMPLE_DIR/load.py"

for f in "$DROP_SQL" "$CREATE_SQL" "$GEN_DATE_SQL" "$LOADER_PY"; do
  [[ -f "$f" ]] || { echo "missing: $f" >&2; exit 1; }
done

echo "==> ensuring schema $SCHEMA exists"
psql -v ON_ERROR_STOP=1 -c "CREATE SCHEMA IF NOT EXISTS $SCHEMA;" >/dev/null

echo "==> dropping existing tables in $SCHEMA"
PSQL_OPTS=(-v ON_ERROR_STOP=1 -v ON_ERROR_ROLLBACK=on)
psql "${PSQL_OPTS[@]}" -c "SET search_path TO $SCHEMA;" -f "$DROP_SQL"

echo "==> creating tables in $SCHEMA"
psql "${PSQL_OPTS[@]}" -c "SET search_path TO $SCHEMA;" -f "$CREATE_SQL"

echo "==> seeding dim_date"
psql "${PSQL_OPTS[@]}" -c "SET search_path TO $SCHEMA;" -f "$GEN_DATE_SQL" >/dev/null

echo "==> loading $FEED"
DEV_SCHEMA="$SCHEMA" python3 "$LOADER_PY" "$FEED"

echo "==> row counts"
psql "${PSQL_OPTS[@]}" -c "SET search_path TO $SCHEMA;" -c "
SELECT 'dim_feed_source'           AS table, count(*) FROM dim_feed_source
UNION ALL SELECT 'dim_release',                count(*) FROM dim_release
UNION ALL SELECT 'dim_release (current only)', count(*) FROM dim_release WHERE is_current
UNION ALL SELECT 'dim_version',                count(*) FROM dim_version
UNION ALL SELECT 'dim_link',                   count(*) FROM dim_link
UNION ALL SELECT 'dim_term',                   count(*) FROM dim_term
UNION ALL SELECT 'fact_release_announcement',  count(*) FROM fact_release_announcement
UNION ALL SELECT 'bridge_release_version',     count(*) FROM bridge_release_version
UNION ALL SELECT 'bridge_release_link',        count(*) FROM bridge_release_link
UNION ALL SELECT 'bridge_release_term',        count(*) FROM bridge_release_term
UNION ALL SELECT 'event_feed_snapshot',        count(*) FROM event_feed_snapshot
UNION ALL SELECT 'event_release_seen',         count(*) FROM event_release_seen;
"
