import asyncio
import asyncpg
from time import time
from asyncpg.connection import Connection
import config
import staff


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
    actions = await staff.get_finished_actions(conn=conn)
    actions_to_delete = []
    tasks_to_delete = []
    objects_to_delete = []
    pawn_for_check = []
    for action in actions:
        pawn_power = action["pawn_power"]
        res_health = action["res_health"]
        action_name = action["pa_name"]
        if action_name == "carry":
            await staff.add_res_to_player(
                conn=conn,
                storage_uuid=str(action["storage_uuid"]),
                task_name=action["task_name"],
                res_count=action["res_count"]
            )
            if action["mo_uuid"] is None:
                tasks_to_delete.append(str(action["pt_uuid"]))
                pawn_for_check.append(str(action["pt_pawn"]))
            else:
                await staff.add_walk_pawn_action(
                    conn=conn,
                    task_uuid=str(action["pt_uuid"]),
                )
        elif action_name == "walk":
            await staff.add_work_pawn_action(
                conn=conn,
                task_uuid=str(action["pt_uuid"]),
                action_name=action["task_name"]
            )
        else:
            new_health = res_health - pawn_power
            if new_health <= 0:
                loot_count = new_health + pawn_power
                objects_to_delete.append(str(action["mo_uuid"]))
            else:
                loot_count = pawn_power
                await staff.change_object_health(
                    conn=conn,
                    go_uuid=action["res_uuid"],
                    new_health=new_health
                )
            await staff.add_walk_pawn_action(
                conn=conn,
                task_uuid=str(action["pt_uuid"]),
                action_name="carry",
                res_count=loot_count
            )
        
        actions_to_delete.append(str(action["pa_uuid"]))

    if pawn_for_check: # Add action for next task in queue
        new_tasks = await staff.get_next_tasks(conn=conn, pawns_uuid=tuple(pawn_for_check))
        for task in new_tasks:
            await staff.add_walk_pawn_action(
                conn=conn,
                task_uuid=task["pt_uuid"],
                updating=True
            )
    if actions_to_delete:
        await staff.delete_actions(conn=conn, actions=tuple(actions_to_delete))
    if tasks_to_delete:
        await staff.delete_tasks(conn=conn, tasks=tuple(tasks_to_delete))
    if objects_to_delete:
        await staff.delete_map_objects(conn=conn, objects=tuple(objects_to_delete))
  

async def run_actions_handler():
    while True:
        conn = await connect()
        await actions_handler(conn)
        await conn.close()
        asyncio.sleep(1)


async def run_delete_old_tasks():
    while True:
        conn = await connect()
        await staff.delete_old_tasks(conn)
        await conn.close()
        asyncio.sleep(1)

    
if __name__ == "__main__":
    try:
        main_loop = asyncio.get_event_loop()
        asyncio.ensure_future(run_actions_handler())
        asyncio.ensure_future(run_delete_old_tasks())
        main_loop.run_forever()
    finally:
        main_loop.close()
   