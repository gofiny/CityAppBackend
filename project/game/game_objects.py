from asyncpg import Record
from asyncpg.pool import Pool
from asyncpg.connection import Connection
from time import time
from utils import exceptions, sql, raw_sql


class GameResource:
    def __init__(self, name: str, count: int):
        self.name = name
        self.count = count

    def _can_subtruct(self, count: int) -> bool:
        return self.count >= count

    def add(self, count: int) -> None:
        self.count += count

    def subtract(self, count: int) -> None:
        if not self._can_subtruct:
            raise exceptions.ResNotEnough
        self.count -= count
    
    def __eq__(self, other: "GameResource"):
        if other.__class__ is not self.__class__:
            return NotImplemented
        return self.name == other.name and self.count == other.count

    def __lt__(self, other: "GameResource"):
        if other.__class__ is not self.__class__:
            return NotImplemented
        return self.name == other.name and self.count < other.count

    def __le__(self, other: "GameResource"):
        if other.__class__ is not self.__class__:
            return NotImplemented
        return self.name == other.name and self.count <= other.count

    def __add__(self, other: "GameResource"):
        if other.__class__ is not self.__class__:
            return NotImplemented
        if other.name != self.name:
            return NotImplemented
        return self.count + other.count

    def __iadd__(self, other: "GameResource"):
        if other.__class__ is not self.__class__:
            return NotImplemented
        if other.name != self.name:
            return NotImplemented
        self.count += other.count
        return self


class User:
    def __init__(self, db_user: Record):
        self.uuid = db_user["uuid"]
        self.gp_id = db_user["gp_id"]
        self.username = db_user["username"]
        self.reg_time = db_user["reg_time"]
        self.money = GameResource("money", db_user["money"])
        self.wood = GameResource("wood", db_user["wood"])
        self.stones = GameResource("stones", db_user["stones"])
        self._save_time = time()

    async def update_save_time(self):
        self._save_time = time()

    async def save_resources(self, conn: Connection):
        async with conn.transaction():
            await sql.save_user_resources(
                conn=conn,
                uuid=self.uuid,
                money=self.money.count,
                wood=self.wood.count,
                stones=self.stones.count
            )
            await self.update_save_time()

    @staticmethod
    async def create_table(conn: Connection):
        async with conn.transaction():
            await conn.execute(raw_sql.create_table_user)

    @staticmethod
    async def create_new_user(conn: Connection, gp_id: str, username: str) -> "User":
        user = await sql.create_new_user(conn, gp_id, username)
        return User(**user)

    def __eq__(self, other: "User"):
        if other.__class__ is not self.__class__:
            return NotImplemented
        return self.uuid == other.uuid


class GameObject:
    def __init__(self, uuid: str, health: int):
        self.uuid = uuid
        self.name = object
        self.object_type = "static"
        self.health = health


class Map:
    def __init__(self):
        pass