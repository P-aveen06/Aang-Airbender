from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


@dataclass(frozen=True, slots=True)
class Point2:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class Point3:
    x: float
    y: float
    z: float


class Finger(Enum):
    THUMB = 0
    INDEX = 1
    MIDDLE = 2
    RING = 3
    PINKY = 4


@dataclass(frozen=True, slots=True)
class HandState:
    image_landmarks: tuple[Point3, ...]
    world_landmarks: tuple[Point3, ...]
    handedness: str | None
    handedness_score: float
    frame_id: int
    capture_timestamp_ns: int
    mediapipe_timestamp_ms: int
    callback_timestamp_ns: int
    valid: bool


@dataclass(frozen=True, slots=True)
class HandFeatures:
    palm_center: Point2
    palm_orientation_radians: float
    palm_facing_score: float
    hand_scale: float
    image_hand_scale: float
    finger_extension: tuple[bool, bool, bool, bool, bool]
    finger_joint_angles_degrees: tuple[tuple[float, ...], ...]
    pinch_ratio_index: float
    pinch_ratio_middle: float
    index_middle_separation_ratio: float
    thumb_direction_down_ratio: float
    palm_velocity: Point2
    anchor_velocity: Point2
    confidence: float
    timestamp_ns: int


class IntentKind(Enum):
    POINT = auto()
    PINCH_START = auto()
    PINCH_END = auto()
    SCROLL_START = auto()
    SCROLL_UPDATE = auto()
    SCROLL_END = auto()
    CLUTCH_ON = auto()
    CLUTCH_OFF = auto()
    ENGAGE_REQUEST = auto()
    RIGHT_CLICK = auto()
    CANCEL = auto()


@dataclass(frozen=True, slots=True)
class GestureIntent:
    kind: IntentKind
    timestamp_ns: int
    point: Point2 | None = None
    velocity: Point2 | None = None
    pinch_kind: str | None = None
    reason: str | None = None


class EventKind(Enum):
    POINTER_MOVE = auto()
    LEFT_DOWN = auto()
    LEFT_UP = auto()
    RIGHT_CLICK = auto()
    SCROLL = auto()


@dataclass(frozen=True, slots=True)
class SemanticEvent:
    kind: EventKind
    timestamp_ns: int
    x: float | None = None
    y: float | None = None
    pixel_dx: float | None = None
    pixel_dy: float | None = None
