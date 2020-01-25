'''Роутинг запросов приходящих на приложение'''
from aiohttp import web
from handlers import register_user, gen_mapobjects, get_map


URLS = [
    web.post("/async/register_user", register_user),
    web.post("/async/gen_objects", gen_mapobjects),
    web.post("/async/get_map", get_map)
]
