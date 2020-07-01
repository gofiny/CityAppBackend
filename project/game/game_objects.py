from asyncpg import Record
from asyncpg.pool import Pool
from asyncpg.connection import Connection
from time import time
from utils import exceptions, sql, raw_sql


actions = {
    "cut_wood": ["woodcutter"],
    "cut_stone": ["stonecutter"],
    "carry": ["woodcutter", "stonecutter"]
}

available_tasks = {
    "woodcutter": ["cut_wood"],
    "stonecutter": ["cut_stone"]
}


class GameResource:
    def __init__(self, name: str, count: int):
        self.name = name
        self.count = count

    def _can_subtract(self, count: int) -> bool:
        return self.count >= count

    def add(self, count: int) -> None:
        self.count += count

    def subtract(self, count: int) -> None:
        if not self._can_subtract:
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
    def __init__(self, uuid: str, name: str, object_type: str, level: int = 1):
        self.uuid = uuid
        self.name = name
        self.object_type = object_type
        self.level = level

    @staticmethod
    async def create_table(conn: Connection):
        async with conn.transaction():
            await conn.execute(raw_sql.create_table_game_objects)

    @staticmethod
    async def create_new_object(conn: Connection, **kwargs) -> __class__:
        game_object = await sql.create_new_user(conn, **kwargs)
        return __class__(**game_object)


class StaticObject(GameObject):
    def __init__(self, **kwargs):
        super().__init__(object_type="static", **kwargs)


class GeneratedObject(GameObject):
    def __init__(self, health: int, **kwargs):
        self.health = health
        super().__init__(object_type="generated", **kwargs)


class PawnObject(GameObject):
    def __init__(self, speed: int, power: int, max_tasks: int, **kwargs):
        self.speed = speed,
        self.power = power
        self.max_tasks = max_tasks
        super().__init__(object_type="pawn", **kwargs)


class Woodcutter(PawnObject):
    def __init__(self, db_woodcutter: Record):
        super().__init__(
            uuid=db_woodcutter["uuid"],
            name=db_woodcutter["name"],
            speed=db_woodcutter["speed"],
            power=db_woodcutter["power"],
            max_tasks=db_woodcutter["max_tasks"],
            level=db_woodcutter["level"]
        )


class MapObject:
    def __init__(self, db_object: Record):
        self.uuid = db_object["uuid"]
        self.coors = db_object["coors"]
        self.game_object = db_object["game_object"]
        self.owner = db_object["owner"]
        self.is_free = db_object["is_free"]


class Map:
    def __init__(self):
        pass
