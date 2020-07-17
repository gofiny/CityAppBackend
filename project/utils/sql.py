from asyncpg.connection import Connection
from asyncpg import Record
from time import time
from uuid import uuid4
from . import raw_sql
from typing import (
    Optional,
    List
)


async def get_user_info_or_none(conn: Connection, gp_id: str, username: str) -> Optional[Record]:
    return await conn.fetchrow(raw_sql.check_reg_user, gp_id, username)


async def create_new_user(conn: Connection, gp_id: str, username: str, spawn_pos: tuple) -> Record:
    return await conn.fetchrow(raw_sql.create_new_user, uuid4(), gp_id, username, int(time()), spawn_pos)


async def save_user_resources(conn: Connection, uuid: uuid4, money: int, wood: int, stones: int) -> None:
    await conn.execute(raw_sql.save_user_resources, money, wood, stones, uuid)


async def create_new_game_object(conn: Connection, name: str,
                                 object_type: str, level: int = 1,
                                 health: Optional[int] = None,
                                 speed: Optional[float] = None,
                                 power: Optional[int] = None,
                                 max_tasks: Optional[int] = None) -> Record:
    game_object = await conn.fetchrow(
        raw_sql.create_game_object, uuid4(), name, object_type, level, health, speed, power, max_tasks)
    return game_object


async def get_random_map_object_pos(conn: Connection, limit: int = 1) -> List[Optional[Record]]:
    return await conn.fetch(raw_sql.get_random_object_pos, limit)


async def check_relay_for_free(conn: Connection, pos: tuple) -> Optional[tuple]:
    return await conn.fetchval(raw_sql.check_relay_for_free % (pos[0][0], pos[0][1], pos[1][0], pos[1][1]))


async def check_pos_for_free(conn: Connection, pos: tuple) -> Optional[tuple]:
    return await conn.fetchval(raw_sql.check_pos_for_free, pos)


async def set_game_objects_on_map(conn: Connection, objects: list) -> None:
    await conn.executemany(raw_sql.set_game_object_on_map, objects)


async def get_game_object_by_gp_id(conn: Connection, gp_id: str, object_name=str) -> Record:
    return await conn.fetchrow(raw_sql.get_game_object_by_gp_id, gp_id, object_name)


async def get_user_by_gp_id(conn: Connection, gp_id: str) -> Record:
    return await conn.fetchrow(raw_sql.get_user_by_gp_id, gp_id)


async def get_all_game_objects_by_gp_id(conn: Connection, gp_id: str) -> List[Optional[Record]]:
    return await conn.fetch(raw_sql.get_all_game_objects_by_gp_id, gp_id)
