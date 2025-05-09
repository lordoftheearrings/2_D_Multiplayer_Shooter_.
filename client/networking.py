import asyncio
import websockets
import json
import time
from utils import *
from player import RemotePlayer

class WebSocketClient:
    def __init__(self, uri, player, other_players, camera, game_map=None):
        self.uri = uri.rstrip('/')
        self.player = player
        self.other_players = other_players
        self.camera = camera
        self.game_map = game_map
        self.remote_bullets = []
        self.position_ws = None
        self.bullet_ws = None
        self.state_ws = None
        self.position_queue = []
        self.bullet_queue = []
        self.state_queue = []
        self.last_position_send = 0
        self.last_bullet_send = 0
        self.last_state_send = 0
        self.position_rate = 20  
        self.bullet_rate = 20    
        self.state_rate = 100    
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.reconnect_delay = 1
        self.max_reconnect_delay = 30
        self.is_connecting = False
        self.receive_tasks = {}
        self.stop_event = asyncio.Event()
        self.last_connection_attempt = {}
        self.min_connection_interval = 2  

    async def connect_with_retry(self, websocket_url):
        while not self.stop_event.is_set():
            current_time = time.time()
            last_attempt = self.last_connection_attempt.get(websocket_url, 0)
            
            # Wait if we've tried to connect too recently
            if current_time - last_attempt < self.min_connection_interval:
                await asyncio.sleep(self.min_connection_interval - (current_time - last_attempt))
                continue
                
            self.last_connection_attempt[websocket_url] = current_time
            
            try:
                ws = await websockets.connect(websocket_url)
                self.reconnect_delay = 1
                return ws
            except Exception as e:
                print(f"Failed to connect to {websocket_url}: {e}")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)

    async def connect(self):
        if self.is_connecting:
            return
        
        self.is_connecting = True
        try:
            self.position_ws = await self.connect_with_retry("ws://localhost:8000/ws/game/position/{self.lobby_id}/")
            await asyncio.sleep(1)  # Wait 1 second between connections
            
            self.bullet_ws = await self.connect_with_retry("ws://localhost:8000/ws/game/bullets/{self.lobby_id}/")
            await asyncio.sleep(1)
            
            self.state_ws = await self.connect_with_retry("ws://localhost:8000/ws/game/state/{self.lobby_id}/")
            
            # Cancel any existing receive tasks
            for task in self.receive_tasks.values():
                task.cancel()
            self.receive_tasks.clear()
            
            # Start new receive tasks
            self.receive_tasks['position'] = self.loop.create_task(self.receive_position_updates())
            self.receive_tasks['bullet'] = self.loop.create_task(self.receive_bullet_updates())
            self.receive_tasks['state'] = self.loop.create_task(self.receive_game_state())
            
        except Exception as e:
            print(f"Failed to connect to WebSocket server: {e}")
            raise
        finally:
            self.is_connecting = False

    async def disconnect(self):
        self.stop_event.set()
        for task in self.receive_tasks.values():
            task.cancel()
        self.receive_tasks.clear()
        
        for ws in [self.position_ws, self.bullet_ws, self.state_ws]:
            if ws:
                try:
                    await ws.close()
                except Exception as e:
                    print(f"Error closing WebSocket connection: {e}")

    async def reconnect(self, websocket_type):
        if self.is_connecting:
            return
            
        self.is_connecting = True
        try:
            if websocket_type == "position":
                if self.receive_tasks.get('position'):
                    self.receive_tasks['position'].cancel()
                self.position_ws = await self.connect_with_retry("ws://localhost:8000/ws/game/position/")
                self.receive_tasks['position'] = self.loop.create_task(self.receive_position_updates())
            elif websocket_type == "bullet":
                if self.receive_tasks.get('bullet'):
                    self.receive_tasks['bullet'].cancel()
                self.bullet_ws = await self.connect_with_retry("ws://localhost:8000/ws/game/bullets/")
                self.receive_tasks['bullet'] = self.loop.create_task(self.receive_bullet_updates())
            elif websocket_type == "state":
                if self.receive_tasks.get('state'):
                    self.receive_tasks['state'].cancel()
                self.state_ws = await self.connect_with_retry("ws://localhost:8000/ws/game/state/")
                self.receive_tasks['state'] = self.loop.create_task(self.receive_game_state())
        finally:
            self.is_connecting = False

    async def send_position(self):
        if not self.position_ws:
            await self.reconnect("position")
            return

        current_time = time.time() * 1000
        if current_time - self.last_position_send >= self.position_rate:
            try:
                data = {
                    "player_id": self.player.id,
                    "x": self.player.x,
                    "y": self.player.y,
                    "health": self.player.health,
                    "is_flying": self.player.is_flying,
                    "is_running": self.player.is_running,
                    "facing_left": self.player.facing_left,
                    "is_dead": self.player.is_dead,
                    
                }
                await self.position_ws.send(json.dumps(data))
                self.last_position_send = current_time

                if self.player.firing_manager and self.player.firing_manager.new_bullets:
                    for bullet in self.player.firing_manager.new_bullets:
                        await self.send_bullet_spawn(self.player.id, bullet.spawn_x, bullet.spawn_y, bullet.angle)
                    self.player.firing_manager.new_bullets.clear()

            except websockets.ConnectionClosed:
                await self.reconnect("position")
            except Exception as e:
                print(f"Failed to send position update: {e}")

    def send_from_main_thread(self):
        if self.loop and not self.loop.is_closed():
            try:
                self.loop.call_soon_threadsafe(asyncio.create_task, self.send_position())
            except RuntimeError as e:
                if "closed" in str(e):
                    self.loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(self.loop)
                    self.loop.call_soon_threadsafe(asyncio.create_task, self.send_position())

    async def send_bullet_spawn(self, player_id, spawn_x, spawn_y, angle):
        if not self.bullet_ws:
            await self.reconnect("bullet")
            return

        current_time = time.time() * 1000
        if current_time - self.last_bullet_send >= self.bullet_rate:
            try:
                await self.bullet_ws.send(json.dumps({
                    "type": "bullet_spawn",
                    "player_id": player_id,
                    "spawn_x": spawn_x,
                    "spawn_y": spawn_y,
                    "angle": angle,
                    "timestamp": current_time
                }))
                self.last_bullet_send = current_time
            except websockets.ConnectionClosed:
                await self.reconnect("bullet")
            except Exception as e:
                print(f"Failed to send bullet spawn: {e}")

    async def send_game_state(self, message_type, data):
        if not self.state_ws:
            await self.reconnect("state")
            return

        current_time = time.time() * 1000
        if current_time - self.last_state_send >= self.state_rate:
            try:
                await self.state_ws.send(json.dumps({
                    "type": message_type,
                    "data": data,
                    "timestamp": current_time
                }))
                self.last_state_send = current_time
            except websockets.ConnectionClosed:
                await self.reconnect("state")
            except Exception as e:
                print(f"Failed to send game state: {e}")

    async def receive_position_updates(self):
        while not self.stop_event.is_set():
            if not self.position_ws:
                await self.reconnect("position")
                continue

            try:
                message = await self.position_ws.recv()
                data = json.loads(message)
                await self.handle_position_update(data)
            except websockets.ConnectionClosed:
                await self.reconnect("position")
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Failed to receive position update: {e}")
                await asyncio.sleep(1)

    async def receive_bullet_updates(self):
        while not self.stop_event.is_set():
            if not self.bullet_ws:
                await self.reconnect("bullet")
                continue

            try:
                message = await self.bullet_ws.recv()
                data = json.loads(message)
                await self.handle_bullet_update(data)
            except websockets.ConnectionClosed:
                await self.reconnect("bullet")
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Failed to receive bullet update: {e}")
                await asyncio.sleep(1)

    async def receive_game_state(self):
        while not self.stop_event.is_set():
            if not self.state_ws:
                await self.reconnect("state")
                continue

            try:
                message = await self.state_ws.recv()
                data = json.loads(message)
                await self.handle_game_state(data)
            except websockets.ConnectionClosed:
                await self.reconnect("state")
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Failed to receive game state: {e}")
                await asyncio.sleep(1)

    async def handle_position_update(self, data):
        try:
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
                        remote_player.is_dead = player_data.get("is_dead", False)
                    else:
                        new_remote = RemotePlayer(
                            pid,
                            player_data["x"],
                            player_data["y"],
                            REMOTE_PLAYER_COLOR,
                            self.camera,
                            self.game_map,
                        )
                        new_remote.health = player_data.get("health", 100)
                        new_remote.is_flying = player_data.get("is_flying", False)
                        new_remote.is_running = player_data.get("is_running", False)
                        new_remote.facing_left = player_data.get("facing_left", False)
                        new_remote.is_dead = player_data.get("is_dead", False)
                        self.other_players[pid] = new_remote

            if "player_left" in data:
                pid = data["player_left"]
                if pid in self.other_players:
                    del self.other_players[pid]
        except Exception as e:
            print(f"Failed to handle position update: {e}")

    async def handle_bullet_update(self, data):
        try:
            if data.get("type") == "bullet_spawn":
                pid = data["player_id"]
                if pid != self.player.id and pid in self.other_players:
                    remote_player = self.other_players[pid]
                    remote_player.spawn_remote_bullet(
                        data["spawn_x"],
                        data["spawn_y"],
                        data["angle"]
                    )
        except Exception as e:
            print(f"Failed to handle bullet update: {e}")

    async def handle_game_state(self, data):
        try:
            pass
        except Exception as e:
            print(f"Failed to handle game state: {e}")

    def start(self):
        def run_loop():
            self.loop.run_forever()
        
        import threading
        self.thread = threading.Thread(target=run_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)
            if hasattr(self, 'thread'):
                self.thread.join()
    
    
