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
    add_res_to_player,
    add_work_pawn_action,
    add_walk_pawn_action,
    delete_map_objects
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
    objects_to_delete = []
    for action in actions:
        pawn_power = action["pawn_power"]
        res_health = action["res_health"]
        action_name = action["pa_name"]
        if action_name == "carry":
            await add_res_to_player(
                conn=conn,
                storage_uuid=action["storage_uuid"],
                task_name=action["task_name"],
                res_count=action["res_count"]
            )
            if action["mo_uuid"] is None:
                tasks_to_delete.append(action["pt_uuid"])
            else:
                await add_work_pawn_action(
                conn=conn,
                task_uuid=action["pt_uuid"],
                action_name=action["task_name"]
            )
        elif action_name == "walk":
            await add_work_pawn_action(
                conn=conn,
                task_uuid=action["pt_uuid"],
                action_name=action["task_name"]
            )
        else:
            new_health = res_health - pawn_power
            if new_health <= 0:
                loot_count = new_health + pawn_power
                objects_to_delete.append(action["mo_uuid"])
            else:
                loot_count = pawn_power
            await add_walk_pawn_action(
                conn=conn,
                task_uuid=action["pt_uuid"],
                action_name="carry",
                res_count=loot_count
            )
        
        actions_to_delete.append(action["pa_uuid"])

    if actions_to_delete:
        await delete_actions(conn=conn, actions=tuple(actions_to_delete))
    if tasks_to_delete:
        await delete_tasks(conn=conn, tasks=tuple(tasks_to_delete))
    if objects_to_delete:
        await delete_map_objects(conn=conn, objects=tuple(objects_to_delete))
