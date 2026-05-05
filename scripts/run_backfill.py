import asyncio, asyncpg, os

async def run():
    url = os.environ['DATABASE_URL'].replace('+asyncpg', '').replace('postgresql://', 'postgresql://127.0.0.1:65432/')
    conn = await asyncpg.connect(url)
    try:
        sql = open('scripts/backfill_search_vector.sql').read()
        await conn.execute(sql)
        print('Backfill SQL executed successfully')
    finally:
        await conn.close()

asyncio.run(run())
