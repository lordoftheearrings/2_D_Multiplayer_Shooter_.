import asyncio
import websockets
import json
import time
from utils import *
from player import RemotePlayer

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
        if now - self.last_send_time >= 0.03:  # 30ms cap
            try:
                data = {
                    "player_id": self.player.id,
                    "x": self.player.x,
                    "y": self.player.y,
                    "health": self.player.health,
                    "is_flying": self.player.is_flying,
                    "is_running": self.player.is_running,#abs(self.player.velocity_x) > 0.5 and self.player.on_ground,
                    "facing_left": self.player.facing_left
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
            for player_data in players:
                pid = player_data["player_id"]
                if pid != self.player.id:
                    if pid in self.other_players:
                        remote_player = self.other_players[pid]
                        remote_player.x = player_data["x"]
                        remote_player.y = player_data["y"]
                        remote_player.health = player_data.get("health", 100)
                        remote_player.is_flying = player_data.get("is_flying", False)
                        remote_player.is_running = player_data.get("is_running", False)
                        remote_player.facing_left = player_data.get("facing_left", False)
                    else:
                        # --- Create new RemotePlayer directly ---
                        new_remote = RemotePlayer(
                            pid,
                            player_data["x"],
                            player_data["y"],
                            REMOTE_PLAYER_COLOR
                        )
                        new_remote.health = player_data.get("health", 100)
                        new_remote.is_flying = player_data.get("is_flying", False)
                        new_remote.is_running = player_data.get("is_running", False)
                        new_remote.facing_left = player_data.get("facing_left", False)
                        self.other_players[pid] = new_remote

            if "player_left" in data:
                pid = data["player_left"]
                if pid in self.other_players:
                    del self.other_players[pid]
        except Exception as e:
            print("[Message Handling Error]", e)
