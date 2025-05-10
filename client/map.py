# import pygame
# import os,random
# from pytmx.util_pygame import load_pygame
# from utils import *

# class GameMap:
#     def __init__(self, map_file, bg_image):
#         # Get the base path where the map and assets are located
#         base_path = os.path.dirname(os.path.abspath(__file__))

#         # Construct full paths
#         map_file_path = os.path.join(base_path, 'assets', map_file)
#         bg_image_path = os.path.join(base_path, 'assets', bg_image)

#         # Load map and background
#         self.tmx_data = load_pygame(map_file_path)
#         self.background = pygame.image.load(bg_image_path).convert()

#         # Fix tileset paths
#         self.set_tile_images(base_path)

#         # Load all collidable tiles into solid_rects
#         self.solid_rects = self.load_collision_rects()

#     def set_tile_images(self, base_path):
#         for tileset in self.tmx_data.tilesets:
#             # Case 1: Single tilesheet image (typical .tsx external tileset)
#             if hasattr(tileset, 'image') and tileset.image:
#                 image_path = tileset.image.source
#                 if not os.path.isabs(image_path):
#                     image_path = os.path.join(base_path, 'assets', image_path)
#                 try:
#                     tileset.image = pygame.image.load(image_path).convert_alpha()
#                 except FileNotFoundError:
#                     print(f"Tileset image not found: {image_path}")
#                     raise

#         # Case 2: Per-tile images (your newer embedded tileset)
#         if hasattr(tileset, 'tiles'):
#             for tile_id in tileset.tile_properties:
#                 tile = tileset.tiles.get(tile_id)
#                 if tile and tile.image:
#                     image_path = tile.image.source
#                     if not os.path.isabs(image_path):
#                         image_path = os.path.join(base_path, 'assets', image_path)
#                     try:
#                         tile.image = pygame.image.load(image_path).convert_alpha()
#                     except FileNotFoundError:
#                         print(f"Tile image not found: {image_path}")
#                         raise

#     def draw_background(self, screen):
#         screen.blit(self.background, (0, 0))

#     def draw_map(self, screen):
#         for layer in self.tmx_data.visible_layers:
#             if hasattr(layer, 'tiles'):
#                 for x, y, surf in layer.tiles():
#                     screen.blit(surf, (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight))

#     def load_collision_rects(self):
#         rects = []
#         for layer in self.tmx_data.visible_layers:
#             if hasattr(layer, 'tiles'): 
#                 for x, y, gid in layer:
#                     if gid == 0:
#                         continue
#                     tile_props = self.tmx_data.get_tile_properties_by_gid(gid)
#                     if tile_props and tile_props.get("collidable", False):
#                         rect = pygame.Rect(
#                             x * self.tmx_data.tilewidth,
#                             y * self.tmx_data.tileheight,
#                             self.tmx_data.tilewidth,
#                             self.tmx_data.tileheight
#                         )
#                         rects.append(rect)
#         return rects

#     def check_collision(self, player_rect):
#         return any(player_rect.colliderect(rect) for rect in self.solid_rects)

    
#     def generate_spawn_points(self, num_regions_x=3, num_regions_y=3, points_per_region=1):
#         spawn_points = []
#         region_width = self.tmx_data.width * self.tmx_data.tilewidth // num_regions_x
#         region_height = self.tmx_data.height * self.tmx_data.tileheight // num_regions_y

#         for region_x in range(num_regions_x):
#             for region_y in range(num_regions_y):
#                 for _ in range(points_per_region):
#                     # Generate a random point within the region
#                     spawn_x = random.randint(region_x * region_width, (region_x + 1) * region_width - PLAYER_SIZE)
#                     spawn_y = random.randint(region_y * region_height, (region_y + 1) * region_height - PLAYER_SIZE)

#                     # Check for collision
#                     while self.check_collision(pygame.Rect(spawn_x, spawn_y, PLAYER_SIZE, PLAYER_SIZE)):
#                         spawn_x = random.randint(region_x * region_width, (region_x + 1) * region_width - PLAYER_SIZE)
#                         spawn_y = random.randint(region_y * region_height, (region_y + 1) * region_height - PLAYER_SIZE)

#                     spawn_points.append((spawn_x, spawn_y))

#         return spawn_points


import pygame
import os, random
from pytmx.util_pygame import load_pygame
from utils import *

class GameMap:
    def __init__(self, map_file, bg_image):
        # Get the base path where the map and assets are located
        base_path = os.path.dirname(os.path.abspath(__file__))

        # Construct full paths
        map_file_path = os.path.join(base_path, 'assets', map_file)
        bg_image_path = os.path.join(base_path, 'assets', bg_image)

        self.tmx_data = load_pygame(map_file_path)
        
        # Load background directly - assuming image is already 5600x4200
        self.background = pygame.image.load(bg_image_path).convert()

        # Fix tileset paths
        self.set_tile_images(base_path)

        # Load all collidable tiles into solid_rects
        self.solid_rects = self.load_collision_rects()

    def set_tile_images(self, base_path):
        for tileset in self.tmx_data.tilesets:
            # Case 1: Single tilesheet image (typical .tsx external tileset)
            if hasattr(tileset, 'image') and tileset.image:
                image_path = tileset.image.source
                if not os.path.isabs(image_path):
                    image_path = os.path.join(base_path, 'assets', image_path)
                try:
                    tileset.image = pygame.image.load(image_path).convert_alpha()
                except FileNotFoundError:
                    print(f"Tileset image not found: {image_path}")
                    raise

        # Case 2: Per-tile images (your newer embedded tileset)
        if hasattr(tileset, 'tiles'):
            for tile_id in tileset.tile_properties:
                tile = tileset.tiles.get(tile_id)
                if tile and tile.image:
                    image_path = tile.image.source
                    if not os.path.isabs(image_path):
                        image_path = os.path.join(base_path, 'assets', image_path)
                    try:
                        tile.image = pygame.image.load(image_path).convert_alpha()
                    except FileNotFoundError:
                        print(f"Tile image not found: {image_path}")
                        raise

    def draw_background(self, screen, camera):
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Calculate map boundaries
        map_width = self.tmx_data.width * self.tmx_data.tilewidth
        map_height = self.tmx_data.height * self.tmx_data.tileheight
        
        # Get screen dimensions
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Calculate maximum camera bounds
        max_camera_x = max(0, map_width - screen_width)
        max_camera_y = max(0, map_height - screen_height)
        
        # Clamp camera position to map boundaries
        camera_x = max(0, min(camera.camera.x, max_camera_x))
        camera_y = max(0, min(camera.camera.y, max_camera_y))
        
        # Calculate source rectangle dimensions
        source_width = min(screen_width, map_width - camera_x)
        source_height = min(screen_height, map_height - camera_y)
        
        # Draw the visible portion with clamped coordinates
        screen.blit(
            self.background,
            (0, 0),  # Destination position
            (
                camera_x,
                camera_y,
                source_width,  # Use calculated dimensions
                source_height  # Use calculated dimensions
            )  # Source rectangle
        )
    def draw_map(self, screen):
        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, 'tiles'):
                for x, y, surf in layer.tiles():
                    screen.blit(surf, (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight))

    def load_collision_rects(self):
        rects = []
        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, 'tiles'): 
                for x, y, gid in layer:
                    if gid == 0:
                        continue
                    tile_props = self.tmx_data.get_tile_properties_by_gid(gid)
                    if tile_props and tile_props.get("collidable", False):
                        rect = pygame.Rect(
                            x * self.tmx_data.tilewidth,
                            y * self.tmx_data.tileheight,
                            self.tmx_data.tilewidth,
                            self.tmx_data.tileheight
                        )
                        rects.append(rect)
        return rects

    def check_collision(self, player_rect):
        return any(player_rect.colliderect(rect) for rect in self.solid_rects)

    def generate_spawn_points(self, num_regions_x=3, num_regions_y=3, points_per_region=1):
        spawn_points = []
        region_width = self.tmx_data.width * self.tmx_data.tilewidth // num_regions_x
        region_height = self.tmx_data.height * self.tmx_data.tileheight // num_regions_y

        for region_x in range(num_regions_x):
            for region_y in range(num_regions_y):
                for _ in range(points_per_region):
                    # Generate a random point within the region
                    spawn_x = random.randint(region_x * region_width, (region_x + 1) * region_width - PLAYER_SIZE)
                    spawn_y = random.randint(region_y * region_height, (region_y + 1) * region_height - PLAYER_SIZE)

                    # Check for collision
                    while self.check_collision(pygame.Rect(spawn_x, spawn_y, PLAYER_SIZE, PLAYER_SIZE)):
                        spawn_x = random.randint(region_x * region_width, (region_x + 1) * region_width - PLAYER_SIZE)
                        spawn_y = random.randint(region_y * region_height, (region_y + 1) * region_height - PLAYER_SIZE)

                    spawn_points.append((spawn_x, spawn_y))

        return spawn_points
