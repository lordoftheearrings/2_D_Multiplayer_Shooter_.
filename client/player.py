import pygame
from animation import Animation
from sound import SoundManager
from utils import *  # Includes PLAYER_SIZE, HEALTH_BAR_WIDTH, etc.

class Player:
    def __init__(self, player_id, x, y, color, is_local=True):
        self.id = player_id
        self.x = x
        self.y = y
        self.color = color
        self.is_local = is_local
        self.health = 100  # Health from 0 to 100

        self.rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)

        # Local and remote animations
        if is_local:
            self.animations = {
                "idle": Animation("assets/player/idleone.png", 1, scale=1.5),
                "run": Animation(["assets/player/runone.png", "assets/player/runtwo.png"], 0.1, scale=1.5),
                "fly": Animation("assets/player/flyone.png", 1, scale=1.5),
            }
        else:
            self.animations = {
                "idle": Animation("assets/player/enemyidle.png", 1, scale=1.5),
                "run": Animation(["assets/player/enemyrunone.png", "assets/player/enemyruntwo.png"], 0.1, scale=1.5),
                "fly": Animation("assets/player/enemyfly.png", 1, scale=1.5),
            }

        self.current_animation = "idle"
        self.frame_index = 0
        self.facing_left = False
        self.inertia_active = False
        self.inertia_velocity_x = 0
        self.was_flying = False
        self.is_flying = False
        self.is_running = False

        self.velocity_x = 0
        self.velocity_y = 0
        self.on_ground = False

        # Only local player needs sounds
        self.sound_manager = SoundManager() if self.is_local else None

    def update(self, keys, delta_time):
        if self.is_local:
            # Update animation based on input
            if keys[pygame.K_UP]:
                self.current_animation = "fly"
                self.sound_manager.fade_in()
            elif keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
                self.current_animation = "run"
            else:
                self.current_animation = "idle"
                self.sound_manager.fade_out()

        # Update animation frames
        self.animations[self.current_animation].update(delta_time)

    def draw(self, screen, camera):
        frame = self.animations[self.current_animation].get_frame()
        player_rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)
        camera_applied_rect = camera.apply(player_rect)

        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)

        screen.blit(frame, camera_applied_rect.topleft)

        # Draw player ID above
        font = pygame.font.SysFont(None, 20)
        id_text = font.render(self.id, True, (0, 0, 0))  # Black text
        id_rect = id_text.get_rect(center=(camera_applied_rect.centerx, camera_applied_rect.top - 15))
        screen.blit(id_text, id_rect)

        # Draw health bar below ID
        bar_x = camera_applied_rect.centerx - HEALTH_BAR_WIDTH // 2
        bar_y = camera_applied_rect.top - 7

        # Outline (black border)
        pygame.draw.rect(screen, (0, 0, 0), (bar_x - 1, bar_y - 1, HEALTH_BAR_WIDTH + 2, HEALTH_BAR_HEIGHT + 2))

        # Fill color based on local/enemy
        fill_color = (0, 255, 0) if self.is_local else (255, 0, 0)  # Green for local, Red for enemy
        fill_width = int((self.health / 100) * HEALTH_BAR_WIDTH)
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, HEALTH_BAR_HEIGHT))

    def update_position(self, x, y):
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y
        
class RemotePlayer(Player):
    def __init__(self, id, x, y, color):
        super().__init__(id, x, y, color, is_local=False)  # Set is_local to False for remote players
        self.health = 100  # Initial health for remote players

        # Setting the animations similar to the Player class
        self.animations = {
            "idle": Animation("assets/player/enemyidle.png", 1, scale=1.5),
            "run": Animation(["assets/player/enemyrunone.png", "assets/player/enemyruntwo.png"], 0.1, scale=1.5),
            "fly": Animation("assets/player/enemyfly.png", 1, scale=1.5),
        }
        self.current_animation = "idle"  # Default to idle animation
        self.facing_left = False  # Default to not facing left

        # New flags for animation states
        self.is_flying = False
        self.is_running = False

    def update(self, is_flying, is_running, facing_left, health, delta_time=None):
        if delta_time is not None:
            # Update animation for remote player based on time elapsed
            self.animations[self.current_animation].update(delta_time)

        # Update the flags for animation states
        self.is_flying = is_flying
        self.is_running = is_running
        self.facing_left = facing_left
        self.health = health  # Update health as well

        # Handle animation based on movement states
        if self.is_flying:
            self.current_animation = "fly"
        elif self.is_running:
            self.current_animation = "run"
        else:
            self.current_animation = "idle"

    def draw(self, screen, camera):
        frame = self.animations[self.current_animation].get_frame()
        player_rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)
        camera_applied_rect = camera.apply(player_rect)

        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)  # Flip sprite if facing left

        screen.blit(frame, camera_applied_rect.topleft)

        # Draw player ID above
        font = pygame.font.SysFont(None, 20)
        id_text = font.render(self.id, True, (0, 0, 0))  # Black text
        id_rect = id_text.get_rect(center=(camera_applied_rect.centerx, camera_applied_rect.top - 15))
        screen.blit(id_text, id_rect)

        # Draw health bar below ID
        bar_x = camera_applied_rect.centerx - HEALTH_BAR_WIDTH // 2
        bar_y = camera_applied_rect.top - 7

        # Outline (black border)
        pygame.draw.rect(screen, (0, 0, 0), (bar_x - 1, bar_y - 1, HEALTH_BAR_WIDTH + 2, HEALTH_BAR_HEIGHT + 2))

        # Fill color based on local/enemy
        fill_color = (0, 255, 0) if self.is_local else (255, 0, 0)  # Green for local, Red for enemy
        fill_width = int((self.health / 100) * HEALTH_BAR_WIDTH)
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, HEALTH_BAR_HEIGHT))
