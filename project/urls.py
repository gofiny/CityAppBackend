'''Роутинг запросов приходящих на приложение'''
from aiohttp import web
from handlers import register_user, get_spawn, gen_mapobjects, get_map


URLS = [
    web.post("/register_user", register_user),
    web.post("/get_spawn", get_spawn),
    web.post("/gen_objects", gen_mapobjects),
    web.post("/get_map", get_map)
]
