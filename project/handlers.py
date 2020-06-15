'''Обработчик запросов приходящих на сервер'''
from asyncpg import exceptions
from exceptions import UserAlreadyExist, ObjectNotExist, UserRegistered, NotValidTask, PawnLimit
from json.decoder import JSONDecodeError
from aiohttp.web import json_response, Request, Response
import staff
import sys


async def test(request: Request) -> json_response:
    return json_response({"status": True})


@staff.pack_response
async def register_user(request: Request) -> dict:
    '''Метод регистрации игрока'''
    response = {"status": False}
    try:
        data: dict = await request.json()
        await staff.make_user(
            pool=request.app["pool"],
            GP_ID=data["GP_ID"],
            username=data["username"]
        )
        response["status"] = True
        response["is_new_user"] = True
    except (TypeError, ValueError, KeyError, JSONDecodeError):
        response["errors"] = [2, "json is not correct"]
    except exceptions.StringDataRightTruncationError:
        response["errors"] = [7, "some data is too long"]
    except UserAlreadyExist:
        response["errors"] = [3, "User with this username already exist"]
    except UserRegistered:
        response["is_new_user"] = False
        response["status"] = True
   
    return response


@staff.pack_response
async def get_map(request: Request) -> dict:
    '''Возвращает объекты расположенные на карте'''
    response = {"status": True, "game_objects": None}
    try:
        data: dict = await request.json()
        map_objects = await staff.get_map(
            pool=request.app["pool"],
            x_coord=int(data["coors"]["x"]),
            y_coord=int(data["coors"]['y']),
            width=data["scope"]["width"],
            height=data["scope"]["height"]
        )

        game_objects = []
        appened_objects = {}

        if map_objects:
            for map_object in map_objects:
                if map_object["uuid"] not in appened_objects:
                    game_object = {
                        "uuid": str(map_object["uuid"]),
                        "name": map_object["name"],
                        "owner": map_object["username"],
                        "health": map_object["health"],
                        "type": map_object["object_type"],
                        "level": map_object["level"],
                        "coors": {
                            "x": float(map_object["x"]),
                            "y": float(map_object["y"])
                        }
                    }
                    if map_object["pt_uuid"]:
                        action = {
                            "task_uuid": str(map_object["pt_uuid"]),
                            "action_name": map_object["pa_name"],
                            "start_time": map_object["start_time"],
                            "end_time": map_object["end_time"],
                            "target_uuid": str(map_object["target_uuid"]),
                            "way": staff.tuple_to_list(map_object["way"])
                        }
                        game_object["action"] = action

                    game_objects.append(game_object)
                    appened_objects[map_object["uuid"]] = True

        pawn_ways = await staff.get_pawn_ways(
            pool=request.app["pool"],
            x_coord=data["coors"]["x"],
            y_coord=data["coors"]['y'],
            width=data["scope"]["width"],
            height=data["scope"]["height"]
        )

        if pawn_ways:
            for way in pawn_ways:
                if way["uuid"] not in appened_objects:
                    game_objects.append({
                        "uuid": str(way["uuid"]),
                        "name": way["name"],
                        "owner": way["username"],
                        "health": way["health"],
                        "type": way["object_type"],
                        "level": way["level"],
                        "coors": {
                            "x": float(way["x"]),
                            "y": float(way["y"])
                        },
                        "task_uuid": str(way["pt_uuid"]),
                        "action_name": way["pa_name"],
                        "start_time": way["start_time"],
                        "end_time": way["end_time"],
                        "way": staff.tuple_to_list(way["way"])
                    })

        if game_objects:
            response["game_objects"] = game_objects

    except (TypeError, ValueError, KeyError, JSONDecodeError):
        response["status"] = False
        response["errors"] = [2, "json is not correct"]
    return response


@staff.pack_response
async def get_profile(request: Request) -> dict:
    '''Возвращает инфу о игроке'''
    response = {"status": True}
    try:
        data = await request.json()
        profile_info = await staff.get_profile_info(
            pool=request.app["pool"],
            GP_ID=data["GP_ID"]
        )
        response["username"] = profile_info["username"]
        response["resources"] = {
            "money": profile_info["money"],
            "stones": profile_info["stones"],
            "wood": profile_info["wood"]
        }
        response["spawn"] = {
            "x": float(profile_info['x']),
            "y": float(profile_info['y'])
        }
    except (TypeError, KeyError, ValueError, JSONDecodeError):
        response["status"] = False
        response["errors"] = [2, "json is not correct"]

    return response


@staff.pack_response
async def get_object_info(request: Request) -> dict:
    '''Возвращает информацию о конкретном объекте'''
    response = {"status": False}
    try:
        data = await request.json()
        game_object = await staff.get_object_by_uuid(
            pool=request.app['pool'],
            object_uuid=data["object_uuid"]
        )
        if game_object:
            response["status"] = True
            response["object_uuid"] = str(data["object_uuid"])
            response["name"] = game_object["name"]
            response["object_type"] = game_object["object_type"]
            response["owner"] = game_object["username"]
            response["health"] = game_object["health"]
            response["level"] = game_object["level"]
            response["coors"] = {
                "x": float(game_object["x"]),
                "y": float(game_object["y"])
            }
            if game_object["object_type"] == "pawn":
                tasks = await staff.get_pawn_tasks(
                    pool=request.app['pool'],
                    gameobject_uuid=game_object["uuid"]
                )
                response["power"] = game_object["power"]
                response["speed"] = game_object["speed"]
                response["max_tasks"] = game_object["max_tasks"]
                if tasks:
                    pawn_tasks = []
                    for task in tasks:
                        pawn_tasks.append({
                            "task_uuid": str(task["uuid"]),
                            "task_name": task["task_name"],
                            "start_time": task["start_time"],
                            "end_time": task["end_time"],
                            "way": staff.tuple_to_list(task["way"])
                        })
                    tasks = pawn_tasks
                response["tasks"] = tasks

                available_tasks = await staff.get_available_tasks(
                    pool=request.app["pool"],
                    gameobject_uuid=str(game_object["uuid"])
                )
                _enabled = False
                if game_object["max_tasks"] > len(tasks):
                    _enabled = True
                tasks = []
                for task in available_tasks:
                    tasks.append({
                        "task_name": task["name"],
                        "enabled": _enabled
                    })
                response["available_tasks"] = tasks
        else:
            response["errors"] = [6, "game_object is not found"]
    except (TypeError, KeyError, ValueError, JSONDecodeError):
        response["errors"] = [2, "json is not correct"]

    return response


@staff.pack_response
async def get_player_pawns(request: Request) -> dict:
    '''Возвращает список всех пешек игрока'''
    response = {"status": True}
    try:
        data = await request.json()
        pawns = await staff.get_pawns(
            pool=request.app['pool'],
            GP_ID=data['GP_ID']
        )
        response_pawns = None
        if pawns:
            response_pawns = []
            for pawn in pawns:
                response_pawns.append({
                    "object_uuid": str(pawn["uuid"]),
                    "name": pawn["name"],
                    "health": pawn["health"],
                    "speed": pawn["speed"],
                    "power": pawn["power"],
                    "level": pawn["level"],
                    "max_actions": pawn["max_tasks"]
                })
        response["pawns"] = response_pawns
    except (TypeError, KeyError, ValueError, JSONDecodeError):
        response["errors"] = [2, "json is not correct"]
        response["status"] = False

    return response


async def gen_new_object(request: Request) -> Response:
    '''Отвечает за проверку и генерацию объектов с ресурсами на карте'''
    #try:
    data = await request.json()
    await staff.generate_object(
        pool=request.app['pool'],
        obj_name=data['obj_name'],
        limit=data['limit']
    )
    return Response(status=200)
    #except (ValueError, KeyError, JSONDecodeError):
        #return Response(status=500)


@staff.pack_response
async def get_tile(request: Request) -> dict:
    '''Получение тайла по координатам'''
    response = {"status": True, "game_object": None}
    try:
        data = await request.json()
        tile = await staff.get_object_by_coors(
            pool=request.app["pool"],
            x=int(data["coors"]["x"]),
            y=int(data["coors"]["y"])
        )
        if tile:
            response["game_object"] = {
                "uuid": str(tile["uuid"]),
                "name": tile["name"],
                "object_type": tile["object_type"],
                "health": tile["health"],
                "level": tile["level"],
                "owner": tile["username"]
            }
    except (KeyError, ValueError, TypeError, JSONDecodeError):
        response["status"] = False
        response["errors"] = [2, "json is not correct"]

    return response


@staff.pack_response
async def add_task_to_pawn(request: Request) -> dict:
    response = {"status": False}
    try:
        data = await request.json()
        response = await staff.add_pretask_to_pawn(
            pool=request.app["pool"],
            object_uuid=data["object_uuid"],
            GP_ID=data["GP_ID"],
            task_name=data["task_name"]
        )
        response["status"] = True
    except (KeyError, ValueError, TypeError, JSONDecodeError):
        response["errors"] = [2, "json is not correct"]
    except NotValidTask:
        response["errors"] = [7, "data is not valid or correct"]
    except PawnLimit:
        response["errors"] = [8, "pawn has tasks limit"]
    return response


@staff.pack_response
async def get_available_tasks_count(request: Request) -> dict:
    response = {"status": False}
    try:
        data = await request.json()
        available_tasks = await staff.get_available_tasks_by_mo(
            pool=request.app["pool"],
            object_uuid=data["object_uuid"],
            GP_ID=data["GP_ID"]
        )

        if not available_tasks:
            response["erros"] = [6, "object_uuid or GP_ID are not correct"]
        else:
            response["status"] = True
            response["count"] = len(available_tasks)
    except (KeyError, ValueError, TypeError, JSONDecodeError, exceptions.InvalidTextRepresentationError):
        response["errors"] = [2, "json is not correct"]

    return response


@staff.pack_response
async def get_player_resources(request: Request) -> dict:
    response = {"status": False}
    try:
        data = await request.json()
        resources = await staff.get_player_resource_by_name(
            pool=request.app["pool"],
            GP_ID=data["GP_ID"],
            res_name=data["resource"]
        )
        if resources:
            response["status"] = True
            response["resources"] = [{k: v} for k, v in resources.items() if k not in ["uuid", "player"]]
        else:
            response["errors"] = [1, "GP_ID is not correct"]
    except (KeyError, ValueError, TypeError, JSONDecodeError):
        response["erros"] = [2, "json is not correct"]
    except exceptions.UndefinedColumnError:
        response["errors"] = [5, "resource name is not correct"]
        

    return response


@staff.pack_response
async def check_connection(request: Request) -> dict:
    '''Тест соединения'''
    return {"status": True}


@staff.pack_response
async def accept_task(request: Request) -> dict:
    response = {"status": False}
    try:
        data = await request.json()
        action = await staff.procced_task(
            pool=request.app["pool"],
            task_uuid=data["task_uuid"],
            GP_ID=data["GP_ID"],
            accept=data["accept"]
        )
        if action:
            response["task_uuid"] = action["task_uuid"]
            response["action_name"] = action["action_name"]
            response["start_time"] = action["start_time"]
            response["end_time"] = action["end_time"]
            response["way"] = action["way"]
        response["status"] = True
    except (ValueError, TypeError, KeyError, JSONDecodeError, exceptions.InvalidTextRepresentationError):
        response["errors"] = [2, "json is not correct"]
    except NotValidTask:
        response["errors"] = [7, "got are not correct data"]
    except PawnLimit:
        response["errors"] = [8, "pawn has tasks limit"]

    return response


@staff.pack_response
async def get_current_action(request: Request) -> dict:
    response = {"status": True}
    try:
        data = await request.json()
        action_data = await staff.get_current_action_data(
            pool=request.app["pool"],
            GP_ID=data["GP_ID"],
            mo_uuid=data["object_uuid"]
        )
        if action_data:
            action_data = {
                "pawn_name": action_data["pawn_name"],
                "action_name": action_data["action_name"],
                "start_time": action_data["start_time"],
                "end_time": action_data["end_time"],
                "way": staff.tuple_to_list(action_data["way"]),
                "target_uuid": str(action_data["target_uuid"])
            }
        response["action"] = action_data
    except (ValueError, TypeError, KeyError, JSONDecodeError, exceptions.InvalidTextRepresentationError):
        response["errors"] = [2, "json is not correct"]
        response["status"] = False

    return response


@staff.pack_response
async def get_pawn_tasks_list(request: Request) -> dict:
    response = {"status": True}
    try:
        data = await request.json()
        pawn_tasks = await staff.get_pawn_tasks_list(
            pool=request.app["pool"],
            pawn_uuid=data["pawn_uuid"],
            GP_ID=data["GP_ID"]
        )
        tasks = []
        for task in pawn_tasks:
            if task["name"]:
                t = {"uuid": str(task["pt_uuid"]),"name": task["name"]}
                if task["end_time"]:
                    t["end_time"] = task["end_time"]
                tasks.append(t)
        for _ in range(pawn_tasks[0]["max_tasks"] - len(tasks)):
            tasks.append(None)
        response["tasks"] = tasks
    except (ValueError, TypeError, KeyError, JSONDecodeError, exceptions.InvalidTextRepresentationError):
        response["errors"] = [2, "json is not correct"]
        response["status"] = False

    return response
