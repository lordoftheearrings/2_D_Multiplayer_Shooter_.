import pygame
from animation import Animation
from sound import SoundManager
from utils import *  
from firing import Bullet,FiringManager
import time 

class Player:
    def __init__(self, player_id, x, y, color, camera, is_local=True):
        self.id = player_id
        self.x = x
        self.y = y
        self.color = color
        self.is_local = is_local
        self.health = 100 
        self.is_dead = False
        self.death_time = None
        self.camera = camera 
        self.bullets = []
        self.rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)

        # Local and remote animations
        if is_local:
            self.animations = {
                "idle": Animation("assets/player/idleone.png", 0.1, scale=1.4),
                "run": Animation(["assets/player/runone.png", "assets/player/runtwo.png"], 0.2, scale=1.4),
                "fly": Animation("assets/player/flyone.png", 0.1, scale=1.4),
                "dead": Animation(["assets/player/death1.png", "assets/player/death2.png"], 0.1, scale=1.4),
            }
        else:
            self.animations = {
                "idle": Animation("assets/player/enemyidle.png", 1, scale=1.5),
                "run": Animation(["assets/player/enemyrunone.png", "assets/player/enemyruntwo.png"], 0.2, scale=1.5),
                "fly": Animation("assets/player/enemyfly.png", 1, scale=1.5),
                "dead": Animation(["assets/player/enemydeath1.png", "assets/player/enemydeath2.png"], 0.1, scale=1.4),
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

        self.sound_manager = SoundManager() if self.is_local else None
        self.firing_manager = FiringManager(self, camera) if is_local else None

    def update(self, keys=None, delta_time=None, is_flying=None, is_running=None,is_dead =False, facing_left=None):
        if self.is_local:
            # Update animation based on input
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.current_animation = "fly"
                self.sound_manager.fade_in()
            elif keys[pygame.K_LEFT] or keys[pygame.K_RIGHT] or keys[pygame.K_a] or keys[pygame.K_d]:
                self.current_animation = "run"
            else:
                self.current_animation = "idle"
                self.sound_manager.fade_out()
        else:
            # Update animation based on received state
            if is_flying:
                self.current_animation = "fly"
            elif is_running:
                self.current_animation = "run"
            elif is_dead:
                self.current_animation = "dead"
            else:
                self.current_animation = "idle"
            self.facing_left = facing_left
        
        # Update animation frames
        if delta_time is not None:
            self.animations[self.current_animation].update(delta_time)
        
        

    def draw(self, screen, camera):
        if self.is_dead:
            return
        frame = self.animations[self.current_animation].get_frame()
        player_rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)
        camera_applied_rect = camera.apply(player_rect)

        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)

        screen.blit(frame, camera_applied_rect.topleft)

        # Draw player ID above
        font = pygame.font.SysFont(None, 20)
        id_text = font.render(self.id, True, (255, 255, 255))  # Black text
        id_rect = id_text.get_rect(center=(camera_applied_rect.centerx, camera_applied_rect.top - 15))
        screen.blit(id_text, id_rect)

        # Draw health bar below ID
        bar_x = camera_applied_rect.centerx - HEALTH_BAR_WIDTH // 2
        bar_y = camera_applied_rect.top - 7

        # Outline (black border)
        pygame.draw.rect(screen, (255, 255, 255), (bar_x - 1, bar_y - 1, HEALTH_BAR_WIDTH + 2, HEALTH_BAR_HEIGHT + 2))

        # Fill color based on local/enemy
        fill_color = (0, 255, 0) if self.is_local else (255, 0, 0)  # Green for local, Red for enemy
        fill_width = int((self.health / 100) * HEALTH_BAR_WIDTH)
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, HEALTH_BAR_HEIGHT))

    def update_position(self, x, y):
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y
    
    
    def respawn(self, spawn_x, spawn_y):
        self.x = spawn_x
        self.y = spawn_y
        self.rect.x = spawn_x
        self.rect.y = spawn_y
        self.health = 100
        self.is_dead = False
        self.death_time = None  
        print(f"Player {self.id} respawned at ({self.x}, {self.y})")

    def handle_firing_input(self,keys):
        if self.is_local and self.firing_manager:
            self.firing_manager.handle_input(keys)

    def update_bullets(self,remote_players):
        if self.is_local and self.firing_manager:
            self.firing_manager.update(remote_players)

    def draw_bullets(self, screen):
        if self.is_local and self.firing_manager:
            self.firing_manager.draw(self, screen, self.firing_manager.camera)
            
        
class RemotePlayer(Player):
    def __init__(self, id, x, y, color, camera, game_map=None):
        super().__init__(id, x, y, color, camera, is_local=False)
        self.remote_bullets = []
        self.health = 100 
        self.game_map = game_map
        # Setting the animations similar to the Player class
        self.animations = {
            "idle": Animation("assets/player/enemyidle.png", 1, scale=1.5),
            "run": Animation(["assets/player/enemyrunone.png", "assets/player/enemyrunthree.png"], 0.2, scale=1.5),
            "fly": Animation("assets/player/enemyfly.png", 1, scale=1.5),
            "dead": Animation(["assets/player/enemydeath1.png", "assets/player/enemydeath2.png"], 0.1, scale=1.4),

        }
        self.current_animation = "idle"  # Default to idle animation
        self.facing_left = False  # Default to not facing left
        self.is_flying = False
        self.is_running = False
        self.camera = camera
        self.is_dead = False

    def update(self, is_flying, is_running, facing_left, health,is_dead = False, delta_time=None):
        if delta_time is not None:
            # Update animation for remote player based on time elapsed
            self.animations[self.current_animation].update(delta_time)

        # Update the flags for animation states
        self.is_flying = is_flying
        self.is_running = is_running
        self.facing_left = facing_left
        self.health = health 
        self.is_dead = is_dead

        # Handle animation based on movement states
        if self.is_flying:
            self.current_animation = "fly"
        elif self.is_running:
            self.current_animation = "run"
        elif self.is_dead:
            self.current_animation = "dead"
        else:
            self.current_animation = "idle"

    def spawn_remote_bullet(self, spawn_x, spawn_y, angle):
        new_bullet = Bullet(spawn_x, spawn_y, angle, self.game_map)
        self.remote_bullets.append(new_bullet)

    def update_bullets(self,local_player_pos,all_players):
        # Update existing bullets
        for bullet in self.remote_bullets[:]:
            bullet.update()
            
            for player in all_players:
                if player.id != self.id and not player.is_dead:  # Exclude self and dead players
                    player_rect = pygame.Rect(player.x, player.y, PLAYER_SIZE, PLAYER_SIZE)
                    if bullet.rect.colliderect(player_rect):  # Collision detected
                        player.health -= 5  
                        print(f"you are hit by {self.id}! Health: {player.health}")  

                        if player.health <= 0:
                            player.is_dead = True
                            player.death_time = time.time()
                            player.sound_manager.play_death_sound()
                            print(f"Player {player.id} is dead!")  

                        self.remote_bullets.remove(bullet) 
                        break
            sound_manager=SoundManager()
            sound_manager.update_remote_player_volume(local_player_pos,[self])
            sound_manager.play_bullet_sound_remote(self.id)
            if bullet.has_exceeded_range():
                if bullet in self.remote_bullets:
                    self.remote_bullets.remove(bullet)

    def draw_bullets(self, screen, camera):
        for bullet in self.remote_bullets:
            bullet.draw(screen, camera)

    def draw(self, screen, camera):
        frame = self.animations[self.current_animation].get_frame()
        player_rect = pygame.Rect(self.x, self.y, PLAYER_SIZE, PLAYER_SIZE)
        camera_applied_rect = camera.apply(player_rect)

        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)  # Flip sprite if facing left

        screen.blit(frame, camera_applied_rect.topleft)

        # Draw player ID above
        font = pygame.font.SysFont(None, 20)
        id_text = font.render(self.id, True, (255, 255, 255))  # Black text
        id_rect = id_text.get_rect(center=(camera_applied_rect.centerx, camera_applied_rect.top - 15))
        screen.blit(id_text, id_rect)

        # Draw health bar below ID
        bar_x = camera_applied_rect.centerx - HEALTH_BAR_WIDTH // 2
        bar_y = camera_applied_rect.top - 7

        # Outline (black border)
        pygame.draw.rect(screen, (255, 255, 255), (bar_x - 1, bar_y - 1, HEALTH_BAR_WIDTH + 2, HEALTH_BAR_HEIGHT + 2))

        # Fill color based on local/enemy
        fill_color = (0, 255, 0) if self.is_local else (255, 0, 0)  # Green for local, Red for enemy
        fill_width = int((self.health / 100) * HEALTH_BAR_WIDTH)
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, HEALTH_BAR_HEIGHT))
