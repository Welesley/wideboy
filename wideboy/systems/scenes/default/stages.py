import logging
import random
from ecs_pattern import EntityManager

from typing import Tuple
from ..utils import Stage
from ....entities import (
    Cache,
    WidgetClockDate,
    WidgetClockTime,
    WidgetFrameAnimation,
    WidgetImage,
    WidgetTileGrid,
)
from .sprites import build_image_sprite, build_image_file_sprite

logger = logging.getLogger(__name__)

IMAGE_DUCK = "images/icons/emoji-duck.png"
IMAGE_CAT = "images/icons/emoji-cat.png"


class StageBoot(Stage):
    def __init__(self, entities: EntityManager, display_size: Tuple[int, int]) -> None:
        super().__init__(entities)
        self.display_size = display_size
        self.setup()


class StageDefault(Stage):
    image_count: int

    def __init__(
        self,
        entities: EntityManager,
        display_size: Tuple[int, int],
        image_count: int = 10,
    ) -> None:
        super().__init__(entities)
        self.display_size = display_size
        self.image_count = image_count
        self.setup()

    def setup(self) -> None:
        cache = next(self.entities.get_by_class(Cache))

        self.stage_entities.append(
            WidgetFrameAnimation(
                build_image_sprite(cache.surfaces["ducky"][0]),
                x=0,
                y=self.display_size[1] - 32,
                z_order=10,
                speed_x=1,
                bound_rect=(0, 0, self.display_size[0], self.display_size[1]),
                bound_size=(32, 32),
                bound_mode="loop",
                frames=cache.surfaces["ducky"],
                frame_delay=4,
            ),  # type: ignore[call-arg]
        )
        for i in range(self.image_count):
            self.stage_entities.append(
                WidgetImage(
                    build_image_file_sprite(IMAGE_DUCK, flip_x=True),
                    x=random.randint(0, self.display_size[0] - 32),
                    y=random.randint(0, self.display_size[1] - 32),
                    alpha=random.randint(64, 128),
                    speed_x=random.choice([-2, -1, 1, 2]),
                    speed_y=random.choice([-2, -1, 1, 2]),
                    bound_rect=(0, 0, self.display_size[0], self.display_size[1]),
                    bound_size=(32, 32),
                ),  # type: ignore[call-arg]
            )
        for w in self.entities.get_by_class(
            WidgetClockDate,
            WidgetClockTime,
            WidgetTileGrid,
        ):
            w.fade_target_alpha = 255

    def update(self) -> None:
        pass


class StageNight(Stage):
    image_count: int

    def __init__(
        self,
        entities: EntityManager,
        display_size: Tuple[int, int],
        image_count: int = 20,
    ) -> None:
        super().__init__(entities)
        self.display_size = display_size
        self.image_count = image_count
        self.setup()

    def setup(self) -> None:
        for i in range(self.image_count):
            self.stage_entities.append(
                WidgetImage(
                    build_image_file_sprite(
                        IMAGE_DUCK,
                    ),
                    x=random.randint(0, self.display_size[0] - 32),
                    y=random.randint(0, self.display_size[1] - 32),
                    alpha=random.randrange(32, 128),
                    speed_x=random.choice([-1, 1]),
                    speed_y=random.choice([-1, 1]),
                    bound_rect=(0, 0, self.display_size[0], self.display_size[1]),
                    bound_size=(32, 32),
                    bound_mode="loop",
                ),  # type: ignore[call-arg]
            )
        widget_tilegrid = next(self.entities.get_by_class(WidgetTileGrid))
        widget_tilegrid.fade_target_alpha = 128
        widget_clock_date = next(self.entities.get_by_class(WidgetClockDate))
        widget_clock_date.fade_target_alpha = 0
