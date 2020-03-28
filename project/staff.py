'''Подкапотка запросов к БД'''
import math
import heapq
from json.decoder import JSONDecodeError
from typing import Optional, Tuple, List, Union
from time import time
from exceptions import UserAlreadyExist, ObjectNotExist
from operator import itemgetter
import random
import string
import hashlib
import uuid
from asyncpg import Record
from asyncpg.pool import Pool
from asyncpg.connection import Connection
from aiohttp.web import json_response


get_objname_by_taskname = {
    "cut": "tree"
}

get_resname_by_taskname = {
    "cut": "wood"
}


class PriorityQueue:
    def __init__(self):
        self.elements = []
    
    def empty(self):
        return len(self.elements) == 0
    
    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))
    
    def get(self):
        return heapq.heappop(self.elements)[1]


class SquareGrid:
    def __init__(self, min_x: int, max_x: int, min_y: int, max_y: int, map_objects: List[Optional[Record]]):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_x
        self.width = abs(min_x - max_x)
        self.height = abs(min_y - max_y)
        self.weights = {}
        self.walls = []
        self._make_walls(map_objects)

    def _make_walls(self, map_objects: List[Optional[Record]]):
        for map_objects in map_objects:
            self.walls.append((
                abs(map_objects["x"] - self.min_x),
                abs(map_objects["y"] - self.min_y)
            ))

    def in_bounds(self, pos: Tuple[int, int]):
        (x, y) = pos
        return 0 <= x < self.width and 0 <= y < self.height
    
    def passable(self, pos: Tuple[int, int]):
        return pos not in self.walls
    
    def neighbors(self, pos: Tuple[int, int]):
        (x, y) = pos
        results = [(x+1, y), (x, y-1), (x-1, y), (x, y+1)]
        if (x + y) % 2 == 0: results.reverse()
        results = filter(self.in_bounds, results)
        results = filter(self.passable, results)
        return results

    def cost(self, from_node, to_node):
        return self.weights.get(to_node, 1)


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
        token: Optional[str] = await conn.fetchval(f"SELECT token FROM players WHERE user_id='{user_id}'")
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
        "INNER JOIN game_objects go ON mo.game_object=go.uuid WHERE "
        f"mo.x >= {min_coords[0]} AND mo.x <= {max_coords[0]} "
        f"AND mo.y >= {min_coords[1]} AND mo.y <= {max_coords[1]} "
        f"AND go.object_type NOT LIKE 'generated';"
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


async def check_object_on_pos(conn: Connection, x: int, y:int) -> Optional[int]:
    return await conn.fetchval(
        f"SELECT x FROM map_objects WHERE x = {x} AND y = {y}"
    )


async def get_free_pos(conn: Connection) -> Tuple[int, int]:
    '''Получение координат свободной позиции на карте'''
    while True:
        random_obj = await get_random_mapobject(conn)
        if random_obj:
            new_pos = await gen_random_pos(pos=(random_obj[0]['x'], random_obj[0]['y']))
            is_exist = await check_object_on_pos(conn, new_pos[0], new_pos[1])
            if is_exist:
                continue
            free_relay = await check_relay(conn, new_pos)
            if free_relay is False:
                continue
            return new_pos
        return (0, 0)


async def create_object_on_map(conn: Connection, x: int, y: int, game_object: Optional[Union[int, uuid.uuid4]], owner_uuid: Optional[int]) -> None:
    '''Создаем объект на карте'''
    if isinstance(game_object, str):
        await conn.execute(
            f"WITH object AS (SELECT uuid FROM game_objects WHERE name='{game_object}') "
            "INSERT INTO map_objects (uuid, x, y, game_object) "
            f"VALUES ('{uuid.uuid4()}', {x}, {y}, (SELECT uuid FROM object))"
        )
    else:
        await conn.execute(
            "INSERT INTO map_objects (uuid, x, y, game_object, owner) "
            f"VALUES ('{uuid.uuid4()}', {x}, {y}, '{game_object}', '{owner_uuid}');"
        )


async def create_spawn(conn: Connection, player_uuid: uuid.uuid4) -> Tuple[int, int]:
    '''Создает точку спауна игрока'''
    pos = await get_free_pos(conn)
    spawn_uuid: Optional[uuid.uuid4] = await conn.fetchval(
        "SELECT uuid FROM game_objects WHERE name = 'spawn';"
    )
    if not spawn_uuid:
        await conn.execute(
            "WITH go AS (INSERT INTO game_objects (uuid, name, health, object_type) "
            f"VALUES ('{uuid.uuid4()}', 'spawn', 1000, 'static') RETURNING uuid), WITH so AS ( "
            "INSERT INTO static_objects (game_object_ptr) "
            "VALUES ((SELECT uuid FROM go))) "
            "INSERT INTO map_objects (uuid, x, y, game_object, owner) "
            f"VALUES ('{uuid.uuid4()}', {pos[0]}, {pos[1]}, (SELECT uuid FROM go), '{player_uuid}')"
        )
        return pos
    await create_object_on_map(conn, x=pos[0], y=pos[1], game_object=spawn_uuid, owner_uuid=player_uuid)
    return pos


async def create_pawn(conn: Connection, player_uuid: int, pawn_name: str, pos: Tuple[int, int], task_name: str) -> None:
    '''Создает пешку'''
    await conn.execute(
        "WITH go AS (INSERT INTO game_objects (uuid, name, health, object_type) "
        f"VALUES ('{uuid.uuid4()}', '{pawn_name}', 10, 'pawn') RETURNING uuid), po AS ( "
        "INSERT INTO pawn_objects (game_object_ptr, max_tasks) "
        "VALUES ((SELECT uuid FROM go), 1)), act AS ( "
        f"SELECT uuid FROM tasks WHERE name='{task_name}' ), at AS ("
        "INSERT INTO available_tasks (uuid, task, pawn) "
        f"VALUES ('{uuid.uuid4()}', (SELECT uuid FROM act), (SELECT uuid FROM go))) "
        "INSERT INTO map_objects (uuid, x, y, game_object, owner) "
        f"VALUES ('{uuid.uuid4()}', {pos[0]}, {pos[1]}, (SELECT uuid FROM go), '{player_uuid}');"
    )


async def create_user(conn: Connection, user_id: int, username: str) -> Tuple[uuid.uuid4, str]:
    '''Создает игрока'''
    user: Optional[str] = await conn.fetchval(
        f"SELECT username FROM players WHERE user_id = '{user_id}' OR username = '{username}';"
    )
    if user:
        raise UserAlreadyExist
    token = await generate_token(user_id)
    player_uuid: int = await conn.fetchval(
        "WITH pl AS (INSERT INTO players (uuid, user_id, username, token) "
        f"VALUES ('{uuid.uuid4()}', '{user_id}', '{username}', '{token}') RETURNING uuid) "
        "INSERT INTO players_resources (uuid, player, money, wood, stones) "
        f"VALUES ('{uuid.uuid4()}', (SELECT uuid FROM pl), 0, 20, 0) RETURNING (SELECT uuid FROM pl)"
    )
    return (player_uuid, token)


async def make_user(pool: Pool, user_id: int, username: str) -> str:
    '''Создает игрока, генерирует ему точку спауна и выдает пешку'''
    async with pool.acquire() as conn:
        player_uuid, token = await create_user(conn, user_id, username)
        spawn_pos = await create_spawn(conn, player_uuid)
        await create_pawn(conn, player_uuid, "wood_cutter", (spawn_pos[0] + 1, spawn_pos[1]), task_name="cut")

        return token


async def get_spawn_coords(pool: Pool, user_id: int) -> Record:
    '''Возвращает точку спауна игрока'''
    async with pool.acquire() as conn:
        spawn: Optional[Record] = await conn.fetchrow(
            "SELECT mo.x, mo.y FROM map_objects mo "
            "INNER JOIN game_objects go ON mo.game_object_id=go.id "
            "INNER JOIN players ON mo.owner_id=players.id "
            f"WHERE players.user_id='{user_id}' AND go.name='spawn';"
        )
        if not spawn:
            raise ObjectNotExist
        return spawn

async def get_objects_from_relay(conn: Connection, x_coords: Tuple[int, int], y_coords: Tuple[int, int]) -> List[Optional[Record]]:
    '''Получает объекты из области на карте'''
    return await conn.fetch(
        "SELECT go.name, players.username, go.health, go.object_type, mo.x, mo.y, mo.uuid "
        "FROM map_objects mo "
        "LEFT JOIN players ON mo.owner=players.uuid "
        "LEFT JOIN game_objects go ON mo.game_object=go.uuid "
        f"WHERE mo.x >= {x_coords[0]} AND mo.x <= {x_coords[1]} "
        f"AND mo.y >= {y_coords[0]} AND mo.y <= {y_coords[1]}"
    )


async def get_map(pool: Pool, x_coord: int, y_coord: int, width: int, height: int) -> List[Optional[Record]]:
    '''Возвращает объекты на карте из области'''
    x_coords = (x_coord - (width // 2), x_coord + (width // 2))
    y_coords = (y_coord - (height // 2), y_coord + (height // 2))
    async with pool.acquire() as conn:
        return await get_objects_from_relay(conn, x_coords, y_coords)


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


async def get_profile_info(pool: Pool, token: str) -> Optional[Record]:
    """Получаем информацию о профиле игрока"""
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT players.username, players.metadata, mo.x, mo.y, "
            "pr.money, pr.wood, pr.stones FROM players "
            "INNER JOIN map_objects mo ON players.uuid=mo.owner "
            "INNER JOIN game_objects go ON mo.game_object=go.uuid "
            "INNER JOIN players_resources pr ON pr.player=players.uuid "
            f"WHERE players.token='{token}' AND go.name='spawn'"
        )


async def get_object_by_uuid(pool: Pool, object_uuid: str) -> Optional[Record]:
    '''Получает объект по uuid map_object'''
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT go.uuid, go.name, go.object_type, players.username, go.health, mo.x, mo.y, "
            "po.speed, po.power, po.max_tasks FROM map_objects mo "
            "INNER JOIN game_objects go ON mo.game_object=go.uuid "
            "LEFT JOIN players ON mo.owner=players.uuid "
            "LEFT JOIN pawn_objects po ON po.game_object_ptr=go.uuid "
            f"WHERE mo.uuid='{object_uuid}';"
        )


async def get_object_by_coors(pool: Pool, x: int, y: int) -> Optional[Record]:
    ''''Получает объект на тайле или ничего'''
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT mo.uuid, go.name, go.object_type, players.username, go.health "
            "FROM map_objects mo "
            "LEFT JOIN game_objects go ON mo.game_object=go.uuid "
            "LEFT JOIN players ON mo.owner=players.uuid "
            f"WHERE mo.x={x} AND mo.y={y}"
        )


async def get_pawn_tasks(pool: Pool, gameobject_uuid: str) -> List[Optional[Record]]:
    '''Получение списка действий пешки'''
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT pt.uuid, tasks.name as task_name, pt.start_time FROM pawn_tasks pt "
            "LEFT JOIN game_objects go ON pt.pawn=go.uuid "
            "INNER JOIN tasks ON pt.task=tasks.uuid "
            f"WHERE go.uuid='{gameobject_uuid}' "
            "ORDER BY pt.start_time"
        )


async def get_available_tasks(pool: Pool, gameobject_uuid: str) -> List[Optional[Record]]:
    '''Получает список доступных действий пешки'''
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT tasks.name FROM available_tasks at "
            "LEFT JOIN game_objects go ON at.pawn=go.uuid "
            "LEFT JOIN tasks ON at.task=tasks.uuid "
            f"WHERE go.uuid='{gameobject_uuid}'"
        )


async def get_available_tasks_by_mo(pool: Pool, object_uuid: str, token: str) -> List[Optional[Record]]:
    '''Получает список доступных действий пешки'''
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT tasks.name FROM available_tasks aa "
            "INNER JOIN game_objects go ON aa.pawn=go.uuid "
            "INNER JOIN map_objects mo ON mo.game_object=go.uuid "
            "INNER JOIN tasks ON aa.atask=tasks.uuid "
            "INNER JOIN players ON mo.owner=players.uuid "
            f"WHERE mo.uuid='{object_uuid}' AND players.token='{token}'"
        )


async def get_pawns(pool: Pool, token: str) -> List[Optional[Record]]:
    '''Получает список пешек игрока'''
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT mo.uuid, go.name, go.health, po.speed, po.power, po.max_tasks "
            "FROM map_objects mo "
            "INNER JOIN game_objects go ON mo.game_object=go.uuid "
            "INNER JOIN pawn_objects po ON po.game_object_ptr=go.uuid "
            "LEFT JOIN players ON mo.owner=players.uuid "
            f"WHERE players.token='{token}';"
        )


async def check_obj_limit(conn: Connection, obj_name: str, limit: int) -> bool:
    '''Проверяем достигнут ли лимит объектов с ресурсами на карте'''
    count: Optional[Record] = await conn.fetchrow(
        "WITH pl_count AS (SELECT COUNT(*) FROM players), "
        "ob_count AS (SELECT COUNT(go) FROM map_objects mo "
        "INNER JOIN game_objects go ON mo.game_object=go.uuid "
        f"WHERE go.name='{obj_name}') "
        "SELECT pl_count.count as players, ob_count.count as objects "
        "FROM pl_count, ob_count;"
    )
    if count["objects"] >= (limit * count["players"]):
        return False
    return True


async def generate_object(pool: Pool, obj_name: str, limit: int):
    '''Метод проверки и генерации объектов с ресурсами'''
    async with pool.acquire() as conn:
        can_generate = await check_obj_limit(conn, obj_name, limit)
        if can_generate is False:
            return
        i = 0
        while i < 100:
            random_obj = await get_random_mapobject(conn)
            random_pos = await gen_random_pos((random_obj[0]['x'], random_obj[0]['y']), min_c=1)
            is_exist = await check_object_on_pos(conn, random_pos[0], random_pos[1])
            if is_exist:
                continue
            await create_object_on_map(
                conn=conn,
                x=random_pos[0],
                y=random_pos[1],
                game_object=obj_name,
                owner_uuid=None
            )
            i += 1
            #return


async def get_nearest_obj(conn: Connection, object_uuid: str, obj_name: str, token: str) -> Optional[Record]:
    return await conn.fetchrow(
        "WITH pawn AS (SELECT mo.x, mo.y, po.power, po.speed FROM map_objects mo "
        "INNER JOIN game_objects go ON mo.game_object=go.uuid "
        "INNER JOIN pawn_objects po ON po.game_object_ptr=go.uuid "
        "INNER JOIN players ON mo.owner=players.uuid "
        f"WHERE players.token='{token}' AND mo.uuid='{object_uuid}') "
        "SELECT mo.x, mo.y, |/((mo.x-(SELECT x FROM pawn))^2 + (mo.y-(SELECT y FROM pawn))^2) AS length, "
        "go.health as object_health, (SELECT x FROM pawn) AS pawn_x, (SELECT y FROM pawn) AS pawn_y, "
        "(SELECT power FROM pawn) AS pawn_power, (SELECT speed FROM pawn) AS pawn_speed "
        "FROM map_objects mo INNER JOIN game_objects go ON mo.game_object=go.uuid "
        f"WHERE go.name='{obj_name}' AND mo.x >= (SELECT x FROM pawn) AND mo.x <= ((SELECT x FROM pawn) + 100) "
        "AND mo.y >= (SELECT y FROM pawn) AND mo.y <= ((SELECT y FROM pawn) + 100) "
        "ORDER BY length LIMIT 1"
    )


async def get_relay_objects(conn: Connection, min_x: int, min_y: int, max_x: int, max_y: int) -> List[Optional[Record]]:
    return await conn.fetch(
        "SELECT mo.x, mo.y "
        "FROM map_objects mo "
        "LEFT JOIN game_objects go ON mo.game_object=go.uuid "
        f"WHERE mo.x >= {min_x} AND mo.x <= {max_x} "
        f"AND mo.y >= {min_y} AND mo.y <= {max_y} "
        "ORDER BY mo.y DESC, mo.x ASC"
    )


async def check_way_for_clear(static_coord: int, st_name: str, way: list, way_name: str, objects: List[Optional[Record]], reverse: bool):
    objects.sort(key=itemgetter(way_name), reverse=reverse)
    for obj in objects:
        if obj[st_name] == static_coord and obj[way_name] in way:
            return obj


def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)


def get_near_finish(start: Tuple[int, int], finish: Tuple[int, int]) -> Tuple[int, int]:
    a = heuristic(start, (finish[0] - 1, finish[1]))
    b = heuristic(start, (finish[0] + 1, finish[1]))
    if a < b:
        return (finish[0] - 1, finish[1])
    return (finish[0] + 1, finish[1])


async def a_star_search(graph: SquareGrid, start: Tuple[int, int], goal: Tuple[int, int]) -> dict:
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0
    
    while not frontier.empty():
        current = frontier.get()
        
        if current == goal:
            break
        
        for next in graph.neighbors(current):
            new_cost = cost_so_far[current] + graph.cost(current, next)
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                frontier.put(next, priority)
                came_from[next] = current
    
    return came_from


async def reconstruct_path(came_from, start, goal, _x, _y):
    current = goal
    path = [(current[0] + _x, current[1] + _y)]
    while current != start:
        current = came_from[current]
        path.append((current[0] + _x, current[1] + _y))
    path.reverse() 
    return path


async def get_way(conn: Connection, start_pos: Tuple[int, int], finish_pos: Tuple[int, int]) -> list:
    x_coors = sorted([start_pos[0], finish_pos[0]])
    y_coors = sorted([start_pos[1], finish_pos[1]])
    all_objects = await get_relay_objects(
        conn=conn,
        min_x=x_coors[0] - 15,
        max_x=x_coors[1] + 15,
        min_y=y_coors[0] - 15,
        max_y=y_coors[1] + 15
    )

    graph = SquareGrid(
        min_x=x_coors[0] - 15,
        max_x=x_coors[1] + 15,
        min_y=y_coors[0] - 15,
        max_y=y_coors[1] + 15,
        map_objects=all_objects
    )

    start=(abs(start_pos[0] - graph.min_x), abs(start_pos[1] - graph.min_y))
    goal=(abs(finish_pos[0] - graph.min_x), abs(finish_pos[1] - graph.min_y)) 
    came_from = await a_star_search(
        graph=graph,
        start=start,
        goal=goal
    )

    return await reconstruct_path(came_from=came_from, start=start, goal=goal, _x=graph.min_x, _y=graph.min_y)


async def create_task(conn: Connection, pawn_mo_uuid: str, task_name: str, common_time: float, walk_time: float, work_time_count: int) -> str:
    task_start_time = time()
    task_end_time = task_start_time + common_time
    task_uuid: uuid.uuid4 = await conn.fetchval(
        "WITH pawn AS (SELECT go.uuid FROM game_objects go "
        "INNER JOIN map_objects mo ON go.uuid=mo.game_object "
        f"WHERE mo.uuid='{pawn_mo_uuid}'), task AS "
        f"(SELECT uuid FROM tasks WHERE name='{task_name}') "
        "INSERT INTO pawn_tasks (uuid, pawn, task, start_time, end_time, walk_time, work_time_count, common_time) "
        f"VALUES ('{uuid.uuid4()}', (SELECT uuid FROM pawn), (SELECT uuid FROM task), "
        f"{task_start_time}, {task_end_time}, {walk_time}, {work_time_count}, {common_time}) RETURNING uuid"
    )
    return task_uuid


async def get_pawn_task(conn: Connection, task_uuid: str) -> Optional[Record]:
    return await conn.fetchrow(
        "SELECT pt.*, tasks.name FROM pawn_tasks pt "
        "LEFT JOIN tasks ON pt.task=tasks.uuid "
        f"WHERE pt.uuid='{task_uuid}'"
    )


async def delete_pawn_task(conn: Connection, task_uuid: str) -> None:
    await conn.execute(
        f"DELETE FROM pawn_tasks WHERE uuid='{task_uuid}'"
    )


async def create_actions(conn: Connection, task_uuid: str) -> tuple:
    actions = []

    pawn_task = await get_pawn_task(conn=conn, task_uuid=task_uuid)
    walk_time = pawn_task["walk_time"]
    work_time_count = pawn_task["work_time_count"]
    task_name = pawn_task["name"]

    start_time = time()
    end_time = start_time + pawn_task["common_time"] 
    actions_queue = [
        {"action": "walk", "lead_time": walk_time},
        {"action": task_name, "lead_time": 10},
        {"action": "carry", "lead_time": walk_time}
    ]
    for _ in range(work_time_count + work_time_count * 2):
        start_time = end_time
        current_action = actions_queue.pop(0)
        end_time = start_time + current_action["lead_time"]
        actions.append((
            uuid.uuid4(),
            task_uuid,
            current_action["action"],
            start_time,
            end_time
        ))
        actions_queue.append(current_action)

    await conn.executemany(
        "INSERT INTO pawn_actions (uuid, task, name, start_time, end_time) "
        "VALUES ($1, $2, $3, $4, $5);", actions
    )

    return actions[0]


async def create_pawn_action(conn: Connection, task_uuid: str, action_name: str, start_time: float, end_time: float):
    await conn.execute(
        "INSERT INTO pawn_actions (uuid, task, name, start_time, end time) "
        f"VALUES ('{uuid.uuid4()}', '{task_uuid}', {action_name}, {start_time}, {end_time})"
    )


async def add_pawn_action(conn: Connection, task: str, action_name: float, work_time: float, get_task: bool = True):
    if get_task:
        pawn_task = await get_pawn_task(conn=conn, task_uuid=task)
    else:
        pawn_task = task
    walk_time = pawn_task["walk_time"]
    start_time = time()
    end_time = start_time + walk_time
    await create_pawn_action(
        conn=conn,
        task_uuid=pawn_task["uuid"],
        action_name=action_name,
        start_time=start_time,
        end_time=end_time
    )


async def add_pretask_to_pawn(pool: Pool, object_uuid: str, token: str, task_name: str) -> dict:
    async with pool.acquire() as conn:
        nearest_obj = await get_nearest_obj(
            conn=conn,
            object_uuid=object_uuid,
            obj_name=get_objname_by_taskname[task_name],
            token=token
        )

        start = (nearest_obj["pawn_x"], nearest_obj["pawn_y"])
        finish = get_near_finish(start=start, finish=(nearest_obj["x"], nearest_obj["y"]))

        way = await get_way(
            conn=conn,
            start_pos=start,
            finish_pos=finish
        )

        walk_time: float = (len(way) - 1) / nearest_obj["pawn_speed"]
        work_time_count = math.ceil((nearest_obj["object_health"] // nearest_obj["pawn_power"]))
        common_time: float = walk_time * (work_time_count * 2) + (work_time_count * 10)

        task_uuid = await create_task(
            conn=conn,
            pawn_mo_uuid=object_uuid,
            task_name=task_name,
            common_time=common_time,
            walk_time=walk_time,
            work_time_count=work_time_count,
        )

        response_dict = {
            "task_uuid": str(task_uuid),
            "common_time": common_time,
            "way": way,
        }
        return response_dict


async def procced_task(pool: Pool, task_uuid, accept: bool):
    async with pool.acquire() as conn:
        if accept is True:
            return await create_actions(
                conn=conn,
                task_uuid=task_uuid
            )
        await delete_pawn_task(conn=conn, task_uuid=task_uuid)


async def get_player_resource_by_name(pool: Pool, token: str, res_name: Optional[str]) -> Optional[Record]:
    async with pool.acquire() as conn:
        res_name = "*" if not res_name else res_name
        return await conn.fetchrow(
            f"SELECT pr.{res_name} FROM players "
            "INNER JOIN players_resources pr ON players.uuid=pr.player "
            f"WHERE players.token='{token}'"
        )


async def get_finished_actions(conn: Connection) -> List[Optional[Record]]:
    current_time = time()
    return await conn.fetch(
        "SELECT p.uuid as player_uuid, pr.uuid as storage_uuid, po.power as pawn_power, "
        "pt.uuid as pt_uuid, t.name as task_name, pa.name as pa_name, pa.uuid as pa_uuid, "
        "coalesce(go.health, 0) as go_health FROM players p INNER JOIN players_resources pr ON p.uuid=pr.player "
        "LEFT JOIN map_objects mo ON mo.owner=p.uuid "
        "LEFT JOIN game_objects go ON mo.game_object=go.uuid "
        "INNER JOIN pawn_objects po ON go.uuid=po.game_object_ptr "
        "INNER JOIN pawn_tasks pt ON pt.pawn=go.uuid "
        "INNER JOIN tasks t ON pt.task=t.uuid "
        "INNER JOIN pawn_actions pa ON pt.uuid=pa.task "
        f"WHERE pa.end_time < {current_time}"
    )


async def delete_actions(conn: Connection, actions: tuple) -> None:
    await conn.execute(
        f"DELETE FROM pawn_actions WHERE uuid IN {actions}"
    )


async def delete_tasks(conn: Connection, tasks: tuple) -> None:
    await conn.execute(
        f"DELETE FROM pawn_tasks WHERE uuid IN {tasks}"
    )

async def add_res_to_player(conn: Connection, storage_uuid: str, task_name: str, res_count: int):
    res_name = get_resname_by_taskname[task_name]
    await conn.execute(
        f"UPDATE players_resources "
        f"SET {res_name}={res_name}+{res_count} "
        f"WHERE uuid='{storage_uuid}'"
    )

async def change_pawn_health(conn: Connection, go_uuid: uuid, new_health: int):
    pass
