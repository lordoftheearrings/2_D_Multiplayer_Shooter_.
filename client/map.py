import pygame
import os,random
from pytmx.util_pygame import load_pygame
from utils import *

class GameMap:
    def __init__(self, map_file, bg_image):
        # Get the base path where the map and assets are located
        base_path = os.path.dirname(os.path.abspath(__file__))

        # Construct full paths
        map_file_path = os.path.join(base_path, 'assets', map_file)
        bg_image_path = os.path.join(base_path, 'assets', bg_image)

        # Load map and background
        self.tmx_data = load_pygame(map_file_path)
        self.background = pygame.image.load(bg_image_path).convert()

        # Fix tileset paths
        self.set_tile_images(base_path)

        # Load all collidable tiles into solid_rects
        self.solid_rects = self.load_collision_rects()

    def set_tile_images(self, base_path):
        """Fix the paths for all tileset images."""
        for ts in self.tmx_data.tilesets:
            if hasattr(ts, 'source'):
                image_path = ts.source
                if not image_path.startswith('assets'):
                    image_path = os.path.join('assets', image_path)
                image_path = os.path.join(base_path, image_path)
                try:
                    ts.image = pygame.image.load(image_path).convert()
                except FileNotFoundError:
                    print(f"Tileset image not found: {image_path}")
                    raise

    def draw_background(self, screen):
        screen.blit(self.background, (0, 0))

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