from uuid import uuid4
from utils import sql, exceptions
from utils.map_methods import find_new_spawn_pos
from game.game_objects import User, Woodcutter, WoodcutterHouse


async def register(server, gp_id: str, username: str) -> dict:
    async with server.pg_pool.acquire() as conn:
        async with conn.transaction():
            user = await sql.get_user_info_or_none(conn, gp_id, username)
            if user:
                if user["gp_id"] == gp_id:
                    raise exceptions.UserExceptions.GPIDAlreadyExist
                else:
                    raise exceptions.UserExceptions.UsernameAlreadyExist
            spawn_pos = await find_new_spawn_pos(conn=conn)
            user = await User.create_new_user(conn, gp_id, username, spawn_pos=spawn_pos)
            woodcutter = await Woodcutter.create_new(conn)
            woodcutter_house = await WoodcutterHouse.create_new(conn)
            await sql.set_game_objects_on_map(conn=conn, objects=[
                (uuid4(), (spawn_pos[0] + 1, spawn_pos[1]), woodcutter.uuid, user.uuid, False),
                (uuid4(), spawn_pos, woodcutter_house.uuid, user.uuid, False)
            ])
            return {"is_new_user": True, "spawn_pos": list(spawn_pos)}

methods = {
    "register": register
}