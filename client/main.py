import pygame
import asyncio
import sys
import threading
import random
from utils import *
from networking import WebSocketClient
from camera import Camera
from map import GameMap
from player import Player
from firing import FiringManager
from sound import SoundManager
import time
from overlay import draw_overlay
#from menu import InputBox, Button

# Initialize Pygame
pygame.init()
pygame.mouse.set_visible(False)

# game_state = "menu"
# name_input = InputBox(300, 200, 200, 40)
# lobby_input = InputBox(300, 260, 200, 40)
# selected_lobby = None
# player_name = None

# def start_game():
#     global game_state, selected_lobby, player_name
#     player_name = name_input.get_text()
#     selected_lobby = lobby_input.get_text()
#     if player_name and selected_lobby:
#         game_state = "playing"

# host_button = Button(300, 320, 90, 40, "Host", start_game)
# join_button = Button(410, 320, 90, 40, "Join", start_game)

# Set up the game screen
# screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
# pygame.display.set_caption("2D Game First Draft")
FONT = pygame.font.SysFont(None, 20)



screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2D Game First Draft")


# Replace the quit_game function with this improved version
def quit_game():
    # Show cursor before quitting
    pygame.mouse.set_visible(True)
    client.stop()
    pygame.quit()
    sys.exit()


# Initialize the game map and camera
game_map = GameMap('map2.tmx', 'background-dark.jpg')
map_width = game_map.tmx_data.width * game_map.tmx_data.tilewidth
map_height = game_map.tmx_data.height * game_map.tmx_data.tileheight
camera = Camera(map_width, map_height)


heart_icon = pygame.image.load("assets/heart.png").convert_alpha()
bullet_icon = pygame.image.load("assets/bullet.png").convert_alpha()

heart_icon = pygame.transform.scale(heart_icon, (30, 30))  
bullet_icon = pygame.transform.scale(bullet_icon, (50, 30)) 



clock = pygame.time.Clock()

# Local player initialization
player_id = str(random.randint(1000, 9999))

spawn_points =  game_map.generate_spawn_points(num_regions_x=3, num_regions_y=3, points_per_region=1)
spawn_x, spawn_y = random.choice(spawn_points)
while game_map.check_collision(pygame.Rect(spawn_x, spawn_y, PLAYER_SIZE, PLAYER_SIZE)):
    spawn_x, spawn_y = random.choice(spawn_points)
    
player = Player(player_id, spawn_x, spawn_y, LOCAL_PLAYER_COLOR, camera)
sound_manager = SoundManager()
player.firing_manager = FiringManager(player, camera, game_map, sound_manager)

# Dictionary to hold other players
other_players = {}

# Networking setup
client = WebSocketClient("ws://127.0.0.1:8000/ws/game/", player, other_players, camera, game_map)#,lobby_id=selected_lobby)
client.start()  # Start the event loop
all_players = [player] + list(other_players.values())
# Game loop
while True:
    # if game_state != "playing":
    #     screen.fill((30, 30, 30))
    #     title = FONT.render("Enter Player Name and Lobby ID", True, (255, 255, 255))
    #     screen.blit(title, (250, 150))
    #     name_input.draw(screen)
    #     lobby_input.draw(screen)
    #     host_button.draw(screen)
    #     join_button.draw(screen)

    #     for event in pygame.event.get():
    #         if event.type == pygame.QUIT:
    #             pygame.quit()
    #             sys.exit()
    #         name_input.handle_event(event)
    #         lobby_input.handle_event(event)
    #         host_button.handle_event(event)
    #         join_button.handle_event(event)

    #     pygame.display.flip()
    #     clock.tick(30)
    #     continue  # skip game loop until ready

    for event in pygame.event.get():
        if event.type == pygame.QUIT: 
            quit_game()  
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  
                quit_game()

    keys = pygame.key.get_pressed()
    dx, dy = 0, 0
    moved = False
    player.handle_firing_input(keys)
    
    # Support both arrow keys and WASD
    up = keys[pygame.K_UP] or keys[pygame.K_w]
    down = keys[pygame.K_DOWN] or keys[pygame.K_s]
    left = keys[pygame.K_LEFT] or keys[pygame.K_a]
    right = keys[pygame.K_RIGHT] or keys[pygame.K_d]

    is_flying_now = up and (left or right)

    player.is_flying = up

    if getattr(player, "was_flying", False) and not is_flying_now:
        player.inertia_active = True
        player.inertia_velocity_x = player.velocity_x
    player.was_flying = is_flying_now

    if is_flying_now:
        if left:
            player.velocity_x = max(player.velocity_x - PLAYER_ACCELERATION, -PLAYER_SPEED)
            player.facing_left = True
        elif right:
            player.velocity_x = min(player.velocity_x + PLAYER_ACCELERATION, PLAYER_SPEED)
            player.facing_left = False
        player.inertia_active = False
    elif left:
        player.velocity_x = max(player.velocity_x - PLAYER_ACCELERATION, -PLAYER_SPEED)
        player.facing_left = True
        player.inertia_active = False
    elif right:
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

    player.is_running = left or right

    dx = player.velocity_x
    player.velocity_y += GRAVITY

    if up:
        player.velocity_y = -JETPACK_FORCE
        if player.is_local:  # Call sound manager only for local player
            player.sound_manager.fade_in()
    if down:
        player.velocity_y += 0.1 * PLAYER_SPEED

    dy = player.velocity_y

    # --- Axis-aligned collision ---
    player_rect_x = pygame.Rect(player.x + dx, player.y, PLAYER_SIZE, PLAYER_SIZE)
    if not game_map.check_collision(player_rect_x):
        player.x += dx
        moved = True
    else:
        player.velocity_x = 0

    player_rect_y = pygame.Rect(player.x, player.y + dy, PLAYER_SIZE, PLAYER_SIZE)
    if not game_map.check_collision(player_rect_y):
        player.y += dy
        moved = True
        player.on_ground = False
    else:
        if player.velocity_y > 0:
            player.on_ground = True
        player.velocity_y = 0

    if moved:
        client.send_from_main_thread()

    player.x = max(0, min(player.x, map_width - PLAYER_SIZE))
    player.y = max(0, min(player.y, map_height - PLAYER_SIZE))

    if player.velocity_y == 0 and not game_map.check_collision(pygame.Rect(player.x, player.y + 1, PLAYER_SIZE, PLAYER_SIZE)):
        player.on_ground = False
    else:
        player.on_ground = True

    camera.update(player_rect_x)

    # --- Drawing ---
    # bg_offset = (camera.camera.left // 3, camera.camera.top // 3)
    # screen.blit(game_map.background, (-bg_offset[0], -bg_offset[1]))
    screen.fill((0,0, 0))
    game_map.draw_background(screen, camera)

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

    # Update and draw local player
    

    for player in all_players:
        if player.is_dead and player.death_time:
            print(f"Player {player.id} is respawning......")
            if time.time() - player.death_time > 4:
                spawn_x, spawn_y = random.choice(spawn_points)
                while game_map.check_collision(pygame.Rect(spawn_x, spawn_y, PLAYER_SIZE, PLAYER_SIZE)):
                    spawn_x, spawn_y = random.choice(spawn_points)
                player.respawn(spawn_x, spawn_y)
                player.firing_manager.reset_ammo()
    remote_players = other_players.values()
    # Draw and update all players
    for player in all_players:
        if player.is_dead :
            continue  

        player.draw(screen, camera)
        if player.is_local:
            player.update(keys, clock.get_time() / 1000)
            local_player_pos = (player.x, player.y)  
        player.update_bullets(remote_players)
        player.draw_bullets(screen)
        
    draw_overlay(screen, player, bullet_icon, heart_icon) 
    

    
      
    # Update and draw remote players
    for remote_player in other_players.values():
        if remote_player.is_dead:
            continue
        
        remote_player.update(
            is_flying=remote_player.is_flying,
            is_running=remote_player.is_running,
            facing_left=remote_player.facing_left,
            health=remote_player.health,
            is_dead=remote_player.is_dead,
            delta_time=clock.get_time() / 1000
        )
        remote_player.draw(screen, camera)
        remote_player.update_bullets(local_player_pos,all_players)
        remote_player.draw_bullets(screen, camera)
    
    pygame.display.flip()
    clock.tick(60)
