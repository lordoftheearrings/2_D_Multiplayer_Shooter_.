import pygame.mixer

class SoundManager:
    def __init__(self):
        self.jetpack_sound = pygame.mixer.Sound("assets/sounds/jet-sound.wav")
        self.jetpack_sound.set_volume(0)
        self.jetpack_fading_in = False

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
