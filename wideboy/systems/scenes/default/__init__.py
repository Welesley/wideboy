import logging
import random
from ecs_pattern import EntityManager, System, entity
from pygame import Color
from pygame.display import Info as DisplayInfo
from typing import List, Optional
from ....components import ComMotion
from ....consts import EventTypes
from ....entities import (
    AppState,
    WidgetClockBackground,
    WidgetClockDate,
    WidgetClockTime,
    WidgetSysMessage,
    WidgetTileGrid,
)
from ....sprites.common import build_rect_sprite
from ....sprites.text import (
    build_date_sprite,
    build_time_sprite,
    build_system_message_sprite,
)
from ....sprites.tile_grid import build_tile_grid_sprite
from .entity_tiles import CELLS
from .stages import Stage, StageBoot, StageDefault, StageNight

logger = logging.getLogger(__name__)


def random_color():
    return Color(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


CLOCK_WIDTH = 110


class SysScene(System):
    entities: EntityManager
    booting: bool = True
    scene_mode: Optional[str]
    stage: Optional[Stage] = None
    stage_entities: List[entity] = []

    def __init__(self, entities: EntityManager) -> None:
        self.entities = entities
        self.display_info = DisplayInfo()
        self.scene_mode: Optional[str] = None

    def start(self):
        logger.info("Scene system starting...")

        self.entities.init()
        self.stage_entities = []
        self.app_state = next(self.entities.get_by_class(AppState))

        clock_x = self.display_info.current_w - CLOCK_WIDTH
        clock_y = 2
        self.entities.add(
            WidgetClockBackground(
                build_rect_sprite(Color(0, 0, 0, 192), CLOCK_WIDTH, 42),
                clock_x,
                clock_y,
                z_order=10,
            ),
            WidgetClockTime(build_time_sprite(""), clock_x, clock_y, z_order=10),
            WidgetClockDate(
                build_date_sprite(""),
                clock_x + 3,
                clock_y + 26,
                z_order=10,
            ),
            WidgetTileGrid(
                build_tile_grid_sprite(CELLS, self.app_state.hass_state),
                256,
                0,
                z_order=10,
            ),
            WidgetSysMessage(
                build_system_message_sprite("Hi!"), 5, 5, z_order=10, hidden=True
            ),
        )

    def update(self) -> None:
        self._handle_scene_mode_change()
        self._update_stage()
        self._update_core_widgets()
        self._update_motion_widgets()

    def _update_core_widgets(self) -> None:
        app_state = next(self.entities.get_by_class(AppState))

        # logger.debug(f"sys.scene.update: events={len(self.app_state.events)}")
        widget_clock_date = next(self.entities.get_by_class(WidgetClockDate))
        widget_clock_time = next(self.entities.get_by_class(WidgetClockTime))
        widget_tilegrid = next(self.entities.get_by_class(WidgetTileGrid))

        time_fmt = "%H:%M" if app_state.clock_24_hour else "%l:%M %p"
        date_fmt = "%a %d %b"

        for event_type, event_payload in self.app_state.events:
            if event_type == EventTypes.EVENT_CLOCK_NEW_SECOND:
                widget_clock_time.sprite = build_time_sprite(
                    app_state.time_now.strftime(time_fmt),
                    night=app_state.scene_mode == "night",
                )
                widget_clock_date.sprite = build_date_sprite(
                    app_state.time_now.strftime(date_fmt),
                    night=app_state.scene_mode == "night",
                )
            if event_type == EventTypes.EVENT_HASS_ENTITY_UPDATE:
                widget_tilegrid.sprite.update(event_payload["entity_id"])

        widget_tilegrid.hidden = app_state.booting
        widget_tilegrid.x = (
            self.display_info.current_w
            - CLOCK_WIDTH
            - widget_tilegrid.sprite.rect.width
        )
        widget_tilegrid.sprite.update()

    def _update_motion_widgets(self) -> None:
        for widget in self.entities.get_with_component(ComMotion):
            if (
                widget.x < 0
                or widget.x > self.display_info.current_w - widget.sprite.rect.width
            ):
                widget.speed_x = -widget.speed_x
            if (
                widget.y < 0
                or widget.y > self.display_info.current_h - widget.sprite.rect.height
            ):
                widget.speed_y = -widget.speed_y

        self.entities.delete_buffer_purge()

    def _update_stage(self) -> None:
        if self.stage is not None:
            self.stage.update()

    def _handle_scene_mode_change(self) -> None:
        if (
            self.app_state.scene_mode != self.scene_mode
            or self.app_state.booting != self.booting
        ):
            self.scene_mode = self.app_state.scene_mode
            self.booting = self.app_state.booting
            logger.info(f"sys.scene.update.scene: mode={self.scene_mode}")
            if self.app_state.booting:
                logger.info("BOOT MODE")
                self._switch_stage(
                    StageBoot(
                        (self.display_info.current_w, self.display_info.current_h)
                    )
                )
            else:
                if self.scene_mode == "night":
                    logger.info("NIGHT MODE")
                    self._switch_stage(
                        StageNight(
                            (self.display_info.current_w, self.display_info.current_h)
                        )
                    )
                else:
                    logger.info("DEFAULT MODE")
                    self._switch_stage(
                        StageDefault(
                            (self.display_info.current_w, self.display_info.current_h)
                        )
                    )

    def _switch_stage(self, stage: Stage) -> None:
        self.entities.delete_buffer_add(*self.stage_entities)
        self.stage = stage
        self.entities.add(*self.stage.entities)
        self.stage_entities = self.stage.entities
