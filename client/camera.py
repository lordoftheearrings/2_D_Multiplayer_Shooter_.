# camera.py
import pygame
from utils import *

class Camera:
    def __init__(self, map_width, map_height):
        self.map_width = map_width
        self.map_height = map_height
        # Get actual screen dimensions when camera is created
        self.screen_width = pygame.display.get_surface().get_width()
        self.screen_height = pygame.display.get_surface().get_height()
        self.camera = pygame.Rect(0, 0, map_width, map_height)

    def apply(self, target_rect):
        # Return the rect relative to the camera view
        return target_rect.move(-self.camera.left, -self.camera.top)

    def update(self, target_rect):
        # Center the camera on the player using actual screen dimensions
        x = target_rect.centerx - self.screen_width // 2
        y = target_rect.centery - self.screen_height // 2

        # Clamp using actual screen dimensions
        x = max(0, min(x, self.map_width - self.screen_width))
        y = max(0, min(y, self.map_height - self.screen_height))

        self.camera = pygame.Rect(x, y, self.screen_width, self.screen_height)
