import pygame
import math

BULLET_SPEED = 20
BULLET_RADIUS = 3
BULLET_MAX_DISTANCE = 400  # Maximum bullet travel distance

class Bullet:
    def __init__(self, x, y, angle, game_map=None):
        self.x = x
        self.y = y
        self.spawn_x = x  # Track the starting point for max distance
        self.spawn_y = y
        self.angle = angle
        self.speed = BULLET_SPEED
        self.rect = pygame.Rect(self.x, self.y, BULLET_RADIUS * 2, BULLET_RADIUS * 2)
        self.image = pygame.image.load('assets/bullet.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (20, 20))
        self.game_map = game_map
        self.destroyed = False

    def update(self):   
        if self.destroyed:
            return

        # Move bullet according to its angle and speed
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        self.rect.x = int(self.x)   
        self.rect.y = int(self.y)

        # Check for map collision if game_map is provided
        if self.game_map and self.game_map.check_collision(self.rect):
            self.destroyed = True

    def has_exceeded_range(self):
        if self.destroyed:
            return True
        # Check if the bullet has exceeded max distance
        distance_traveled = math.hypot(self.x - self.spawn_x, self.y - self.spawn_y)
        return distance_traveled > BULLET_MAX_DISTANCE

    def draw(self, screen, camera):
        if self.destroyed:
            return
        # Rotate bullet image according to angle
        bullet_rotated = pygame.transform.rotate(self.image, -math.degrees(self.angle))
        rect = bullet_rotated.get_rect(center=camera.apply(self.rect).center)
        screen.blit(bullet_rotated, rect)


class FiringManager:
    def __init__(self, player, camera, game_map=None):
        self.player = player
        self.camera = camera
        self.game_map = game_map
        self.bullets = []
        self.new_bullets = []
        self.shoot_cooldown = 100
        self.last_shot_time = 0

    def handle_input(self):
        mouse_pressed = pygame.mouse.get_pressed()
        now = pygame.time.get_ticks()
        if mouse_pressed[0]:  # Left click
            if now - self.last_shot_time > self.shoot_cooldown:
                self.last_shot_time = now
                self.fire_bullet()

    def fire_bullet(self):
        # --- 1) Player center in world coords ---
        px = self.player.x + self.player.rect.width // 2
        py = self.player.y + self.player.rect.height // 2

        # --- 2) Mouse (screen) → world ---
        mx, my = pygame.mouse.get_pos()

        # Adjust mouse position based on camera offset to get world coordinates
        wx = mx + self.camera.camera.left
        wy = my + self.camera.camera.top

        # --- 3) Calculate the angle between player and mouse (world to world) ---
        angle = math.atan2(wy - py, wx - px)

        # --- 4) Spawn point on the exact same offset as your line ---
        LINE_OFFSET = 10
        sx = px + LINE_OFFSET * math.cos(angle)
        sy = py + LINE_OFFSET * math.sin(angle)

        # Create new bullet with game_map reference
        new_bullet = Bullet(sx, sy, angle, self.game_map)
        self.bullets.append(new_bullet)
        self.new_bullets.append(new_bullet)

    def update(self):
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.has_exceeded_range() or bullet.destroyed:
                self.bullets.remove(bullet)

    def draw_dotted_line(self, surface, color, start_pos, end_pos, width=3, dash_length=20):
        x1, y1 = start_pos
        x2, y2 = end_pos
        dl = math.hypot(x2 - x1, y2 - y1)
        if dl == 0:
            return

        dx = (x2 - x1) / dl
        dy = (y2 - y1) / dl

        for i in range(0, int(dl / dash_length), 2):
            start = (x1 + dx * i * dash_length, y1 + dy * i * dash_length)
            end = (x1 + dx * (i + 1) * dash_length, y1 + dy * (i + 1) * dash_length)
            pygame.draw.line(surface, color, start, end, width)

    def draw_aim_line(self, screen, camera):
        world_rect = pygame.Rect(self.player.x, self.player.y,
                                 self.player.rect.width,
                                 self.player.rect.height)
        px, py = camera.apply(world_rect).center

        mx, my = pygame.mouse.get_pos() 

        dx = mx - px
        dy = my - py
        angle = math.atan2(dy, dx)

        offset_distance = 80
        start_x = px + offset_distance * math.cos(angle)
        start_y = py + offset_distance * math.sin(angle)

        end_x = start_x + (BULLET_MAX_DISTANCE-200) * math.cos(angle)
        end_y = start_y + (BULLET_MAX_DISTANCE-200) * math.sin(angle)

        self.draw_dotted_line(
            screen,
            (0, 0, 0),                
            (start_x, start_y),
            (end_x, end_y),
            width=3,
            dash_length=20
        )

    def draw(self, player, screen, camera):
        self.draw_aim_line(screen, camera)
        for bullet in self.bullets:
            bullet.draw(screen, camera)
