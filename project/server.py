import asyncio
import logging
import websockets
import json
from config import methods
from time import time
from websockets import WebSocketServerProtocol
from utils import exeptions


class Server:
    def __init__(self):
        self.clients = set()

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
                        raise exeptions.MethodIsNotExist
                    await ws.send(message)
                except exeptions.MethodIsNotExist:
                    await self._send_json(ws=ws, data={"errors": [0, "method is not exist"]})
        finally:
            await self._disconnect_client(ws)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = Server()
    start_server = websockets.serve(server.ws_handler, host="localhost", port=6876)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    loop.run_forever()
