import asyncio
import logging
import websockets
from websockets import WebSocketServerProtocol


class Server:
    def __init__(self):
        self.clients = set()

    async def _connect_client(self, ws: WebSocketServerProtocol) -> None:
        self.clients.add(ws)
        logging.info(f"{ws.remote_address} connected")

    async def _disconnect_client(self, ws: WebSocketServerProtocol) -> None:
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} dissconected")

    async def ws_handler(self, ws: WebSocketServerProtocol, path: str) -> None:
        await self._connect_client(ws)
        try:
            async for message in ws:
                logging.info(f"receive: {message}")
                await ws.send(message)
        finally:
            await self._disconnect_client(ws)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = Server()
    start_server = websockets.serve(server.ws_handler, host="localhost", port=6876)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    loop.run_forever()
