import pygame


class Animation:
    def __init__(self, images, frame_rate, scale=1):
        if isinstance(images, str):
            images = [images]
        
        self.images = [pygame.image.load(img).convert_alpha() for img in images]
        self.frame_rate = frame_rate
        self.scale = scale
        self.frame_index = 0
        self.time_accumulator = 0  

    def update(self, delta_time):
        self.time_accumulator += delta_time
        if self.time_accumulator > self.frame_rate:
            self.time_accumulator = 0
            self.frame_index = (self.frame_index + 1) % len(self.images)

    def get_frame(self):
        frame = self.images[self.frame_index]
        if self.scale != 1:
            width, height = frame.get_size()
            frame = pygame.transform.scale(frame, (int(width * self.scale), int(height * self.scale)))
        return frame
