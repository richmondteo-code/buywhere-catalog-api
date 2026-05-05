#!/usr/bin/env bash
set -euo pipefail

# run-alembic-migration.sh
# Runs alembic upgrade head against a Cloud SQL database.
# Designed to run in CI/CD (GitHub Actions) or manually with gcloud auth.
#
# Usage:
#   ./scripts/run-alembic-migration.sh [staging|production]
#
# Environment variables (CI/CD):
#   INSTANCE_CONNECTION_NAME   — Cloud SQL instance connection name
#   DATABASE_URL                — Full database connection string
#   GCP_SA_KEY                  — (optional) Service account JSON key
#
# Local usage with gcloud auth:
#   export INSTANCE_CONNECTION_NAME="gaia-calendar-488606:asia-southeast1:buywhere-staging"
#   ./scripts/run-alembic-migration.sh

ENV="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$SCRIPT_DIR"

echo "=== Migration Runner ==="
echo "Environment: ${ENV:-local}"
echo "Working dir: $(pwd)"

# Resolve connection details
if [ "$ENV" = "production" ]; then
  INSTANCE_CONNECTION_NAME="${INSTANCE_CONNECTION_NAME:-buywhere-production:asia-southeast1:buywhere-db}"
elif [ "$ENV" = "staging" ]; then
  INSTANCE_CONNECTION_NAME="${INSTANCE_CONNECTION_NAME:-gaia-calendar-488606:asia-southeast1:buywhere-staging}"
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "ERROR: DATABASE_URL is required"
  echo "Set it to the full postgresql+asyncpg:// connection string"
  exit 1
fi

# Ensure dependencies
export PIP_REQUIRE_VIRTUALENV=false
pip install -q alembic psycopg2-binary cloud-sql-proxy 2>/dev/null || true

# Start Cloud SQL Proxy
PROXY_PORT=65432
echo "Starting Cloud SQL Proxy on port $PROXY_PORT..."
cloud-sql-proxy \
  --auto-iam-authn \
  "$INSTANCE_CONNECTION_NAME" \
  --port "$PROXY_PORT" &
PROXY_PID=$!
trap "kill $PROXY_PID 2>/dev/null; wait $PROXY_PID 2>/dev/null" EXIT
sleep 3

# Verify proxy is running
if ! kill -0 "$PROXY_PID" 2>/dev/null; then
  echo "ERROR: Cloud SQL Proxy failed to start"
  exit 1
fi

echo "Proxy connected. Running alembic upgrade head..."

# Run migration
export DATABASE_URL
alembic upgrade head

echo "=== Migration complete ==="

# Verify
echo "=== Verification ==="
python3 -c "
import asyncio, asyncpg
url = '$DATABASE_URL'.replace('+asyncpg', '')
async def verify():
    conn = await asyncpg.connect(url.replace('postgresql://', 'postgresql://127.0.0.1:$PROXY_PORT/'))
    row = await conn.fetchrow('SELECT version_num FROM alembic_version')
    print(f'Alembic version: {row[\"version_num\"]}')
    rows = await conn.fetchrow('''
        SELECT count(*) as total,
               count(*) FILTER (WHERE search_vector IS NULL) as null_search,
               count(*) FILTER (WHERE title_search_vector IS NULL) as null_title
        FROM products
    ''')
    print(f'Products: {rows[\"total\"]}, NULL search: {rows[\"null_search\"]}, NULL title: {rows[\"null_title\"]}')
    has_trigger = await conn.fetchval(\"SELECT count(*) FROM pg_trigger WHERE tgname = 'trg_products_search_vector'\")
    print(f'Trigger exists: {has_trigger > 0}')
    await conn.close()
asyncio.run(verify())
"
echo "=== Verification complete ==="
