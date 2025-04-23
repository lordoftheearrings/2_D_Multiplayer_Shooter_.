# camera.py
import pygame
from utils import *

class Camera:
    def __init__(self, map_width, map_height):
        self.camera = pygame.Rect(0, 0, map_width, map_height)
        self.map_width = map_width
        self.map_height = map_height

    def apply(self, target_rect):
        # Return the rect relative to the camera view
        return target_rect.move(-self.camera.left, -self.camera.top)

    def update(self, target_rect):
        # Center the camera on the player
        x = target_rect.centerx - SCREEN_WIDTH // 2
        y = target_rect.centery - SCREEN_HEIGHT // 2

        # Clamp so camera doesn’t go outside the map
        x = max(0, min(x, self.map_width - SCREEN_WIDTH))
        y = max(0, min(y, self.map_height - SCREEN_HEIGHT))

        self.camera = pygame.Rect(x, y, SCREEN_WIDTH, SCREEN_HEIGHT)
