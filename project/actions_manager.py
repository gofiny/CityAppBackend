import asyncio
import asyncpg
from time import time
from asyncpg.connection import Connection
import config
from staff import (
    get_finished_actions,
    get_resname_by_taskname,
    delete_actions,
    delete_tasks,
    add_res_to_player
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
    tasks_to_delete = []
    for action in actions:
        pawn_power = action["pawn_power"]
        go_health = action["go_health"]
        if action["pa_name"] == "carry":
            if go_health <= 0:
                loot_count = pawn_power
                tasks_to_delete.append(action["pt_uuid"])
            else:
                loot_count = go_health + pawn_power
            await add_res_to_player(
                conn=conn,
                storage_uuid=action["storage_uuid"],
                task_name=action["task_name"],
                res_count=loot_count
            )
        elif action["pa_name"] != "walk":
            new_health = go_health - pawn_power
        
        actions_to_delete.append(action["pa_uuid"])

    await delete_actions(conn=conn, actions=tuple(actions_to_delete))
    await delete_tasks(conn=conn, tasks=tuple(tasks_to_delete))
    
