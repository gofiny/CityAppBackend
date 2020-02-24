import asyncio
import asyncpg
from time import time
from asyncpg.connection import Connection
import config
from staff import (
    get_finished_actions,
    get_resname_by_taskname,
    delete_actions
)


async def connect():
    '''Подключается к БД и возваращает объект соединения'''
    conn = await asyncpg.connect(
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
        host=config.HOST
    )
    return conn


async def actions_handler(conn: Connection):
    actions = await get_finished_actions(conn=conn)
    actions_to_delete = []
    for action in actions:
        pawn_power = action["pawn_power"]
        if action["pa_name"] == "carry":
            pass
        elif action["pa_name"] != "walk":
            new_health = action["go_health"] - pawn_power
        
        actions_to_delete.append(action["pa_uuid"])

    await delete_actions(conn=conn, actions=tuple(actions_to_delete))
    