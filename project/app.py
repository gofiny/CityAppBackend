import asyncio
import asyncpg
import config
from aiohttp import web
from urls import urls


async def init_app():
    app = web.Application()
    app["pool"] = await asyncpg.create_pool(dsn=config.DESTINATION)
    app.router.add_routes(urls)
    return app


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    web.run_app(app)
