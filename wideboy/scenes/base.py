import logging
from pygame import Clock, Color, Event, Rect, FRect, Vector2
from pygame.sprite import LayeredDirty, Group
from typing import Union, TYPE_CHECKING
from wideboy.sprites.image_helpers import build_background

if TYPE_CHECKING:
    from wideboy.engine import Engine

logger = logging.getLogger("scenes.base")


class BaseScene:
    name: str
    frame: int
    debug_every_frame: int = 1000

    def __init__(
        self,
        engine: "Engine",
        bg_color: Color = Color(0, 0, 0, 255),
    ) -> None:
        self.engine = engine
        self.hass = engine.hass
        self.background = build_background(
            Vector2(self.width, self.height),
            bg_color,
        )
        self.group: LayeredDirty = LayeredDirty()
        self.animation_group: Group = Group()
        self.setup()

    def reset(self) -> None:
        self.destroy()
        self.setup()

    def setup(self) -> None:
        self.clear()
        self.empty_groups()
        self.frame = 0

    def destroy(self) -> None:
        logger.debug(f"scene:destroy name={self.name}")
        self.clear()
        self.empty_groups()
        self.screen.blit(self.background, (0, 0))

    def render(
        self,
        clock: Clock,
        delta: float,
        events: list[Event],
    ) -> list[Union[Rect, FRect]]:
        self.update(clock, delta, events)
        self.clear()
        return self.draw()

    def clear(self) -> None:
        self.group.clear(self.screen, self.background)

    def empty_groups(self) -> None:
        self.group.empty()
        self.animation_group.empty()

    def update(self, clock: Clock, delta: float, events: list[Event]) -> None:
        self.handle_events(events)
        self.animation_group.update()
        self.group.update(self.frame, clock, delta, events)
        self.frame += 1

    def draw(self) -> list[Union[FRect, Rect]]:
        return self.group.draw(self.screen)

    def handle_events(self, events: list[Event]) -> None:
        pass

    def debug(self, clock: Clock, delta: float) -> None:
        frame = self.frame
        if frame % self.debug_every_frame == 0:
            logger.debug(
                f"scene:debug frame={frame} fps={clock.get_fps()} delta={delta}"
            )

    @property
    def screen(self):
        return self.engine.screen

    @property
    def height(self):
        return self.screen.get_rect().height

    @property
    def width(self):
        return self.screen.get_rect().width
