from __future__ import annotations

from dataclasses import dataclass

from .config import ControlBoxConfig
from .types import Point2

CAMERA_INPUT_IS_MIRRORED = False


@dataclass(frozen=True, slots=True)
class DisplayBounds:
    x: float
    y: float
    width: float
    height: float


def camera_to_display_orientation(point: Point2, *, camera_input_is_mirrored: bool) -> Point2:
    return point if camera_input_is_mirrored else Point2(1.0 - point.x, point.y)


def corrected_handedness(label: str | None, *, camera_input_is_mirrored: bool) -> str | None:
    if label is None or not camera_input_is_mirrored:
        return label
    # MediaPipe Tasks reports the physical hand for the unmirrored AVFoundation
    # frame. Mirroring the input swaps the visible chirality, so only that path
    # needs its label exchanged.
    if label == "Left":
        return "Right"
    if label == "Right":
        return "Left"
    return label


def map_control_box_to_display(
    point: Point2,
    control_box: ControlBoxConfig,
    bounds: DisplayBounds,
) -> Point2:
    normalized_x = (point.x - control_box.left) / (control_box.right - control_box.left)
    normalized_y = (point.y - control_box.top) / (control_box.bottom - control_box.top)
    normalized_x = min(max(normalized_x, 0.0), 1.0)
    normalized_y = min(max(normalized_y, 0.0), 1.0)
    return Point2(
        bounds.x + normalized_x * bounds.width,
        bounds.y + normalized_y * bounds.height,
    )
