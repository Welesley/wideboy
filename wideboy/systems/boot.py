import datetime
import logging
from dynaconf import Dynaconf
from ecs_pattern import EntityManager, System
from ..entities import AppState
from pygame.constants import KEYDOWN, KEYUP, QUIT, K_UP, K_DOWN, K_ESCAPE
from pygame.event import Event, get as get_events, post as post_event
from typing import Optional
from ..consts import (
    EVENT_CLOCK_NEW_SECOND,
    EVENT_CLOCK_NEW_MINUTE,
    EVENT_CLOCK_NEW_HOUR,
    EVENT_DEBUG_LOG,
)

logger = logging.getLogger(__name__)


class SysBoot(System):
    def __init__(
        self,
        entities: EntityManager,
        config: Dynaconf,
    ) -> None:
        self.entities = entities
        self.config = config

    def start(self) -> None:
        logger.info("Boot system starting...")
        self.entities.init()


class SysClock(System):
    def __init__(self, entities: EntityManager) -> None:
        self.entities = entities
        self.now = datetime.datetime.now()

    def start(self) -> None:
        logger.info("Clock system starting...")

    def update(self) -> None:
        now = datetime.datetime.now()
        if now.second != self.now.second:
            app_state = next(self.entities.get_by_class(AppState))
            app_state.time_now = now
            post_event(Event(EVENT_CLOCK_NEW_SECOND, dict(unit=now.second, now=now)))
            if now.second == 0 and now.minute != self.now.minute:
                post_event(
                    Event(EVENT_CLOCK_NEW_MINUTE, dict(unit=now.minute, now=now))
                )
                if now.minute == 0 and now.hour != self.now.hour:
                    post_event(
                        Event(EVENT_CLOCK_NEW_HOUR, dict(unit=now.hour, now=now))
                    )
            self.now = now


class SysInput(System):
    def __init__(self, entities: EntityManager) -> None:
        self.entities = entities
        self.event_types = (KEYDOWN, KEYUP, QUIT)  # Whitelist
        self.app_state: Optional[AppState] = None

    def start(self) -> None:
        logger.info("Input system starting...")
        self.app_state = next(self.entities.get_by_class(AppState))

    def update(self) -> None:
        if not self.app_state:
            return
        for event in get_events(self.event_types):
            event_type = event.type
            event_key = getattr(event, "key", None)
            # Quit App
            if (event_type == KEYDOWN and event_key == K_ESCAPE) or event_type == QUIT:
                self.app_state.running = False
            # Up/Down
            if event_type == KEYDOWN and event_key in (K_UP, K_DOWN):
                logger.debug("Up/Down", event_key)


class SysDebug(System):
    def __init__(self, entities: EntityManager) -> None:
        self.entities = entities

    def start(self) -> None:
        logger.info("Debug system starting...")

    def update(self) -> None:
        for event in get_events(EVENT_DEBUG_LOG):
            logger.debug(f"sys.debug.log: {event.msg}")
