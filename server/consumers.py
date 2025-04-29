import json
from channels.generic.websocket import AsyncWebsocketConsumer

active_players = {}

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.group_name = "game"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

    async def disconnect(self, close_code):
        player_id = getattr(self, "player_id", None)
        print(f"[DISCONNECTED] Player left: {player_id}")

        if player_id and player_id in active_players:
            del active_players[player_id]
            print(f"[DEBUG] Removed player: {player_id}")
            await self.broadcast_players(player_left=player_id)

        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get("type") == "bullet":
                print(f"[DEBUG] Bullet received: {data}")
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "send_update",
                        "message": data  
                    }
                )
                return 

            player_id = data.get("player_id")
            if not player_id:
                return  

           
            clean_id = str(player_id).split("!")[0].split(".")[-1]
            self.player_id = clean_id

            
            active_players[clean_id] = {
                "x": data.get("x", 0),
                "y": data.get("y", 0),
                "health": data.get("health", 100),
                "is_flying": data.get("is_flying", False),
                "is_running": data.get("is_running", False),
                "facing_left": data.get("facing_left", False),
            }

            await self.broadcast_players()

             

        except Exception as e:
            print(f"[ERROR] receive() failed: {e}")

    async def broadcast_players(self, player_left=None):
        player_data = [
            {
                "player_id": pid,
                "x": pdata["x"],
                "y": pdata["y"],
                "health": pdata["health"],
                "is_flying": pdata["is_flying"],
                "is_running": pdata["is_running"],
                "facing_left": pdata["facing_left"],
            }
            for pid, pdata in active_players.items()
        ]

        message = {"players": player_data}
        if player_left:
            message["player_left"] = player_left

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "send_update",
                "message": message,
            },
        )

    async def send_update(self, event):
        try:
            message = event["message"]
            if message.get("type") == "bullet":
                print(f"[DEBUG] Broadcasting bullet data to client: {message}")
            await self.send(text_data=json.dumps(event["message"]))
        except Exception as e:
            print(f"[ERROR] send_update() failed: {e}")
