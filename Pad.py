import pygame


class Pad(pygame.sprite.Sprite):
    def __init__(self, left, top, width, height, color):
        pygame.sprite.Sprite.__init__(self)
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.color = color

        self.rect = pygame.Rect(self.left, self.top, self.width, self.height)
