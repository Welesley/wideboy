import json
import logging
import pygame
import sys

from wideboy.constants import (
    EVENT_EPOCH_SECOND,
    EVENT_EPOCH_MINUTE,
    EVENT_EPOCH_HOUR,
    EVENT_MQTT_MESSAGE,
    EVENT_MASTER_POWER,
    EVENT_MASTER_BRIGHTNESS,
    EVENT_SCENE_NEXT,
    EVENT_BUTTON_A,
    EVENT_BUTTON_B,
    EVENT_BUTTON_X,
    EVENT_BUTTON_Y,
    EVENT_BUTTON_L,
    EVENT_BUTTON_R,
    EVENT_BUTTON_DPAD_LEFT,
    EVENT_BUTTON_DPAD_RIGHT,
    EVENT_BUTTON_DPAD_UP,
    EVENT_BUTTON_DPAD_DOWN,
    EVENT_NOTIFICATION_RECEIVED,
)
from wideboy.mqtt import MQTT
from wideboy.state import STATE
from wideboy.scenes.manager import SceneManager
from wideboy.utils.helpers import EpochEmitter

logger = logging.getLogger("utils.events")

# Stadia Controller
# 0: A, 1: B, 2: X, 3: Y, 4: LB, 5: RB, 6: LT, 7: RT, 8: Back, 9: Start, 10: L3, 11: R3, 12: Dpad Up, 13: Dpad Down, 14: Dpad Left, 15: Dpad Right

GAMEPAD_BUTTONS = {
    0: EVENT_BUTTON_A,
    1: EVENT_BUTTON_B,
    2: EVENT_BUTTON_X,
    3: EVENT_BUTTON_Y,
    4: EVENT_BUTTON_L,
    5: EVENT_BUTTON_R,
}

GAMEPAD_DPAD = {
    (0, 1): EVENT_BUTTON_DPAD_UP,
    (0, -1): EVENT_BUTTON_DPAD_DOWN,
    (-1, 0): EVENT_BUTTON_DPAD_LEFT,
    (1, 0): EVENT_BUTTON_DPAD_RIGHT,
}

epoch_emitter = EpochEmitter()


def handle_events(
    events: list[pygame.event.Event], matrix: any, scene_manager: SceneManager
) -> None:
    handle_pygame_events(events)
    handle_epoch_events(events)
    handle_mqtt_events(events)
    handle_joystick_events(events)
    handle_state_events(events, matrix, scene_manager)


def handle_state_events(
    events: list[pygame.event.Event], matrix: any, scene_manager: SceneManager
) -> None:
    for event in events:
        if event.type == EVENT_MASTER_POWER:
            STATE.power = event.value
            MQTT.publish(
                "master/state",
                dict(
                    state="ON" if STATE.power else "OFF",
                    brightness=STATE.brightness,
                ),
            )
        if event.type == EVENT_MASTER_BRIGHTNESS:
            STATE.brightness = event.value
            if matrix:
                matrix.brightness = (STATE.brightness / 255) * 100
            MQTT.publish(
                "master/state",
                dict(
                    state="ON" if STATE.power else "OFF",
                    brightness=STATE.brightness,
                ),
            )
        if event.type == EVENT_SCENE_NEXT:
            scene_manager.next_scene()
        if event.type == EVENT_NOTIFICATION_RECEIVED:
            logger.debug(f"message: {event.message}")
            STATE.notifications.append(event.message)


def handle_joystick_events(events: list[pygame.event.Event]) -> None:
    for event in events:
        if event.type == pygame.JOYBUTTONUP:
            logger.debug(f"Joystick BUTTONUP: {event.button}")
            if event.button == 5:  # R
                pygame.event.post(pygame.event.Event(EVENT_SCENE_NEXT))
        if event.type == pygame.JOYHATMOTION:
            logger.debug(f"Joystick HATMOTION: {event.hat} {event.value}")


def handle_mqtt_events(events: list[pygame.event.Event]):
    for event in events:
        if event.type == EVENT_MQTT_MESSAGE:
            if event.topic.endswith("master/set"):
                try:
                    payload = json.loads(event.payload)
                except Exception as e:
                    logger.warn("hass:mqtt:event error={e}")
                if "state" in payload:
                    pygame.event.post(
                        pygame.event.Event(
                            EVENT_MASTER_POWER, value=payload["state"] == "ON"
                        )
                    )
                if "brightness" in payload:
                    pygame.event.post(
                        pygame.event.Event(
                            EVENT_MASTER_BRIGHTNESS, value=payload["brightness"]
                        )
                    )
            if event.topic.endswith("scene_next/set"):
                pygame.event.post(pygame.event.Event(EVENT_SCENE_NEXT))
            if event.topic.endswith("action_a/set"):
                pygame.event.post(pygame.event.Event(EVENT_BUTTON_A))
            if event.topic.endswith("action_b/set"):
                pygame.event.post(pygame.event.Event(EVENT_BUTTON_B))
            if event.topic.endswith("message/set"):
                pygame.event.post(
                    pygame.event.Event(
                        EVENT_NOTIFICATION_RECEIVED, message=event.payload
                    )
                )


def handle_epoch_events(events: list[pygame.event.Event]) -> None:
    epochs = epoch_emitter.check()
    if epochs.get("new_sec"):
        pygame.event.post(
            pygame.event.Event(EVENT_EPOCH_SECOND, unit=epochs.get("sec"))
        )
    if epochs.get("new_min"):
        pygame.event.post(
            pygame.event.Event(EVENT_EPOCH_MINUTE, unit=epochs.get("min"))
        )
    if epochs.get("new_hour"):
        pygame.event.post(pygame.event.Event(EVENT_EPOCH_HOUR, unit=epochs.get("hour")))


def handle_pygame_events(events: list[pygame.event.Event]) -> None:
    for event in events:
        if event.type == pygame.QUIT:
            sys.exit()
