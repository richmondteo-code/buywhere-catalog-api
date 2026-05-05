import asyncio, asyncpg, os, sys
from urllib.parse import urlparse, urlunparse

async def verify():
    raw = os.environ['DATABASE_URL']
    clean = raw.replace('+asyncpg', '')
    parsed = urlparse(clean)
    url = urlunparse(parsed._replace(netloc=f'{parsed.username}:{parsed.password}@127.0.0.1:65432'))
    try:
        row = await conn.fetchrow('SELECT version_num FROM alembic_version')
        print(f'Alembic version: {row["version_num"]}')
        rows = await conn.fetchrow(
            'SELECT count(*) as total, '
            'count(*) FILTER (WHERE search_vector IS NULL) as null_search, '
            'count(*) FILTER (WHERE title_search_vector IS NULL) as null_title '
            'FROM products'
        )
        print(f'Products: {rows["total"]}, NULL search: {rows["null_search"]}, NULL title: {rows["null_title"]}')
        if rows['null_search'] > 0 or rows['null_title'] > 0:
            print('WARNING: NULL search vectors still exist!')
            sys.exit(1)
        print('Migration verification passed.')
    finally:
        await conn.close()

asyncio.run(verify())
