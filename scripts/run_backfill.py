#!/usr/bin/env python3
import os, subprocess, sys, re

raw = os.environ['DATABASE_URL']
# Parse postgresql://user:password@host:port/dbname
m = re.match(r'postgresql(?:\+asyncpg)?://([^:]+):([^@]+)@[^/]+/(\S+)', raw)
if not m:
    print(f'ERROR: could not parse DATABASE_URL: {raw}', file=sys.stderr)
    sys.exit(1)
user, password, dbname = m.group(1), m.group(2), m.group(3)

env = os.environ.copy()
env['PGPASSWORD'] = password

sql_path = os.path.join(os.path.dirname(__file__), 'backfill_search_vector.sql')
result = subprocess.run(
    ['psql', '-h', '127.0.0.1', '-p', '65432', '-U', user, '-d', dbname, '-f', sql_path, '-q'],
    env=env, capture_output=True, text=True
)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
sys.exit(result.returncode)
