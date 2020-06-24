from asyncpg import Record
from asyncpg.pool import Pool
from asyncpg.connection import Connection
from time import time
from utils import exceptions, sql


class GameResource:
    def __init__(self, name: str, count: int):
        self.name = name
        self.count = count

    def _can_subtruct(self, count) -> bool:
        return self.count >= count

    def add(self, count: int) -> None:
        self.count + count

    def subtract(self, count: int) -> None:
        if not self._can_subtruct:
            raise exceptions.ResNotEnough
        self.count - count


class User:
    def __init__(self, db_user: Record):
        self.uuid = db_user["uuid"]
        self.gp_id = db_user["gp_id"]
        self.username = db_user["username"]
        self.money = GameResource("money", db_user["money"])
        self.wood = GameResource("wood", db_user["wood"])
        self.stones = GameResource("stones", db_user["stones"])
        self._save_time = time()

    async def update_save_time(self):
        self._save_time = time()

    async def save_resources(self, conn: Connection):
        async with conn.transaction():
            await conn.execute(
                sql.save_user_resources % (self.money, self.wood, self.stones, self.uuid))
        await self.update_save_time()

    @staticmethod
    async def create_table(pool: Pool):
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(sql.create_table_user)

