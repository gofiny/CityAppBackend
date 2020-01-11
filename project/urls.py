from handlers import test_api, register_user
from aiohttp import web


urls = [
    web.post("/test", test_api),
    web.post("/register_user", register_user)
]
