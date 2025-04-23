import pygame
import asyncio
import sys
import threading
import random
from player import Player
from networking import WebSocketClient
from utils import *
from camera import Camera
from map import GameMap

# Initialize Pygame
pygame.init()

# Set up the game screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mini Militia PC")
FONT = pygame.font.SysFont(None, 20)

# Initialize the game map and camera
game_map = GameMap('map.tmx', 'background.jpg')
map_width = game_map.tmx_data.width * game_map.tmx_data.tilewidth
map_height = game_map.tmx_data.height * game_map.tmx_data.tileheight
camera = Camera(map_width, map_height)

clock = pygame.time.Clock()

# Local player initialization with gravity and jetpack properties
player_id = str(random.randint(1000, 9999))

# Find a spawn location not in collision
spawn_x, spawn_y = random.randint(50, 450), random.randint(50, 450)
while game_map.check_collision(pygame.Rect(spawn_x, spawn_y, PLAYER_SIZE, PLAYER_SIZE)):
    spawn_x, spawn_y = random.randint(50, 450), random.randint(50, 450)

player = Player(player_id, spawn_x, spawn_y, LOCAL_PLAYER_COLOR)
player.velocity_y = 0  # Initial vertical velocity
player.velocity_x = 0  # Initial horizontal velocity
player.on_ground = False

# Dictionary to hold other players
other_players = {}

# Networking setup
client = WebSocketClient("ws://127.0.0.1:8000/ws/game/", player, other_players)
threading.Thread(target=lambda: asyncio.run(client.connect()), daemon=True).start()

# Game loop
while True:
    # Handle Pygame events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    dx, dy = 0, 0
    moved = False

    # Track if player is flying this frame
    is_flying_now = keys[pygame.K_UP] and (keys[pygame.K_LEFT] or keys[pygame.K_RIGHT])

    # Trigger inertia only when releasing from flight
    if getattr(player, "was_flying", False) and not is_flying_now:
        player.inertia_active = True
        player.inertia_velocity_x = player.velocity_x
    player.was_flying = is_flying_now

    # Handle horizontal movement
    if is_flying_now:
        if keys[pygame.K_LEFT]:
            player.velocity_x = max(player.velocity_x - PLAYER_ACCELERATION, -PLAYER_SPEED)
            player.facing_left = True
        elif keys[pygame.K_RIGHT]:
            player.velocity_x = min(player.velocity_x + PLAYER_ACCELERATION, PLAYER_SPEED)
            player.facing_left = False
        player.inertia_active = False
    elif keys[pygame.K_LEFT]:
        player.velocity_x = max(player.velocity_x - PLAYER_ACCELERATION, -PLAYER_SPEED)
        player.facing_left = True
        player.inertia_active = False
    elif keys[pygame.K_RIGHT]:
        player.velocity_x = min(player.velocity_x + PLAYER_ACCELERATION, PLAYER_SPEED)
        player.facing_left = False
        player.inertia_active = False
    elif player.inertia_active:
        player.inertia_velocity_x *= (1 - INERTIA_DECAY)
        player.velocity_x = player.inertia_velocity_x
        if abs(player.velocity_x) < 0.1:
            player.velocity_x = 0
            player.inertia_active = False
    else:
        player.velocity_x *= (1 - INERTIA_DECAY)
        if abs(player.velocity_x) < 0.1:
            player.velocity_x = 0

    dx = player.velocity_x

    # Gravity
    player.velocity_y += GRAVITY
    # Jetpack
    if keys[pygame.K_UP]:
        player.velocity_y = -JETPACK_FORCE

    # Down
    if keys[pygame.K_DOWN]:
        player.velocity_y += 0.1*PLAYER_SPEED

    dy = player.velocity_y

    # --- Improved axis-wise collision detection ---

    # Check horizontal (X-axis)
    player_rect_x = pygame.Rect(player.x + dx, player.y, PLAYER_SIZE, PLAYER_SIZE)
    if not game_map.check_collision(player_rect_x):
        player.x += dx
        moved = True
    else:
        player.velocity_x = 0

    # Check vertical (Y-axis)
    player_rect_y = pygame.Rect(player.x, player.y + dy, PLAYER_SIZE, PLAYER_SIZE)
    if not game_map.check_collision(player_rect_y):
        player.y += dy
        moved = True
        player.on_ground = False
    else:
        if player.velocity_y > 0:  # Only set on_ground if falling down
            player.on_ground = True
        player.velocity_y = 0


    # # Check if on ground
    # if player.velocity_y == 0 and not game_map.check_collision(pygame.Rect(player.x, player.y + 1, PLAYER_SIZE, PLAYER_SIZE)):
    #     player.on_ground = False
    # else:
    #     player.on_ground = True

    if moved:
        client.send_from_main_thread()


    # Clamp player position to stay within the bounds of the map
    player.x = max(0, min(player.x, map_width - PLAYER_SIZE))
    player.y = max(0, min(player.y, map_height - PLAYER_SIZE))

    # Update the player's on-ground status (checking collision below)
    if player.velocity_y == 0 and not game_map.check_collision(pygame.Rect(player.x, player.y + 1, PLAYER_SIZE, PLAYER_SIZE)):
        player.on_ground = False
    else:
        player.on_ground = True

    # Update the camera
    camera.update(player_rect_x)

    # Draw the background with parallax effect
    bg_offset = (camera.camera.left // 3, camera.camera.top // 3)
    screen.blit(game_map.background, (-bg_offset[0], -bg_offset[1]))

    # Draw the game map layers
    for layer in game_map.tmx_data.visible_layers:
        if hasattr(layer, 'tiles'):
            for x, y, tile_surface in layer.tiles():
                tile_rect = pygame.Rect(
                    x * game_map.tmx_data.tilewidth,
                    y * game_map.tmx_data.tileheight,
                    game_map.tmx_data.tilewidth,
                    game_map.tmx_data.tileheight
                )
                screen.blit(tile_surface, camera.apply(tile_rect))

    # Update and draw the local player using the Player class methods
    player.update(keys, clock.get_time() / 1000)  # Pass delta time for animation updates
    player.draw(screen, camera)  # Pass the camera for proper drawing

    # Draw other players (remote players)
    for pid, pos in other_players.items():
        remote_rect = pygame.Rect(pos[0], pos[1], PLAYER_SIZE, PLAYER_SIZE)
        camera_applied_rect = camera.apply(remote_rect)
        pygame.draw.rect(screen, REMOTE_PLAYER_COLOR, camera_applied_rect)
        name_surf = FONT.render(pid, True, (255, 255, 255))
        screen.blit(name_surf, camera_applied_rect.move(0, -20))

    # Update the screen and control the frame rate
    pygame.display.flip()
    clock.tick(60)
