'''Обработчик запросов приходящих на сервер'''
from exceptions import UserAlreadyExist, UserOrSpawnNotExist
from json.decoder import JSONDecodeError
from aiohttp.web import json_response, Request, Response
import staff


async def register_user(request: Request) -> json_response:
    '''Метод регистрации игрока'''
    response = {"status": False}
    try:
        data: dict = await request.json()
        token = await staff.make_user(
            pool=request.app["pool"],
            vk_id=data["vk_id"],
            username=data["username"]
        )
        response["status"] = True
        response["token"] = token
    except (ValueError, KeyError, JSONDecodeError):
        response["errors"] = [2, "json is not correct"]
    except UserAlreadyExist:
        response["errors"] = [3, "user already exist"]

    return json_response(response)


async def get_spawn(request: Request) -> json_response:
    '''Возвращает координаты спауна игрока'''
    response = {"status": False}
    try:
        data: dict = await request.json()
        spawn = await staff.get_spawn_coords(
            pool=request.app["pool"],
            vk_id=data["vk_id"]
        )
        response["status"] = True
        response["coords"] = {"x": spawn["x"], "y": spawn["y"]}
    except UserOrSpawnNotExist:
        response["errors"] = [5, "User or Spawn are not exist"]
    except (ValueError, KeyError, JSONDecodeError):
        response["errors"] = [2, "json is not correct"]

    return json_response(response)


async def gen_mapobjects(request: Request) -> json_response:
    '''Метод генерации рандомных объектов на карте'''
    #try:
    await staff.gen_objects(pool=request.app["pool"])
    return Response()
    # except:
    #     return Response(status=300)


async def get_map(request: Request) -> json_response:
    '''Возвращает объекты расположенные на карте'''
    response = {"status": True, "game_objects": None}
    try:
        data: dict = await request.json()
        map_objects = await staff.get_map(
            pool=request.app["pool"],
            x_coord=data["coords"][0],
            y_coord=data["coords"][1],
            width=data["scope"][0],
            height=data["scope"][1]
        )

        if map_objects:
            game_objects = []
            for map_object in map_objects:
                game_object = {
                    "name": map_object["name"],
                    "owner": map_object["vk_id"],
                    "health": map_object["health"],
                    "type": map_object["object_type"],
                    "coords": {
                        "x": map_object["x"],
                        "y": map_object["y"]
                    }
                }
                game_objects.append(game_object)
            response["game_objects"] = game_objects
    except (ValueError, KeyError, JSONDecodeError):
        response["status"] = False
        response["errors"] = [2, "json is not correct"]

    return json_response(response)
