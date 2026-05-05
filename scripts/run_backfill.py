import asyncio, asyncpg, os
from urllib.parse import urlparse, urlunparse

async def run():
    raw = os.environ['DATABASE_URL']
    clean = raw.replace('+asyncpg', '')
    parsed = urlparse(clean)
    new = urlunparse(parsed._replace(netloc=f'{parsed.username}:{parsed.password}@127.0.0.1:65432'))
    url = new
    conn = await asyncpg.connect(url)
    try:
        sql = open('scripts/backfill_search_vector.sql').read()
        await conn.execute(sql)
        print('Backfill SQL executed successfully')
    finally:
        await conn.close()

asyncio.run(run())
