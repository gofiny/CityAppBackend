from asyncpg.pool import Pool
from asyncpg.connection import Connection


async def register(server, ws, gp_id: str, username: str):
    pool = server.pg_pool
    async with pool.acquire() as conn:
        async with conn.transaction():
            result = await conn.fetchval(f"SELECT * from users where gp_id='{gp_id}'")
            print(result)


methods = {
    "register": register
}