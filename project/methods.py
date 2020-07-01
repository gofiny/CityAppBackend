from utils import sql, exceptions
from uuid import uuid4
from time import time
from game.game_objects import User


async def register(server, ws, gp_id: str, username: str):
    pool = server.pg_pool
    async with pool.acquire() as conn:
        async with conn.transaction():
            user = await sql.get_user_info_or_none(conn, gp_id, username)
            if user:
                if user["gp_id"] == gp_id:
                    raise exceptions.UserExceptions.GPIDAlreadyExist
                else:
                    raise exceptions.UserExceptions.UsernameAlreadyExist
            user = await User.create_new_user(conn, gp_id, username)

methods = {
    "register": register
}