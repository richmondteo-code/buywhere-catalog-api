#!/usr/bin/env python3
import os, subprocess, sys, re

raw = os.environ['DATABASE_URL']
m = re.match(r'postgresql(?:\+asyncpg)?://([^:]+):([^@]+)@[^/]+/(\S+)', raw)
if not m:
    print(f'ERROR: could not parse DATABASE_URL: {raw}', file=sys.stderr)
    sys.exit(1)
user, password, dbname = m.group(1), m.group(2), m.group(3)

env = os.environ.copy()
env['PGPASSWORD'] = password

queries = {
    'alembic_version': "SELECT version_num FROM alembic_version",
    'null_search_vector': "SELECT count(*) FROM products WHERE search_vector IS NULL",
    'trigger_exists': "SELECT tgname FROM pg_trigger WHERE tgname = 'trg_products_search_vector'",
}

all_ok = True
for label, sql in queries.items():
    result = subprocess.run(
        ['psql', '-h', '127.0.0.1', '-p', '65432', '-U', user, '-d', dbname,
         '-c', sql, '-t', '-A'],
        env=env, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f'ERROR: {label} query failed', file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        all_ok = False
    else:
        output = result.stdout.strip()
        print(f'{label}: {output}')

if not all_ok:
    sys.exit(1)
print('Migration verification passed.')
