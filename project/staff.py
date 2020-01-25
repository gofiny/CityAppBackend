'''Подкапотка запросов к БД'''
from json.decoder import JSONDecodeError
from typing import Optional, Tuple, List
from exceptions import UserAlreadyExist, UserOrSpawnNotExist
import random
import string
import hashlib
from asyncpg import Record
from asyncpg.pool import Pool
from asyncpg.connection import Connection
from aiohttp.web import json_response


async def gen_string(size: int = 18, chars: str = string.ascii_uppercase + string.digits) -> str:
    '''Генерирует рандомную строку'''
    return ''.join(random.choice(chars) for _ in range(size))


async def generate_token(user_id: int) -> str:
    '''Генерирует Токен в виде строки sha256'''
    salt: str = "sFTtzfpkqdSuDxrwTQGLCFZlLofLYG"
    random_string = await gen_string()
    finally_string = str(user_id) + salt + random_string
    hash_string = hashlib.sha256(finally_string.encode('utf-8')).hexdigest()
    return hash_string


async def get_token(pool: Pool, user_id: int) -> Optional[str]:
    '''Получает токен игрока из БД'''
    async with pool.acquire() as conn:
        token: Optional[str] = await conn.fetchval(f'SELECT token FROM players WHERE user_id={user_id}')
        return token


async def gen_random_pos(pos: Tuple[int, int], min_c: int = 20, max_c: int = 70) -> Tuple[int, int]:
    '''Генерирует рандомные координаты отталкиваясь от исходных координат'''
    x_coord: int = random.choice([random.randint(pos[0] - max_c, pos[0] - min_c), random.randint(pos[0] + min_c, pos[0] + max_c)])
    y_coord: int = random.choice([random.randint(pos[1] - max_c, pos[1] - min_c), random.randint(pos[1] + min_c, pos[1] + max_c)])
    return (x_coord, y_coord)


async def get_random_mapobject(conn: Connection, limit: int = 1) -> List[Optional[Record]]:
    '''Получает рандомный объект на карте'''
    map_object: List[Optional[Record]] = await conn.fetch(
        "SELECT * FROM map_objects OFFSET RANDOM() * "
        f"(SELECT COUNT(*) FROM map_objects) LIMIT {limit};"
    )
    return map_object


async def check_relay(conn: Connection, pos: Tuple[int, int]) -> bool:
    '''Проверяет зону на содержание в ней статических объектов'''
    min_coords = (pos[0] - 20, pos[1] - 20)
    max_coords = (pos[0] + 20, pos[1] + 20)
    objects: Optional[str] = await conn.fetchval(
        "SELECT go.name FROM map_objects mo "
        "INNER JOIN game_objects go ON mo.game_object_id=go.id WHERE "
        f"mo.x >= {min_coords[0]} AND mo.x <= {max_coords[0]} "
        f"AND mo.y >= {min_coords[1]} AND mo.y <= {max_coords[1]} "
        f"AND go.name NOT LIKE '%gen_%';"
    )
    if objects:
        return False
    return True


def check_token(func):
    '''Декоратор проверки токена авторизации'''
    async def wrapper(request):
        try:
            data: dict = await request.json()
            token = await get_token(pool=request.app["pool"], user_id=data["user_id"])
            if token == data["token"]:
                return await func(request)
            errors = [1, "token is not correct"]
        except (ValueError, KeyError, JSONDecodeError):
            errors = [2, "json is not correct"]
        status = False
        return json_response({"status": status, "errors": errors})
    return wrapper


async def get_free_pos(conn: Connection) -> Tuple[int, int]:
    '''Получение координат свободной позиции на карте'''
    while True:
        random_obj = await get_random_mapobject(conn)
        if random_obj:
            new_pos = await gen_random_pos(pos=(random_obj[0]['x'], random_obj[0]['y']))
            is_exist: Optional[int] = await conn.fetchval(
                f"SELECT x FROM map_objects WHERE x = {new_pos[0]} AND y = {new_pos[1]}"
            )
            if is_exist:
                continue
            free_relay = await check_relay(conn, new_pos)
            if free_relay is False:
                continue
            return new_pos
        return (0, 0)


async def create_object_on_map(conn: Connection, x: int, y: int, game_object_id: int, owner_id: int) -> None:
    '''Создаем объект на карте'''
    await conn.execute(
        "INSERT INTO map_objects (x, y, game_object_id, owner_id) "
        f"VALUES ({x}, {y}, {game_object_id}, {owner_id});"
    )


async def create_spawn(conn: Connection, player_id: int) -> Tuple[int, int]:
    '''Создает точку спауна игрока'''
    pos = await get_free_pos(conn)
    spawn_id: Optional[int] = await conn.fetchval(
        "SELECT id FROM game_objects WHERE name = 'spawn';"
    )
    if not spawn_id:
        spawn_id: int = await conn.fetchval(
            "WITH go AS (INSERT INTO game_objects (name, health, object_type) "
            "VALUES ('spawn', 1000, 'static') RETURNING id) "
            "INSERT INTO static_objects (game_object_ptr_id) "
            "VALUES ((SELECT id FROM go)) RETURNING (SELECT id FROM go);"
        )
    await create_object_on_map(conn, x=pos[0], y=pos[1], game_object_id=spawn_id, owner_id=player_id)
    return pos


async def create_pawn(conn: Connection, player_id: int, pawn_name: str, pos: Tuple[int, int]) -> None:
    '''Создает пешку'''
    pawn_id: Optional[int] = await conn.fetchval(
        f"SELECT id FROM game_objects WHERE name = '{pawn_name}'"
    )
    if not pawn_id:
        pawn_id: int = await conn.fetchval(
            "WITH go AS (INSERT INTO game_objects (name, health, object_type) "
            f"VALUES ('{pawn_name}', 10, 'dynamic') RETURNING id) "
            "INSERT INTO dynamic_objects (game_object_ptr_id, power, speed) "
            "VALUES ((SELECT id FROM go), 10, 10) RETURNING (SELECT id FROM go);"
        )
    await create_object_on_map(conn, x=pos[0], y=pos[1], game_object_id=pawn_id, owner_id=player_id)


async def create_user(conn: Connection, user_id: int, username: str) -> Tuple[int, str]:
    '''Создает игрока'''
    user: Optional[str] = await conn.fetchval(
        f"SELECT username FROM players WHERE user_id = {user_id} OR username = '{username}';"
    )
    if user:
        raise UserAlreadyExist
    token = await generate_token(user_id)
    player_id: int = await conn.fetchval(
        f"INSERT INTO players (user_id, username, token) "
        "VALUES ({user_id}, '{username}', '{token}') RETURNING id;"
    )
    return (player_id, token)


async def make_user(pool: Pool, user_id: int, username: str) -> str:
    '''Создает игрока, генерирует ему точку спауна и выдет пешку'''
    async with pool.acquire() as conn:
        player_id, token = await create_user(conn, user_id, username)
        spawn_pos = await create_spawn(conn, player_id)
        await create_pawn(conn, player_id, "wood_cutter", spawn_pos)

        return token


async def get_spawn_coords(pool: Pool, user_id: int) -> Record:
    '''Возвращает точку спауна игрока'''
    async with pool.acquire() as conn:
        spawn: Optional[Record] = await conn.fetchrow(
            "SELECT mo.x, mo.y FROM map_objects mo "
            "INNER JOIN game_objects go ON mo.game_object_id=go.id "
            "INNER JOIN players ON mo.owner_id=players.id "
            f"WHERE players.user_id={user_id} AND go.name='spawn';"
        )
        if not spawn:
            raise UserOrSpawnNotExist
        return spawn


async def get_map(pool: Pool, x_coord: int, y_coord: int, width: int, height: int) -> List[Optional[Record]]:
    '''Возвращает объекты на карте из области'''
    x_coords = (x_coord - (width // 2), x_coord + (width // 2))
    y_coords = (y_coord - (height // 2), y_coord + (height // 2))
    async with pool.acquire() as conn:
        all_objects: List[Optional[Record]] = await conn.fetch(
            "SELECT go.name, players.user_id, go.health, go.object_type, mo.x, mo.y "
            "FROM map_objects mo "
            "LEFT JOIN players ON mo.owner_id=players.id "
            "LEFT JOIN game_objects go ON mo.game_object_id=go.id "
            f"WHERE mo.x >= {x_coords[0]} AND mo.x <= {x_coords[1]} "
            f"AND mo.y >= {y_coords[0]} AND mo.y <= {y_coords[1]}"
        )

        return all_objects


async def gen_objects(pool: Pool) -> None:
    '''Генерирует объекты для фарма на карте'''
    async with pool.acquire() as conn:
        all_objects: List[Record] = await conn.fetch(
            "SELECT id FROM game_objects "
            f"WHERE name LIKE '%gen_%'"
        )
        all_objects *= 7
        random_objects = await get_random_mapobject(conn, len(all_objects))
        values: List[Tuple[int, int, int]] = []
        for random_obj in random_objects:
            pos = await gen_random_pos(pos=(random_obj["x"], random_obj["y"]), min_c=1)
            is_exist = await conn.fetchval(
                f"SELECT x FROM map_objects WHERE x={pos[0]} AND y={pos[1]}"
            )
            if is_exist:
                continue
            values.append((pos[0], pos[1], all_objects.pop()["id"]))
        await conn.executemany(
            "INSERT INTO map_objects (x, y, game_object_id) "
            "VALUES ($1, $2, $3);", values
        )
            