
import json
from channels.generic.websocket import AsyncWebsocketConsumer

active_players = {}

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.group_name = "game"

        # Add to broadcast group
        await self.channel_layer.group_add(self.group_name, self.channel_name)

    async def disconnect(self, close_code):
        player_id = getattr(self, "player_id", None)
        print(f"[DISCONNECTED] Player left: {player_id}")

        if player_id:
            if player_id in active_players:
                del active_players[player_id]
                print(f"[DEBUG] Removed player: {player_id}")
            else:
                print(f"[DEBUG] Player {player_id} not found in active_players")

            await self.broadcast_players(player_left=player_id)

        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            player_id = data.get("player_id")
            x = data.get("x")
            y = data.get("y")

            # Sanitize: store only clean IDs (e.g., "8375")
            clean_id = str(player_id).split("!")[0].split(".")[-1]
            self.player_id = clean_id

            # Update player position
            active_players[clean_id] = {"x": x, "y": y}

            await self.broadcast_players()

        except Exception as e:
            print(f"[ERROR] receive() failed: {e}")

    async def broadcast_players(self, player_left=None):
        player_data = [
            {"player_id": pid, "x": pos["x"], "y": pos["y"]}
            for pid, pos in active_players.items()
        ]

        message = {"players": player_data}
        if player_left:
            message["player_left"] = player_left

        print(f"[BROADCAST] Sending data: {message}")

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "send_update",
                "message": message,
            },
        )

    async def send_update(self, event):
        try:
            await self.send(text_data=json.dumps(event["message"]))
        except Exception as e:
            print(f"[ERROR] send_update() failed: {e}")
