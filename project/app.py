'''Входная точка приложения'''
import asyncio
import argparse
import logging
import asyncpg
from aiohttp import web
import config
from urls import URLS


async def init_app():
    '''Ицициализация приложения'''
    #stio_handler = logging.StreamHandler()
    #stio_handler.setLevel(logging.INFO)
    #file_logs = logging.FileHandler("server.log")
    #file_logs.setLevel(logging.INFO)
    #_logger = logging.getLogger('aiohttp.access')
    #_logger.addHandler(file_logs)
    #_logger.addHandler(stio_handler)
    #_logger.setLevel(logging.DEBUG)
    __app = web.Application()
    __app["pool"] = await asyncpg.create_pool(dsn=config.DESTINATION)
    __app["websockets"] = []
    __app.router.add_routes(URLS)
    return __app


async def on_shutdown(app):
    for ws in app["websockets"]:
        await ws.close(code=999, message="Server shutdown")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path')
    LOOP = asyncio.get_event_loop()
    APP = LOOP.run_until_complete(init_app())
    APP.on_shutdown.append(on_shutdown)
    args = parser.parse_args()
    web.run_app(APP, access_log_format='%t %a "%r" -> [%s] %b bytes in %Tf seconds.', path=args.path)
