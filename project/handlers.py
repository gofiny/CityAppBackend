from aiohttp.web import json_response
from json.decoder import JSONDecodeError


async def test_api(request):
    response = {"status": True}
    try:
        data = await request.json()
    except JSONDecodeError:
        status = False
        errors = [2, "json is not correct"]
        response["errors"] = errors
        response["status"] = status

    return json_response(response)