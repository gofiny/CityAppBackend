from asyncpg.pool import Pool
from game import game_objects


async def create_databases(pool: Pool):
    async with pool.acquire() as conn:
        await game_objects.User.create_table(conn=conn)
        await game_objects.GameObject.create_table(conn=conn)
