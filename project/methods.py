from utils import sql, exceptions
from game.game_objects import User, Woodcutter, WoodcutterHouse


async def register(server, ws, gp_id: str, username: str):
    async with server.pg_pool.acquire() as conn:
        async with conn.transaction():
            user = await sql.get_user_info_or_none(conn, gp_id, username)
            if user:
                if user["gp_id"] == gp_id:
                    raise exceptions.UserExceptions.GPIDAlreadyExist
                else:
                    raise exceptions.UserExceptions.UsernameAlreadyExist
            user = await User.create_new_user(conn, gp_id, username)
            woodcutter = await Woodcutter.create_new_object(conn)
            woodcutter_house = await WoodcutterHouse.create_new_object(conn)

methods = {
    "register": register
}