import json,sys
from channels.generic.websocket import AsyncWebsocketConsumer

active_players = {}
GAME_GROUP_NAME = "game_room"

class BaseConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(GAME_GROUP_NAME, self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(GAME_GROUP_NAME, self.channel_name)

    async def send_update(self, event):
        await self.send(text_data=json.dumps(event["message"]))

class PositionConsumer(BaseConsumer):
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            player_id = data.get("player_id")
            if not player_id:
                return

            clean_id = str(player_id).split("!")[0].split(".")[-1]
            self.player_id = clean_id

            # Update or create player data
            active_players[clean_id] = {
                "x": data.get("x", 0),
                "y": data.get("y", 0),
                "health": data.get("health", 100),
                "is_flying": data.get("is_flying", False),
                "is_running": data.get("is_running", False),
                "facing_left": data.get("facing_left", False),
                "is_dead": data.get("is_dead", False),
            }

            # Immediately broadcast the updated player list
            await self.broadcast_players()

        except Exception as e:
            print(f"Position error: {e}")

    async def broadcast_players(self, player_left=None):
        try:
            # Create player data list
            player_data = []
            for pid, pdata in active_players.items():
                player_data.append({
                    "player_id": pid,
                    "x": pdata["x"],
                    "y": pdata["y"],
                    "health": pdata["health"],
                    "is_flying": pdata["is_flying"],
                    "is_running": pdata["is_running"],
                    "facing_left": pdata["facing_left"],
                    "is_dead": pdata["is_dead"],
                })
            

            # Create message with all players
            message = {"players": player_data}
        
            if player_left:
                message["player_left"] = player_left
            
              

            # Broadcast to all connected clients
            await self.channel_layer.group_send(
                GAME_GROUP_NAME,
                {
                    "type": "send_update",
                    "message": message,
                },
            )

        except Exception as e:
            print(f"Broadcast error: {e}")

    async def disconnect(self, close_code):
        if hasattr(self, 'player_id'):
            player_left = self.player_id
            if player_left in active_players:
                del active_players[player_left]
            await self.broadcast_players(player_left)
        await super().disconnect(close_code)

class BulletConsumer(BaseConsumer):
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get("type") == "bullet_spawn":
                await self.channel_layer.group_send(
                    GAME_GROUP_NAME,
                    {
                        "type": "send_update",
                        "message": {
                            "type": "bullet_spawn",
                            "player_id": data["player_id"],
                            "spawn_x": data["spawn_x"],
                            "spawn_y": data["spawn_y"],
                            "angle": data["angle"],
                            "timestamp": data.get("timestamp")
                        }
                    }
                )
        except Exception as e:
            print(f"Bullet error: {e}")

class GameStateConsumer(BaseConsumer):
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            await self.channel_layer.group_send(
                GAME_GROUP_NAME,
                {
                    "type": "send_update",
                    "message": data
                }
            )
        except Exception as e:
            print(f"GameState error: {e}")
