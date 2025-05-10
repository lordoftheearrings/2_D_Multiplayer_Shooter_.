import pygame

def draw_overlay(screen, player, bullet_icon, heart_icon):
    # === Health bar ===
    screen.blit(heart_icon, (10, 10))  
    health_bar_x = 50
    health_bar_y = 15
    health_bar_width = 200
    health_bar_height = 20

    # Draw health bar outline
    pygame.draw.rect(screen, (255, 255, 255), (health_bar_x - 1, health_bar_y - 1, health_bar_width + 2, health_bar_height + 2))

    # Draw health bar fill
    health_fill_width = int((player.health / 100) * health_bar_width)
    pygame.draw.rect(screen, (200, 100, 150), (health_bar_x, health_bar_y, health_fill_width, health_bar_height))  # Custom pinkish-red

    # === Bullet info (top-right corner) ===
    screen_width = screen.get_width()
    bullet_icon_x = screen_width - 170
    bullet_icon_y = 10

    # Translucent background box
    box_width = 170
    box_height = 40
    translucent_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA) 
    translucent_box.fill((255, 255, 255, 100))  # Black with 50% opacity
    screen.blit(translucent_box, (bullet_icon_x - 10, bullet_icon_y - 5))

    # Draw bullet icon
    screen.blit(bullet_icon, (bullet_icon_x, bullet_icon_y))

    # Display bullet count or reloading state
    font = pygame.font.SysFont(None, 30)
    if player.firing_manager.is_reloading:
        
            
        bullet_text = font.render("  Reloading", True, (255, 255, 255))
    else:
       
        bullet_text = font.render(f" x {player.firing_manager.current_ammo}", True, (255, 255, 255))

    screen.blit(bullet_text, (bullet_icon_x + 40, bullet_icon_y + 5))
