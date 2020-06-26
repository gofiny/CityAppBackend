from asyncpg.pool import Pool
from game import game_objects


async def create_databases(pool: Pool):
    async with pool.acquire() as connection:
        await game_objects.User.create_table(connection=connection)
