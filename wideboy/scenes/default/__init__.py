import asyncio
import logging
import pygame

from wideboy.scenes.animation import Act, Animation
from wideboy.sprites.image import ImageSprite
from wideboy.sprites.clock import ClockSprite
from wideboy.sprites.qrcode import QRCodeSprite
from wideboy.sprites.text import TextSprite
from wideboy.sprites.weather import WeatherSprite
from wideboy.scenes.base import BaseScene
from wideboy.scenes.default.tasks import fetch_weather
from wideboy.state import DEVICE_ID
from wideboy.utils.pygame import EVENT_EPOCH_MINUTE

from wideboy.config import settings, get_config_env_var

SCENE_BACKGROUND_CHANGE_INTERVAL_MINS = int(
    get_config_env_var("SCENE_BACKGROUND_CHANGE_INTERVAL_MINS", 5)
)

logger = logging.getLogger(__name__)


class DefaultScene(BaseScene):
    name = "default"

    def __init__(
        self,
        surface: pygame.surface.Surface,
        bg_color: pygame.color.Color = (0, 0, 0),
    ) -> None:
        super().__init__(surface, bg_color)
        asyncio.create_task(fetch_weather())

    def setup(self):
        super().setup()
        # Setup background widget
        self.background_widget = ImageSprite(
            pygame.Rect(
                0,
                0 - self.height,
                self.width,
                self.height,
            ),
            (self.height * 2, self.height * 2),
            (self.width, self.height),
            255,
        )
        self.group.add(self.background_widget)
        # Setup clock widget
        self.clock_widget = ClockSprite(
            pygame.Rect(
                self.width - 128,
                2,
                128 - 2,
                self.height - 4,
            ),
            color_bg=(0, 0, 0, 255 - 64),
        )
        self.group.add(self.clock_widget)
        # Setup weather widget
        self.weather_widget = WeatherSprite(
            pygame.Rect(self.width - 192, 2, 64 - 2, 64 - 4),
            color_bg=(0, 0, 0, 255 - 64),
        )
        self.group.add(self.weather_widget)
        self.qr_widget = QRCodeSprite(
            pygame.Rect(self.width - 256, 64 - 2, 64 - 2, 64 - 4),
            f"{settings.general.remote_url}?d={DEVICE_ID}",
            (60, 60),
        )
        self.group.add(self.qr_widget)
        # Setup text widget
        # self.text_widget = TextSprite((4, self.height, 512 - 8, 56), self.state)
        # self.group.add(self.text_widget)
        # Run initial acts
        self.act_clock_show = self.build_clock_show_act()
        self.act_clock_show.start()
        self.act_weather_show = self.build_weather_show_act()
        self.act_weather_show.start()
        self.act_background_change = self.build_background_change_act()
        self.act_background_change.start()
        self.act_qrcode_show = self.build_qrcode_show_act()
        self.act_qrcode_show.start()
        # self.act_ticker_change = None  # self.build_ticker_change_act()
        # self.act_ticker_change.start()

    def update(
        self,
        delta: float,
        events: list[pygame.event.Event],
    ) -> None:
        super().update(delta, events)
        if self.act_clock_show is not None:
            self.act_clock_show.update()
        if self.act_weather_show is not None:
            self.act_weather_show.update()
        if self.act_background_change is not None:
            self.act_background_change.update()
        if self.act_qrcode_show is not None:
            self.act_qrcode_show.update()
        # if self.act_ticker_change is not None:
        #    self.act_ticker_change.update()

    # Handle Events

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        super().handle_events(events)
        for event in events:
            if event.type == EVENT_EPOCH_MINUTE:
                if event.unit % 5 == 0:
                    self.background_widget.glob_images()
                if event.unit % SCENE_BACKGROUND_CHANGE_INTERVAL_MINS == 0:
                    self.act_background_change = self.build_background_change_act()
                    self.act_background_change.start()

    # Acts

    def build_clock_show_act(self) -> Act:
        return Act(
            64,
            [
                (
                    0,
                    Animation(
                        self.clock_widget,
                        (self.width - 128, 2),
                        64,
                    ),
                ),
            ],
        )

    def build_qrcode_show_act(self) -> Act:
        return Act(
            64,
            [
                (
                    0,
                    Animation(
                        self.qr_widget,
                        (self.width - 256, 2),
                        64,
                    ),
                ),
            ],
        )

    def build_weather_show_act(self) -> Act:
        return Act(
            64,
            [
                (
                    0,
                    Animation(
                        self.weather_widget,
                        (self.width - 192, 2),
                        64,
                    ),
                ),
            ],
        )

    def build_background_change_act(self) -> Act:
        return Act(
            128,
            [
                (
                    0,
                    Animation(
                        self.background_widget,
                        (0, 0 - self.height),
                        64,
                    ),
                ),
                (64, lambda: self.background_widget.render_next_image()),
                (
                    64,
                    Animation(
                        self.background_widget,
                        (0, 0),
                        64,
                        (0, 0 - self.height),
                    ),
                ),
            ],
        )

    def build_ticker_change_act(self) -> Act:
        return Act(
            176,
            [
                (
                    0,
                    Animation(
                        self.text_widget,
                        (4, self.height),
                        64,
                    ),
                ),
                (64, lambda: self.text_widget.set_random_content()),
                (
                    96,
                    Animation(self.text_widget, (4, 4), 64, (4, self.height)),
                ),
            ],
        )
