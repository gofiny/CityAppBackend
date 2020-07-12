import asyncio
import websockets
import json
from time import sleep


SERVER_URI = "ws://localhost:6876"

async def connect():
    async with websockets.connect(SERVER_URI) as websocket:
        data = {"method": "register", "data": {"gp_id": "gsddsgsd", "username": "tdfest"}}
        await websocket.send(json.dumps(data))
        answer = await websocket.recv()
        print(answer)

    print("loop has done")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(connect())