import enum
import logging
import pygame
import random
import time
from datetime import datetime
from typing import Any, Callable, List, Dict, Optional, Tuple, Type, TypeVar, cast

from wideboy.constants import EVENT_HASS_STATESTREAM_UPDATE, EVENT_EPOCH_SECOND
from wideboy.scenes.base import BaseScene
from wideboy.sprites.base import BaseSprite
from wideboy.sprites.tile_grid.helpers import (
    Animator,
    AnimatorState,
    FontAwesomeIcons,
    CommonColors,
    render_icon,
    render_text,
)

# NOTES

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


# CONSTANTS

TILE_GRID_CELL_WIDTH = 64
TILE_GRID_CELL_HEIGHT = 12
TILE_GRID_CELL_ICON_WIDTH = 15
TILE_GRID_CELL_ICON_HEIGHT = 12

# TILE GRID


# Mixins


class StyleMixin:
    # Cell
    cell_color_background: pygame.Color = pygame.Color(16, 16, 16, 64)
    # Label
    label_antialias: bool = True
    label_outline: bool = True
    label_color_foreground: pygame.Color = pygame.Color(255, 255, 255, 255)
    label_color_outline: pygame.Color = pygame.Color(0, 0, 0, 255)
    # Icon
    icon_visible: bool = True
    icon_codepoint: int = FontAwesomeIcons.ICON_FA_BOLT
    icon_width: int = TILE_GRID_CELL_ICON_WIDTH
    icon_height: int = TILE_GRID_CELL_ICON_HEIGHT
    icon_color_background: pygame.Color = pygame.Color(32, 32, 32, 255)
    icon_color_foreground: pygame.Color = pygame.Color(255, 255, 255, 255)


# Tile Grid Cell Sprites


class TileGridCell(pygame.sprite.DirtySprite, StyleMixin):
    style: Dict
    width: int = TILE_GRID_CELL_WIDTH
    height: int = TILE_GRID_CELL_HEIGHT
    label: str = ""

    def __init__(self, state):
        super().__init__()
        self.state = state
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.image.fill(self.cell_color_background)
        self.rect = self.image.get_rect()

    def update(self):
        self.dirty = 1
        self.image.fill(self.cell_color_background)
        cx, cy = 0, 0
        if self.icon_visible:
            icon_surface = render_icon(
                self.icon_width,
                self.icon_height,
                self.icon_codepoint,
                self.icon_color_background,
                self.icon_color_foreground,
            )
            self.image.blit(icon_surface, (0, 0))
            cx += icon_surface.get_width()
        label_surface = render_text(
            text=self.label,
            antialias=self.label_antialias,
            color_foreground=self.label_color_foreground,
            color_outline=self.label_color_outline,
            padding=(2, 1),
            outline=self.label_outline,
        )
        self.image.blit(label_surface, (cx, 0))

    def __repr__(self):
        return f"TileGridCell(size=({self.width}x{self.height}), visible={self.visible}, label='{self.label}')"


# Tile Grid Column Group


class TileGridColumn(pygame.sprite.Group):
    animator: Animator

    def __init__(self, *sprites: TileGridCell):
        super().__init__()
        self.add(sprites)
        self.animator = Animator(range=(0.0, 64.0), open=True, speed=1.0)

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        open = any([sprite for sprite in self.sprites() if sprite.open])
        self.animator.set(open)
        self.animator.update()


# Tile Grid Sprite


class TileGrid(pygame.sprite.Sprite):
    state: Dict
    columns: List

    def __init__(self, scene: BaseScene, cells: List[List[Type[TileGridCell]]]):
        super().__init__()
        self.image = pygame.Surface((0, 0), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.scene = scene
        self.cells = cells
        self.state = self.scene.engine.state
        self.columns = []

        for column in self.cells:
            column_group: TileGridColumn = TileGridColumn()
            for cell in column:
                cell_instance = cell(self.state)
                column_group.add(cell_instance)
            self.columns.append(column_group)

    def __repr__(self):
        return f"TileGrid(columns={self.columns})"

    def update(self, frame, clock, delta, events):
        # print("TILE GRID UPDATE")
        super().update(frame, clock, delta, events)
        for event in events:
            pass
        cx, cy = 0, 0
        width, height = self.calculate_size()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        for column in self.columns:
            column.update()
            cy = 0
            for cell in column.sprites():
                cell.rect.width = column.animator.value
                cell.rect.x = cx
                cell.rect.y = cy
                cell.update()
                cy += cell.rect.height
            cx += column.animator.value

            column.draw(self.image)

    def calculate_size(self):
        width = 0
        height = 0
        for column in self.columns:
            width += column.animator.value
            height = max(height, sum([cell.rect.height for cell in column.sprites()]))
        return width, height


# USEFUL SUBCLASSES


class VerticalCollapseTileGridCell(TileGridCell):
    open: bool = True
    width: int = TILE_GRID_CELL_WIDTH
    height_animator: Animator

    def __init__(self, state):
        super().__init__(state)
        self.height_animator = Animator(range=(0.0, 12.0), open=self.open, speed=1.0)

    def update(self, *args, **kwargs):
        self.height_animator.set(self.open)
        self.height_animator.update()
        self.rect.height = self.height_animator.value
        super().update()

    @property
    def open_finished(self):
        return self.height_animator.state != AnimatorState.CLOSED

    @property
    def close_finished(self):
        return self.height_animator.state != AnimatorState.OPEN

    @property
    def animating(self):
        return self.height_animator.animating

    def __repr__(self):
        return f"VerticalCollapseTileGridCell(size=({self.width}x{self.height}), label='{self.label}', open={self.open}, height={self.height_animator.value})"
