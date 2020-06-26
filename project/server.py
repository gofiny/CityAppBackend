import asyncio
import asyncpg
import aioredis
import logging
import websockets
import json
from config import DESTINATION, REDIS_ADDR
from methods import methods
from time import time
from websockets import WebSocketServerProtocol
from utils import exceptions, init_dbs


class Server:
    def __init__(self):
        self.clients = set()
        self.redis_connections_count = 0
        self.pg_pool = None
        self.redis_pool = None
        
    async def create_pools(self) -> None:
        self.pg_pool = await asyncpg.create_pool(dsn=DESTINATION)
        self.redis_pool = await aioredis.create_pool(address=REDIS_ADDR, db=0)

    async def get_redis_connection(self) -> aioredis.RedisConnection:
        conn = await self.redis_pool.get_connection()[0]
        if conn:
            return conn
        self.redis_connections_count += 1
        return await self.redis_pool.acquire()

    async def _connect_client(self, ws: WebSocketServerProtocol) -> None:
        self.clients.add(ws)
        logging.info(f"{ws.remote_address} connected")

    async def _disconnect_client(self, ws: WebSocketServerProtocol) -> None:
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnected")

    async def _get_json_data(self, message: str) -> dict:
        return json.loads(message)

    async def _send_json(self, ws: WebSocketServerProtocol, data: dict) -> None:
        data["timestamp"] = int(time())
        await ws.send(json.dumps(data))

    async def ws_handler(self, ws: WebSocketServerProtocol, path: str) -> None:
        await self._connect_client(ws)
        try:
            async for message in ws:
                try:
                    data = await self._get_json_data(message)
                    if data["method"] not in methods:
                        raise exceptions.MethodIsNotExist
                    methods[data["method"]](pool=self.pg_pool, **data["data"])
                except exceptions.MethodIsNotExist:
                    await self._send_json(ws=ws, data=exceptions.errors[0])
                except TypeError:
                    await self._send_json(ws=ws, data=exceptions.errors[1])
        finally:
            await self._disconnect_client(ws)


async def prepare(server: Server) -> None:
    await server.create_pools()
    await init_dbs.create_databases(pool=server.pg_pool)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    server = Server()
    loop.run_until_complete(prepare(server))
    start_server = websockets.serve(server.ws_handler, host="localhost", port=6876)
    loop.run_until_complete(start_server)
    loop.run_forever()
