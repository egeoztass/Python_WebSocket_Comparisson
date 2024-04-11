import asyncio
import websockets
async def hello():
    uri = "ws://localhost:8888"
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello, World!")
        response = await websocket.recv()
        print(f"Received from server: {response}")


asyncio.get_event_loop().run_until_complete(hello())
