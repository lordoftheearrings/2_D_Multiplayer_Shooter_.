
import pygame



def draw_overlay(screen, player, bullet_icon, heart_icon):
    screen.blit(heart_icon, (10, 10))  
    health_bar_x = 50
    health_bar_y = 15
    health_bar_width = 200
    health_bar_height = 20

    # Draw health bar outline
    pygame.draw.rect(screen, (0, 0, 0), (health_bar_x - 1, health_bar_y - 1, health_bar_width + 2, health_bar_height + 2))

    # Draw health bar fill
    health_fill_width = int((player.health / 100) * health_bar_width)
    pygame.draw.rect(screen, (0, 255, 0), (health_bar_x, health_bar_y, health_fill_width, health_bar_height))  # Red for health

    # Draw bullets (top-right corner)
    screen_width = screen.get_width()
    bullet_icon_x = screen_width - 150
    bullet_icon_y = 10
    screen.blit(bullet_icon, (bullet_icon_x, bullet_icon_y))  # Draw bullet icon

    # Display bullet count or reloading state
    font = pygame.font.SysFont(None, 30)
    if player.firing_manager.is_reloading:
        bullet_text = font.render("Reloading...", True, (255, 255, 255))  # White text
    else:
        bullet_text = font.render(f" x {player.firing_manager.current_ammo}", True, (255, 255, 255)) 

    screen.blit(bullet_text, (bullet_icon_x + 40, bullet_icon_y + 5))  