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
