import logging
import pygame
from typing import Optional
from wideboy.sprites.base import BaseSprite
from wideboy.sprites.image_helpers import (
    load_image,
    filter_surface,
    scale_surface,
)


logger = logging.getLogger("sprite.image")


class ImageSprite(BaseSprite):
    def __init__(
        self,
        rect: pygame.Rect,
        size: Optional[pygame.math.Vector2],
        filename: str,
        alpha: int = 255,
    ) -> None:
        super().__init__(rect)
        self.filename = filename
        self.size = size
        self.alpha = alpha
        self.draw()

    def draw(self) -> None:
        surface = load_image(self.filename)
        self.rect = pygame.rect.Rect(
            self.rect[0], self.rect[1], surface.get_rect()[2], surface.get_rect()[3]
        )
        surface = scale_surface(surface, self.size)
        surface = filter_surface(surface, alpha=self.alpha)
        self.image = surface
        self.dirty = 1
