import pygame
import math

class SoundManager:
    def __init__(self):
        self.jetpack_sound = pygame.mixer.Sound("assets/sounds/jet-sound.wav")
        self.bullet_sound = pygame.mixer.Sound("assets/sounds/bullet-sound.wav")
        self.jetpack_sound.set_volume(0)
        self.jetpack_fading_in = False
        self.remote_player_volumes = {}  
        self.max_hearing_distance = 900  
        self.distance_threshold = 20

    def fade_in(self):
        if not self.jetpack_fading_in:
            self.jetpack_fading_in = True
            pygame.mixer.Sound.play(self.jetpack_sound, loops=-1)  
            self._increase_volume()

    def fade_out(self):
        if self.jetpack_fading_in:
            self.jetpack_fading_in = False
            self._decrease_volume()

    def _increase_volume(self):
        volume = self.jetpack_sound.get_volume()
        if volume < 1.0:
            self.jetpack_sound.set_volume(volume + 0.05)
            pygame.time.set_timer(pygame.USEREVENT, 50)  

    def _decrease_volume(self):
        volume = self.jetpack_sound.get_volume()
        if volume > 0.0:
            self.jetpack_sound.set_volume(volume - 0.05)
            pygame.time.set_timer(pygame.USEREVENT, 50)
            
    def play_bullet_sound(self):
        pygame.mixer.Sound.play(self.bullet_sound)
        
    def calculate_volume(self, local_player_pos, remote_player_pos):
        """Calculate volume based on proximity."""
        distance = math.sqrt(
            (remote_player_pos[0] - local_player_pos[0]) ** 2 +
            (remote_player_pos[1] - local_player_pos[1]) ** 2
        )
        if distance > self.max_hearing_distance:
            return 0 
        return max(0, 1 - (distance / self.max_hearing_distance))

    def update_remote_player_volume(self, local_player_pos, remote_players):
        """
        Update the volume for all remote players based on their proximity to the local player.
        Only recalculate if the remote player has moved significantly.
        """
        for remote_player in remote_players:
            player_id = remote_player.id
            remote_pos = (remote_player.x, remote_player.y)

            # Check if recalculation is needed
            if player_id in self.remote_player_volumes:
                last_volume, last_pos = self.remote_player_volumes[player_id]
                distance_moved = math.sqrt(
                    (remote_pos[0] - last_pos[0]) ** 2 +
                    (remote_pos[1] - last_pos[1]) ** 2
                )
                if distance_moved < self.distance_threshold:
                    continue  # Skip recalculation if movement is insignificant

            # Calculate new volume and update
            new_volume = self.calculate_volume(local_player_pos, remote_pos)
            self.remote_player_volumes[player_id] = (new_volume, remote_pos)

            # Set the volume for the bullet sound
            self.bullet_sound.set_volume(new_volume)
    
    
    def play_bullet_sound_remote(self, remote_player_id):
        """Play the bullet sound for a specific remote player."""
        if remote_player_id in self.remote_player_volumes:
            volume, _ = self.remote_player_volumes[remote_player_id]
            self.bullet_sound.set_volume(volume)
        self.bullet_sound.play()
    