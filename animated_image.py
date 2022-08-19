class AnimatedImage:
    def __init__(self, name, num_frames):
        self.name = name
        self.num_frames = num_frames
        self.current_frame = 0
        self.current_image = 1
    
    def update(self):
        self.current_frame += 1
        if self.current_frame >= 60:
            self.current_frame = 0
        
        self.current_image = int(self.current_frame * self.num_frames / 60) + 1
    
    def get_current_image_name(self):
        return self.name + str(self.current_image)
