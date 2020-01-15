'''Входная точка приложения'''
import asyncio
import asyncpg
from aiohttp import web
import config
from urls import URLS


async def init_app():
    '''Ицициализация приложения'''
    __app = web.Application()
    __app["pool"] = await asyncpg.create_pool(dsn=config.DESTINATION)
    __app.router.add_routes(URLS)
    return __app


if __name__ == "__main__":
    LOOP = asyncio.get_event_loop()
    APP = LOOP.run_until_complete(init_app())
    web.run_app(APP)
