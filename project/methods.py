from asyncpg.pool import Pool
from asyncpg.connection import Connection
from utils import sql, exceptions
from uuid import uuid4
from time import time
from game.game_objects import User


async def register(server, ws, gp_id: str, username: str):
    pool = server.pg_pool
    async with pool.acquire() as conn:
        async with conn.transaction():
            user = await conn.fetchrow(sql.check_reg_user % (gp_id, username))
            if user:
                if user["gp_id"] == gp_id:
                    raise exceptions.UserExceptions.GPIDAlreadyExist
                else:
                    raise exceptions.UserExceptions.UsernameAlreadyExist
            user = User(await conn.fetchrow(sql.create_new_user % (uuid4(), gp_id, username, int(time()))))
            print(user.uuid)

methods = {
    "register": register
}