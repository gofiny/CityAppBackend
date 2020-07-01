from asyncpg.connection import Connection
from asyncpg import Record
from time import time
from uuid import uuid4
from . import raw_sql
from typing import (
    Optional,
    Union
)


async def get_user_info_or_none(conn: Connection, gp_id: str, username: str) -> Optional[Record]:
    return await conn.fetchrow(raw_sql.check_reg_user % (gp_id, username))


async def create_new_user(conn: Connection, gp_id: str, username: str) -> Record:
    return await conn.fetchrow(raw_sql.create_new_user % (uuid4(), gp_id, username, int(time())))


async def save_user_resources(conn: Connection, uuid: uuid4, money: int, wood: int, stones: int) -> None:
    await conn.execute(raw_sql.save_user_resources % (money, wood, stones, uuid))
