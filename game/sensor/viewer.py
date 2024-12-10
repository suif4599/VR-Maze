import pygame


class MpuViewer:
    def __init__(self, mpu):
        self.mpu = mpu
        self.window = pygame.display.set_mode((640, 480))
        self.clock = pygame.time.Clock()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

            self.window.fill((0, 0, 0))
            self.mpu.update()
            self.mpu.draw(self.window)
            pygame.display.flip()
            self.clock.tick(60)