from aiohttp.web import json_response
from json.decoder import JSONDecodeError
from exceptions import UserAlreadyExist
import staff


@staff.check_token
async def test_api(request):
    data = await request.json()

    return json_response({"status": True})


async def register_user(request):
    response = {"status": False}
    try:
        data = await request.json()
        token = await staff.create_user(pool=request.app["pool"], vk_id=data["vk_id"], username=data["username"])
        response["status"] = True
        response["token"] = token
    except (ValueError, KeyError, JSONDecodeError):
        response["errors"] = [2, "json is not correct"]
    except UserAlreadyExist:
        response["errors"] = [3, "user already exist"]

    return json_response(response)
