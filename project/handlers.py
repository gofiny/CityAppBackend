'''Обработчик запросов приходящих на сервер'''
from asyncpg import exceptions
from exceptions import UserAlreadyExist, ObjectNotExist
from json.decoder import JSONDecodeError
from aiohttp.web import json_response, Request, Response
import staff
import sys


async def test(request: Request) -> json_response:
    return json_response({"status": True})


async def register_user(request: Request) -> json_response:
    '''Метод регистрации игрока'''
    response = {"status": False}
    try:
        data: dict = await request.json()
        token = await staff.make_user(
            pool=request.app["pool"],
            user_id=data["user_id"],
            username=data["username"]
        )
        response["status"] = True
        response["token"] = token
    except (TypeError, ValueError, KeyError, JSONDecodeError):
        response["errors"] = [2, "json is not correct"]
    except exceptions.StringDataRightTruncationError:
        response["errors"] = [7, "some data is too long"]
    except UserAlreadyExist:
        response["errors"] = [3, "user already exist"]

    return json_response(response)


async def get_map(request: Request) -> json_response:
    '''Возвращает объекты расположенные на карте'''
    response = {"status": True, "game_objects": None}
    try:
        data: dict = await request.json()
        map_objects = await staff.get_map(
            pool=request.app["pool"],
            x_coord=data["coors"]["x"],
            y_coord=data["coors"]['y'],
            width=data["scope"]["width"],
            height=data["scope"]["height"]
        )

        if map_objects:
            game_objects = []
            for map_object in map_objects:
                game_object = {
                    "uuid": str(map_object["uuid"]),
                    "name": map_object["name"],
                    "owner": map_object["username"],
                    "health": map_object["health"],
                    "type": map_object["object_type"],
                    "coors": {
                        "x": map_object["x"],
                        "y": map_object["y"]
                    }
                }
                game_objects.append(game_object)
            response["game_objects"] = game_objects
    except (TypeError, ValueError, KeyError, JSONDecodeError):
        response["status"] = False
        response["errors"] = [2, "json is not correct"]

    return json_response(data=response)


async def get_profile(request: Request) -> json_response:
    '''Возвращает инфу о игроке'''
    response = {"status": True}
    try:
        data = await request.json()
        profile_info = await staff.get_profile_info(
            pool=request.app["pool"],
            token=data["token"]
        )
        response["username"] = profile_info["username"]
        response["resources"] = {
            "money": profile_info["money"],
            "stones": profile_info["stones"],
            "wood": profile_info["wood"]
        }
        response["spawn"] = {
            "x": profile_info['x'],
            "y": profile_info['y']
        }
    except (TypeError, KeyError, ValueError, JSONDecodeError):
        response["status"] = False
        response["errors"] = [2, "json is not correct"]

    return json_response(response)


async def get_object_info(request: Request) -> json_response:
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
            response["object_uuid"] = data["object_uuid"]
            response["name"] = game_object["name"]
            response["object_type"] = game_object["object_type"]
            response["owner"] = game_object["username"]
            response["health"] = game_object["health"]
            response["coors"] = {
                "x": game_object["x"],
                "y": game_object["y"]
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
                    pawn_actions = []
                    for action in actions:
                        pawn_actions.append({
                            "task_uuid": action["uuid"],
                            "task_name": action["task_name"],
                            "start_time": action["start_time"]
                        })
                    tasks = pawn_actions
                response["tasks"] = tasks

                available_tasks = await staff.get_available_tasks(
                    pool=request.app["pool"],
                    gameobject_uuid=game_object["uuid"]
                )
                _enabled = False
                if game_object["max_tasks"] > len(tasks):
                    _enabled = True
                actions = []
                for task in available_tasks:
                    actions.append({
                        "task_name": task["name"],
                        "enabled": _enabled
                    })
                response["available_tasks"] = tasks
        else:
            response["errors"] = [6, "game_object is not found"]
    except (TypeError, KeyError, ValueError, JSONDecodeError):
        response["errors"] = [2, "json is not correct"]

    return json_response(response)


async def get_player_pawns(request: Request) -> json_response:
    '''Возвращает список всех пешек игрока'''
    response = {"status": True}
    try:
        data = await request.json()
        pawns = await staff.get_pawns(
            pool=request.app['pool'],
            token=data['token']
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
                    "max_actions": pawn["max_actions"]
                })
        response["pawns"] = response_pawns
    except (TypeError, KeyError, ValueError, JSONDecodeError):
        response["errors"] = [2, "json is not correct"]

    return json_response(response)


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


async def get_tile(request: Request) -> json_response:
    '''Получение тайла по координатам'''
    response = {"status": True, "game_object": None}
    try:
        data = await request.json()
        tile = await staff.get_object_by_coors(
            pool=request.app["pool"],
            x=data["coors"]["x"],
            y=data["coors"]["y"]
        )
        if tile:
            response["game_object"] = {
                "uuid": str(tile["uuid"]),
                "name": tile["name"],
                "object_type": tile["object_type"],
                "health": tile["health"],
                "owner": tile["username"]
            }
    except (KeyError, ValueError, TypeError, JSONDecodeError):
        response["status"] = False
        response["errors"] = [2, "json is not correct"]

    return json_response(response)


async def add_task_to_pawn(request: Request) -> json_response:
    response = {"status": False}
    try:
        data = await request.json()
        response = await staff.add_pretask_to_pawn(
            pool=request.app["pool"],
            object_uuid=data["object_uuid"],
            token=data["token"],
            task_name=data["task_name"]
        )
        response["status"] = True
    except (KeyError, ValueError, TypeError, JSONDecodeError):
        response["errors"] = [2, "json is not correct"]
    return json_response(response, )


async def get_available_tasks_count(request: Request) -> json_response:
    response = {"status": False}
    try:
        data = await request.json()
        available_tasks = await staff.get_available_tasks_by_mo(
            pool=request.app["pool"],
            object_uuid=data["object_uuid"],
            token=data["token"]
        )

        if not available_tasks:
            response["erros"] = [6, "object_uuid or token not correct"]
        else:
            response["status"] = True
            response["count"] = len(available_tasks)
    except (KeyError, ValueError, TypeError, JSONDecodeError, exceptions.InvalidTextRepresentationError):
        response["errors"] = [2, "json is not correct"]

    return json_response(response)


async def get_player_resources(request: Request) -> json_response:
    response = {"status": False}
    try:
        data = await request.json()
        resources = await staff.get_player_resources_by_names(
            pool=request.app["pool"],
            token=data["token"],
            res_name=data["resource"]
        )
        if resources:
            response["status"] = True
            response["resources"] = [{k: v} for k, v in resources.items() if k not in ["uuid", "player"]]
        else:
            response["errors"] = [1, "token not correct"]
    except (KeyError, ValueError, TypeError, JSONDecodeError):
        response["erros"] = [2, "json is not correct"]
    except exceptions.UndefinedColumnError:
        response["errors"] = [5, "resource name is not correct"]
        

    return json_response(response)


async def check_connection(request: Request) -> json_response:
    '''Тест соединения'''
    return json_response({"status": True})


async def accept_task(request: Request) -> json_response:
    response = {"status": True}
    try:
        data = await request.json()
        action = await staff.procced_task(
            pool=request.app["pool"],
            task_uuid=data["task_uuid"],
            accept=data["accept"]
        )
        if action:
            response["task_uuid"] = action[1]
            response["action_name"] = action[2]
            response["start_time"] = action[3]
            response["end_time"] = action[4]
    except (ValueError, TypeError, KeyError, JSONDecodeError, exceptions.InvalidTextRepresentationError):
        response["status"] = True
        response["errors"] = [2, "json is not correct"]

    return json_response(response)
