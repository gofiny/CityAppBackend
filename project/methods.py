from asyncpg.pool import Pool
from asyncpg.connection import Connection


async def register(pool: Pool, gp_id: str, username: str):
    async with pool.acquire() as connection:
        async with connection.transaction():
            is_exist = await connection.fetchval(f"SELECT gp_id FROM users WHERE gp_id='{gp_id}'")
            if not is_exist:
                pass




methods = {
    "register": register
}