from handlers import test_api
from aiohttp import web


urls = [
    web.post("/test", test_api),
]
