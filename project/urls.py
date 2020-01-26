'''Роутинг запросов приходящих на приложение'''
from aiohttp import web
from handlers import (
    register_user,
    gen_mapobjects,
    get_map, test,
    get_profile,
    get_object_info,
    get_player_pawns
)


URLS = [
    web.post("/async/register_user", register_user),
    web.post("/async/gen_objects", gen_mapobjects),
    web.post("/async/get_map", get_map),
    web.post("/async/test", test),
    web.post("/async/get_profile", get_profile),
    web.post("/async/get_object_info", get_object_info),
    web.post("/async/get_player_pawns", get_player_pawns)
]
