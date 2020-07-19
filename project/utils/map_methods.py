from asyncpg import Connection
from aioredis import RedisConnection
from aioredis.commands import Pipeline
import random
from . import db


async def dumps_game_objects(conn: RedisConnection, game_objects: list) -> None:
    pipe = Pipeline(conn)
    await db.dump_game_objects(pipe=pipe, game_objects=game_objects)
    await pipe.execute()


def gen_random_pos(pos: tuple, min_c: int = 20, max_c: int = 70) -> tuple:
    x_coord: int = random.choice(
        [random.randint(pos[0] - max_c, pos[0] - min_c), random.randint(pos[0] + min_c, pos[0] + max_c)])
    y_coord: int = random.choice(
        [random.randint(pos[1] - max_c, pos[1] - min_c), random.randint(pos[1] + min_c, pos[1] + max_c)])
    return x_coord, y_coord


def make_square(x_coord: int, y_coord: int, width: int, height: int) -> tuple:
    min_coors = (x_coord - (width // 2), y_coord - (height // 2))
    max_coors = (x_coord + (width // 2), y_coord + (height // 2))
    return min_coors, max_coors


async def find_new_spawn_pos(conn: Connection) -> tuple:
    while True:
        random_objects = await db.get_random_map_object_pos(conn=conn, limit=10)
        if not random_objects:
            return 0, 0
        for random_pos in random_objects:
            new_pos = gen_random_pos(pos=random_pos["pos"])
            square = make_square(x_coord=new_pos[0], y_coord=new_pos[1], width=40, height=40)
            is_busy = await db.check_relay_for_free(conn=conn, pos=square)
            if is_busy:
                continue
            is_busy = await db.check_pos_for_free(conn, new_pos)
            if is_busy:
                continue
            return new_pos
