#!/usr/bin/env bash
# dev_teardown.sh — stop the ephemeral Postgres started for dev_loop testing.
#
# Resolves ISSUE-10 from the 2026-05-09 session manifest: during the build
# of this skill an ephemeral Postgres 16 server was started at /tmp/pgdata
# on port 5433 and never stopped. This script is the canonical teardown.
#
# Usage:
#   ./scripts/dev_teardown.sh                 # uses defaults below
#   PGDATA=/path/to/pgdata ./scripts/dev_teardown.sh
#
# Defaults match what dev_loop.sh's docs imply for an ephemeral sandbox:
#   PGDATA=/tmp/pgdata
#   PGPORT=5433
#
# Idempotent: if no server is running, it just reports that and exits 0.

set -euo pipefail

PGDATA="${PGDATA:-/tmp/pgdata}"
PGPORT="${PGPORT:-5433}"

echo "[teardown] PGDATA=$PGDATA PGPORT=$PGPORT"

if [[ ! -d "$PGDATA" ]]; then
  echo "[teardown] no data dir at $PGDATA — nothing to stop."
  exit 0
fi

if ! pg_ctl -D "$PGDATA" status >/dev/null 2>&1; then
  echo "[teardown] no running server in $PGDATA — done."
  exit 0
fi

echo "[teardown] stopping..."
pg_ctl -D "$PGDATA" -m fast stop || pg_ctl -D "$PGDATA" -m immediate stop

if [[ "${PURGE:-0}" == "1" ]]; then
  echo "[teardown] PURGE=1 set — removing $PGDATA"
  rm -rf "$PGDATA"
fi

echo "[teardown] done."
