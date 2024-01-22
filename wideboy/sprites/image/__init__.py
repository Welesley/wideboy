import logging
from pygame import Rect, Surface
from pygame.image import load as pygame_image_load
from pygame.sprite import Sprite


logger = logging.getLogger(__name__)


def build_image_sprite(filename: str):
    return ImageSprite(filename)


class ImageSprite(Sprite):
    image: Surface
    rect: Rect

    def __init__(
        self,
        filename: str,
        alpha: int = 255,
    ) -> None:
        self.image = pygame_image_load(filename, "RGBA")
        self.rect = self.image.get_rect()
