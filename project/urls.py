'''Роутинг запросов приходящих на приложение'''
from aiohttp import web
from handlers import (
    register_user,
    get_map, 
    test,
    get_profile,
    get_object_info,
    get_player_pawns,
    gen_new_object,
    get_tile,
    add_task_to_pawn,
    get_available_tasks_count,
    get_player_resources,
    check_connection,
    accept_task
)


URLS = [
    web.post("/async/register_user", register_user),
    web.post("/async/get_map", get_map),
    web.post("/async/test", test),
    web.post("/async/get_profile", get_profile),
    web.post("/async/get_object_info", get_object_info),
    web.post("/async/get_player_pawns", get_player_pawns),
    web.post("/async/gen_new_object", gen_new_object),
    web.post("/async/get_tile", get_tile),
    web.post("/async/add_task_to_pawn", add_task_to_pawn),
    web.post("/async/get_available_actions_count", get_available_tasks_count),
    web.post("/async/get_player_resources", get_player_resources),
    web.post("/async/check_connection", check_connection),
    web.post("/async/accept_task", accept_task)
]
