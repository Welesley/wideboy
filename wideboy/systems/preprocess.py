import logging
from ecs_pattern import EntityManager, System
from pygame.display import Info as DisplayInfo
from typing import Callable, Generator, List, Tuple
from ..entities import AppState, Cache, WidgetSysMessage
from ..sprites.graphics import load_image
from .scene.sprites import build_mode7_sprite, build_system_message_sprite

logger = logging.getLogger(__name__)

# Preprocessing Functions


def preprocess_load_spritesheet(
    cache: Cache,
    key: str,
    path: str,
    size: Tuple[int, int],
    tile_range: Tuple[int, int],
):
    logger.debug(f"preprocess_load_spritesheet: key={key} path={path} size={size}")
    if key not in cache.surfaces:
        cache.surfaces[key] = []
    sheet = load_image(path)
    idx = 0
    for y in range(0, sheet.get_height(), size[1]):
        for x in range(0, sheet.get_width(), size[0]):
            if tile_range[0] <= idx <= tile_range[1]:
                cache.surfaces[key].append(sheet.subsurface((x, y, size[0], size[1])))
            idx += 1


def preprocess_load_image(cache: Cache, key: str, path: str):
    logger.debug(f"preprocess_load_image: key={key} path={path}")
    if key not in cache.surfaces:
        cache.surfaces[key] = []
    cache.surfaces[key].append(load_image(path))


def preprocess_text(cache: Cache, key: str, text: str):
    logger.debug(f"preprocess_text: key={key} text={text}")
    sprite = build_system_message_sprite(text)
    if key not in cache.surfaces:
        cache.surfaces[key] = []
    cache.surfaces[key].append(sprite.image)


def preprocess_mode7(
    cache: Cache,
    key: str,
    path: str,
    canvas_size: Tuple[int, int],
    perspective=0.5,
    rotation=0.0,
    zoom=1.0,
):
    logger.debug(
        f"preprocess_mode7: key={key} path={path} canvas_size={canvas_size} perspective={perspective} rotation={rotation} zoom={zoom}"
    )

    if key not in cache.surfaces:
        cache.surfaces[key] = []
    sprite = build_mode7_sprite(
        load_image(path),
        canvas_size,
        perspective=perspective,
        rotation=rotation,
        zoom=zoom,
    )
    cache.surfaces[key].append(sprite.image)


class SysPreprocess(System):
    entities: EntityManager
    app_state: AppState
    cache: Cache
    queue: List[Tuple[Callable, Tuple]] = []
    queue_length: int = 0
    step_index: int = 0

    def __init__(self, entities: EntityManager) -> None:
        self.entities = entities
        self.display_info = DisplayInfo()
        self.task_gen = self.tasks()

    def start(self) -> None:
        logger.info("Preprocessing system starting...")
        self.app_state = next(self.entities.get_by_class(AppState))
        self.cache = next(self.entities.get_by_class(Cache))

    def update(self) -> None:
        if not self.app_state.booting:
            # logger.debug(f"sys.preprocess.update: booting={self.app_state.booting}")
            return

        if not self.cache:
            return

        try:
            next(self.task_gen)
            dots = "." * (self.step_index % 4)
            self._progress(f"Getting ready{dots}")
            self.step_index += 1
        except StopIteration:
            self.app_state.booting = False
            self._progress(visible=False)

    def _progress(self, message: str = "", visible: bool = True) -> None:
        widget_message = next(self.entities.get_by_class(WidgetSysMessage))
        if widget_message is not None:
            widget_message.fade_target_alpha = 255 if visible else 0
            widget_message.sprite = build_system_message_sprite(message)

    def tasks(self) -> Generator:
        # Duck Pixel
        preprocess_load_image(
            self.cache,
            "duck_pixel",
            f"{self.app_state.config.paths.images_sprites}/misc/duck-pixel.png",
        )
        yield True
        # Animated Duck
        preprocess_load_spritesheet(
            self.cache,
            "duck_animated",
            f"{self.app_state.config.paths.images_sprites}/ducky/spritesheet.png",
            (32, 32),
            (6, 12),
        )
        yield True
        # Mode7 Vinyl
        for r in range(1, 360, 5):
            preprocess_mode7(
                self.cache,
                "mode7_vinyl",
                f"{self.app_state.config.paths.images_sprites}/misc/vinyl.png",
                (
                    512,
                    self.display_info.current_h,
                ),
                0.2,
                0 - r,
                0.5,
            )
            preprocess_mode7(
                self.cache,
                "mode7_vinyl_serato",
                f"{self.app_state.config.paths.images_sprites}/misc/vinyl_serato.png",
                (
                    512,
                    self.display_info.current_h,
                ),
                0.2,
                0 - r,
                0.175,
            )
            yield True
