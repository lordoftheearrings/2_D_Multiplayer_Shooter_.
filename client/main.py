import pygame
import sys
import asyncio
import threading
import json
import websockets
import random
import time

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((500, 500))
pygame.display.set_caption("Game 1st Draft")
clock = pygame.time.Clock()

# Font for player names 
font = pygame.font.SysFont(None, 24)

player_color = (0, 255, 0)
player_pos = [random.randint(50, 450), random.randint(50, 450)]
player_size = 30
player_id = str(random.randint(1000, 9999))

other_players = {}

# Global websocket reference and loop
ws = None
ws_loop = None
last_send_time = time.time()

# Coroutine to connect and handle incoming WebSocket data
async def websocket_handler():
    global ws, ws_loop
    uri = "ws://127.0.0.1:8000/ws/game/"
    
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                ws = websocket
                ws_loop = asyncio.get_running_loop()
                print(f"Connected to WebSocket server at {uri}")
                await ws.send(json.dumps({
                    "player_id": player_id,
                    "x": player_pos[0],
                    "y": player_pos[1],
                }))
                print(f"Sent initial position: {player_pos}")

                async for message in ws:
                    try:
                        data = json.loads(message)
                        players = data.get("players", [])
                        for player in players:
                            pid = player.get("player_id")
                            if pid and pid != player_id:
                                other_players[pid] = [player["x"], player["y"]]
                        
                        if 'player_left' in data:
                            player_id_left = data['player_left']
                            if player_id_left in other_players:
                                del other_players[player_id_left]
                                print(f"Player {player_id_left} has left, removing from the game.")
                    except Exception as e:
                        print(f"Error in processing message: {e}")
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            await asyncio.sleep(5)  # Wait for 5 seconds before trying to reconnect

# Start websocket in background thread
def start_ws():
    asyncio.run(websocket_handler())

threading.Thread(target=start_ws, daemon=True).start()

# Coroutine to send data
async def async_send_position():
    global last_send_time
    current_time = time.time()
    
    if current_time - last_send_time >= 0.035:  
        try:
            position_data = {
                "player_id": player_id,
                "x": player_pos[0],
                "y": player_pos[1],
            }
            await ws.send(json.dumps(position_data))
            last_send_time = current_time
        except Exception as e:
            print("Send error:", e)

# Safe way to trigger send from main thread
def send_position():
    if ws and ws_loop:
        ws_loop.call_soon_threadsafe(asyncio.create_task, async_send_position())

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    moved = False
    if keys[pygame.K_LEFT]:
        player_pos[0] -= 5
        moved = True
    if keys[pygame.K_RIGHT]:
        player_pos[0] += 5
        moved = True
    if keys[pygame.K_UP]:
        player_pos[1] -= 5
        moved = True
    if keys[pygame.K_DOWN]:
        player_pos[1] += 5
        moved = True

    # Enforce boundary limits
    player_pos[0] = max(0, min(player_pos[0], 500 - player_size))
    player_pos[1] = max(0, min(player_pos[1], 500 - player_size))

    if moved:
        send_position()

    screen.fill((0, 0, 0))

    # Draw local player
    pygame.draw.rect(screen, player_color, (*player_pos, player_size, player_size))
    text = font.render(player_id, True, (255, 255, 255))
    screen.blit(text, (player_pos[0], player_pos[1] - 20))

    # Draw other players
    for pid, pos in other_players.items():
        pygame.draw.rect(screen, (255, 0, 0), (*pos, player_size, player_size))
        text = font.render(pid, True, (255, 255, 255))
        screen.blit(text, (pos[0], pos[1] - 20))

    pygame.display.flip()
    clock.tick(60)
