import asyncio
import websockets
from time import sleep


SERVER_URI = "ws://localhost:6876"

async def connect():
    async with websockets.connect(SERVER_URI) as websocket:
        await websocket.send("i`m trying to connect")
        answer = await websocket.recv()
        print(answer)

        sleep(5)

        await websocket.send("sent again after sleeping")
        answer = await websocket.recv()
        print(answer)

    print("loop has done")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(connect())