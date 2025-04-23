import pygame
from animation import Animation
from sound import SoundManager
from utils import *  # Assuming all constants (PLAYER_SIZE, etc.) are in utils.py

class Player:
    def __init__(self, player_id, x, y, color):
        self.id = player_id
        self.x = x
        self.y = y
        self.color = color
        self.rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)

        # Initialize animations for the player
        self.animations = {
            "idle": Animation("assets/player/Idle.png", 1, scale=1.5),
            "run": Animation(["assets/player/Run1.png", "assets/player/Run2.png"], 0.1, scale=1.5),  # Run animation with two images
            "fly": Animation("assets/player/Jump.png", 1, scale=1.5)  # Single frame for flying
        }

        self.current_animation = "idle"
        self.frame_index = 0
        self.facing_left = False  # Player facing direction
        self.inertia_active = False
        self.inertia_velocity_x = 0
        self.was_flying = False

        
        # Sound management
        self.sound_manager = SoundManager()

        # Player movement attributes
        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = False

    def update(self, keys, delta_time):
        # Handle animation change based on movement
        if keys[pygame.K_UP]:  # Jetpack (fly)
            self.current_animation = "fly"
            self.sound_manager.fade_in()
        elif keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:  # Run (horizontal movement)
            self.current_animation = "run"
        else:  # Idle (no movement)
            self.current_animation = "idle"
            self.sound_manager.fade_out()

        # Update animations
        self.animations[self.current_animation].update(delta_time)

    def draw(self, screen, camera):
        """Draws the player's current animation frame to the screen."""
        frame = self.animations[self.current_animation].get_frame(self.frame_index)
        
        # Adjust the player position based on camera offset
        player_rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)
        camera_applied_rect = camera.apply(player_rect)
        
        # Flip the player image if facing left
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)
        
        # Draw player frame
        screen.blit(frame, camera_applied_rect.topleft)
        
        # Draw the player's ID text
        font = pygame.font.SysFont(None, 24)
        text = font.render(self.id, True, (255, 255, 255))
        
        # Adjust the text position based on the camera's applied coordinates
        screen.blit(text, camera.apply(player_rect).move(0, -20))

    def update_position(self, x, y):
        """Updates the player's position manually."""
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y
