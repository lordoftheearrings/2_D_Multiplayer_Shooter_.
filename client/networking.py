import asyncio
import websockets
import json
import time

class WebSocketClient:
    def __init__(self, uri, player, other_players):
        self.uri = uri
        self.player = player
        self.other_players = other_players
        self.ws = None
        self.loop = None
        self.last_send_time = 0

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    self.ws = websocket
                    self.loop = asyncio.get_running_loop()

                    await self.send_position()
                    async for message in websocket:
                        await self.handle_message(message)
            except Exception as e:
                print(f"[WebSocket Error] {e}")
                await asyncio.sleep(5)

    async def send_position(self):
        now = time.time()
        if now - self.last_send_time >= 0.03:
            try:
                data = {
                    "player_id": self.player.id,
                    "x": self.player.x,
                    "y": self.player.y
                }
                await self.ws.send(json.dumps(data))
                self.last_send_time = now
            except Exception as e:
                print("[Send Error]", e)

    def send_from_main_thread(self):
        if self.ws and self.loop:
            self.loop.call_soon_threadsafe(asyncio.create_task, self.send_position())

    async def handle_message(self, message):
        try:
            data = json.loads(message)
            players = data.get("players", [])
            for player in players:
                pid = player["player_id"]
                if pid != self.player.id:
                    self.other_players[pid] = (player["x"], player["y"])

            if "player_left" in data:
                pid = data["player_left"]
                if pid in self.other_players:
                    del self.other_players[pid]
        except Exception as e:
            print("[Message Handling Error]", e)
