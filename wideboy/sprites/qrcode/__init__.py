import logging
import pygame
import qrcode
from pygame import SRCALPHA
from wideboy.sprites.base import BaseSprite


logger = logging.getLogger("sprite.qrcode")


class QRCodeSprite(BaseSprite):
    def __init__(
        self,
        rect: pygame.rect.Rect,
        data: str,
        size: pygame.math.Vector2 = (64, 64),
        color_bg: pygame.color.Color = (255, 255, 255),
        color_fg: pygame.color.Color = (0, 0, 0),
        border: int = 2,
    ) -> None:
        super().__init__(rect)
        self.image = pygame.Surface((self.rect.width, self.rect.height), SRCALPHA)
        self.data = data
        self.size = size
        self.color_bg = color_bg
        self.color_fg = color_fg
        self.border = border
        self.draw()

    def draw(self) -> None:
        qr = qrcode.QRCode(border=self.border)
        qr.add_data(self.data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color=self.color_fg, back_color=self.color_bg)
        qr_surface = pygame.image.fromstring(
            qr_img.tobytes(), qr_img.size, qr_img.mode
        ).convert()
        qr_surface_scaled = pygame.transform.scale(qr_surface, self.size)
        self.image.blit(qr_surface_scaled, (0, 0))
        self.dirty = 1
