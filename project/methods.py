from asyncpg.pool import Pool
from asyncpg.connection import Connection


async def register(pool: Pool, GP_ID: str, username: str):
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.fetchval("")



methods = {
    "register": register
}