'''Обработчик запросов приходящих на сервер'''
from exceptions import UserAlreadyExist, UserOrSpawnNotExist
from json.decoder import JSONDecodeError
from aiohttp.web import json_response, Request, Response
import staff


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
    except (ValueError, KeyError, JSONDecodeError):
        response["errors"] = [2, "json is not correct"]
    except UserAlreadyExist:
        response["errors"] = [3, "user already exist"]

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
    except (ValueError, KeyError, JSONDecodeError):
        response["status"] = False
        response["errors"] = [2, "json is not correct"]

    return json_response(response)


@staff.check_token
async def get_profile(request: Request) -> json_response:
    '''Возвращает инфу о игроке'''
    response = {"status": True}
    try:
        data = await request.json()
        profile_info = await staff.get_profile_info(
            pool=request.app["pool"],
            user_id=data["user_id"]
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
    except (KeyError, ValueError, JSONDecodeError):
        response["status"] = False
        response["errors"] = [2, "json is not correct"]

    return json_response(response)


async def get_object_info(request: Request) -> json_response:
    '''Возвращает информацию о конкретном объекте'''
    response = {"status": False}
    try:
        data = await request.json()
        game_object = await staff.get_object(
            pool=request.app['pool'],
            object_uuid=data["uuid"]
        )
        if game_object:
            response["status"] = True
            response["name"] = game_object["name"]
            response["object_type"] = game_object["object_type"]
            response["owner"] = game_object["username"]
            response["health"] = game_object["health"]
            response["coors"] = {
                "x": game_object["x"],
                "y": game_object["y"]
            }
        else:
            response["errors"] = [6, "game_object is not found"]
    except (KeyError, ValueError, JSONDecodeError):
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
                response_pawns.append(
                    {
                        "uuid": str(pawn["uuid"]),
                        "name": pawn["name"],
                        "health": pawn["health"],
                        "max_tasks": pawn["max_tasks"]
                    }
                )
        response["pawns"] = response_pawns
    except (KeyError, ValueError, JSONDecodeError):
        response["errors"] = [2, "json is not correct"]

    return json_response(response)
