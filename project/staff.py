from aiohttp.web import json_response
from json.decoder import JSONDecodeError
from exceptions import UserAlreadyExist
import random
import string
import hashlib


async def generate_string(size=18, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


async def generate_token(vk_id):
    salt = "sFTtzfpkqdSuDxrwTQGLCFZlLofLYG"
    random_string = await generate_string()
    finally_string = str(vk_id) + salt + random_string
    hash_string = hashlib.sha256(finally_string.encode('utf-8')).hexdigest()
    return hash_string


async def get_token(pool, vk_id):
    async with pool.acquire() as conn:
        token = await conn.fetchval(f'SELECT token FROM players WHERE vk_id = {vk_id};')
        return token


async def gen_random_pos(pos, min_c=20, max_c=70):
    x = random.choice([random.randint(pos[0] - max_c, pos[0] - min_c), random.randint(pos[0] + min_c, pos[0] + max_c)])
    y = random.choice([random.randint(pos[1] - max_c, pos[1] - min_c), random.randint(pos[1] + min_c, pos[1] + max_c)])
    return (x, y)


def check_token(func):
    async def wrapper(request):
        try:
            data = await request.json()
            token = await get_token(pool=request.app["pool"], vk_id=data["vk_id"])
            if token == data["token"]:
                return await func(request)
            errors = [1, "token is not correct"]
        except (ValueError, KeyError, JSONDecodeError):
            errors = [2, "json is not correct"]
        status = False
        return json_response({"status": status, "errors": errors})
    return wrapper



async def check_relay(conn, pos):
    min_coords = (pos[0] - 20, pos[1] - 20)
    max_coords = (pos[0] + 20, pos[1] + 20)
    objects = await conn.fetchval(
        "SELECT name FROM game_objects WHERE "
        f"x > {min_coords[0]} AND x < {max_coords[0]} "
        f"AND y > {min_coords[1]} AND y < {max_coords[1]} "
        f"AND name <> LIKE '%gen_%';"
    )
    if objects:
        return False
    return True


async def check_player(conn, vk_id, username):
    user = await conn.fetchval(f"SELECT username FROM players WHERE vk_id = {vk_id} OR username = '{username}';")
    return user


async def create_player(conn, vk_id, username, token):
    await conn.execute(f"INSERT INTO players (vk_id, username, token) VALUES ({vk_id}, '{username}', '{token}');")


async def create_user(pool, vk_id, username):
    async with pool.acquire() as conn:
        he_exist = await check_player(conn, vk_id, username)
        if he_exist:
            raise UserAlreadyExist
        token = await generate_token(vk_id)
        await create_player(conn, vk_id, username, token)
        return token
