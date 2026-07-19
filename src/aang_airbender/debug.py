from __future__ import annotations

from typing import Any

from .coordinates import DisplayBounds
from .fsm import GestureEngine
from .poses import PoseClassification
from .types import HandFeatures, HandState

# OpenCV uses BGR. These mirror the design system's primary text and light background.
DEBUG_TEXT_BGR = (27, 24, 24)
DEBUG_TEXT_OUTLINE_BGR = (248, 250, 251)
DEBUG_FONT_SCALE = 0.38
DEBUG_LINE_HEIGHT_PX = 17
DEBUG_MARGIN_PX = 8


def debug_text_origins(height: int, line_count: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (
            DEBUG_MARGIN_PX,
            height - DEBUG_MARGIN_PX - DEBUG_LINE_HEIGHT_PX * (line_count - line_number - 1),
        )
        for line_number in range(line_count)
    )


def overlay_origin(
    bounds: DisplayBounds,
    *,
    width: int,
    height: int,
    margin: int,
) -> tuple[float, float]:
    """Return the bottom-left AppKit origin for an overlay on the main display."""
    return (
        bounds.x + margin,
        bounds.y + margin,
    )


class _MacOSOverlayWindow:
    """Small borderless, click-through AppKit image window."""

    def __init__(
        self,
        *,
        bounds: DisplayBounds,
        width: int,
        height: int,
        margin: int,
        corner_radius: float,
    ) -> None:
        import AppKit

        self._appkit = AppKit
        self._app = AppKit.NSApplication.sharedApplication()
        self._app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
        self._app.finishLaunching()

        x, y = overlay_origin(bounds, width=width, height=height, margin=margin)
        rect = AppKit.NSMakeRect(x, y, width, height)
        self._window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            rect,
            AppKit.NSWindowStyleMaskBorderless,
            AppKit.NSBackingStoreBuffered,
            False,
        )
        self._window.setLevel_(AppKit.NSFloatingWindowLevel)
        self._window.setOpaque_(False)
        self._window.setBackgroundColor_(AppKit.NSColor.clearColor())
        self._window.setHasShadow_(True)
        self._window.setHidesOnDeactivate_(False)
        self._window.setIgnoresMouseEvents_(True)
        self._window.setReleasedWhenClosed_(False)
        self._window.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
            | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
        )

        self._image_view = AppKit.NSImageView.alloc().initWithFrame_(
            AppKit.NSMakeRect(0, 0, width, height)
        )
        self._image_view.setImageScaling_(AppKit.NSImageScaleAxesIndependently)
        self._image_view.setWantsLayer_(True)
        layer = self._image_view.layer()
        layer.setCornerRadius_(corner_radius)
        layer.setMasksToBounds_(True)
        self._window.setContentView_(self._image_view)
        self._image: Any | None = None
        self._window.orderFrontRegardless()
        self._pump_events()

    def show_jpeg(self, encoded_jpeg: bytes) -> None:
        data = self._appkit.NSData.dataWithBytes_length_(encoded_jpeg, len(encoded_jpeg))
        self._image = self._appkit.NSImage.alloc().initWithData_(data)
        self._image_view.setImage_(self._image)
        self._pump_events()

    def _pump_events(self) -> None:
        until = self._appkit.NSDate.dateWithTimeIntervalSinceNow_(0)
        while True:
            event = self._app.nextEventMatchingMask_untilDate_inMode_dequeue_(
                self._appkit.NSEventMaskAny,
                until,
                self._appkit.NSDefaultRunLoopMode,
                True,
            )
            if event is None:
                return
            self._app.sendEvent_(event)

    def close(self) -> None:
        self._window.orderOut_(None)
        self._window.close()


class CameraOverlayRenderer:
    def __init__(
        self,
        *,
        every_n_frames: int,
        bounds: DisplayBounds,
        width: int,
        height: int,
        margin: int,
        corner_radius: float,
        mirror: bool,
        debug: bool,
    ) -> None:
        if every_n_frames < 1:
            raise ValueError("Preview render cadence must be positive")
        if width < 1 or height < 1:
            raise ValueError("Preview dimensions must be positive")
        import cv2

        self._cv2 = cv2
        self._every_n_frames = every_n_frames
        self._width = width
        self._height = height
        self._mirror = mirror
        self._debug = debug
        self._window = _MacOSOverlayWindow(
            bounds=bounds,
            width=width,
            height=height,
            margin=margin,
            corner_radius=corner_radius,
        )

    def render(
        self,
        image_bgr: Any,
        frame_id: int,
        hand: HandState | None,
        features: HandFeatures | None,
        pose: PoseClassification | None,
        engine: GestureEngine,
    ) -> None:
        if frame_id % self._every_n_frames:
            return
        image = self._cv2.resize(image_bgr, (self._width, self._height))
        if self._mirror:
            image = self._cv2.flip(image, 1)
        if self._debug:
            self._annotate(image, frame_id, hand, features, pose, engine)
        encoded, jpeg = self._cv2.imencode(
            ".jpg",
            image,
            (self._cv2.IMWRITE_JPEG_QUALITY, 90),
        )
        if not encoded:
            raise RuntimeError("Could not encode the camera overlay frame")
        self._window.show_jpeg(jpeg.tobytes())

    def _annotate(
        self,
        image: Any,
        frame_id: int,
        hand: HandState | None,
        features: HandFeatures | None,
        pose: PoseClassification | None,
        engine: GestureEngine,
    ) -> None:
        height, width = image.shape[:2]
        if hand is not None:
            for landmark in hand.image_landmarks:
                normalized_x = 1.0 - landmark.x if self._mirror else landmark.x
                self._cv2.circle(
                    image,
                    (int(normalized_x * width), int(landmark.y * height)),
                    3,
                    (0, 255, 0),
                    -1,
                )
        pose_names = "none"
        if pose is not None:
            pose_names = (
                ",".join(
                    name
                    for name, active in (
                        ("point", pose.pointer_family),
                        ("index-pinch", pose.index_pinch_closed),
                        ("middle-pinch", pose.middle_pinch_closed),
                        ("two", pose.two_finger),
                        ("fist", pose.fist),
                        ("thumb-down", pose.thumbs_down),
                        ("wake", pose.wake_palm),
                    )
                    if active
                )
                or "unknown"
            )
        confidence = 0.0 if features is None else features.confidence
        callback_latency_ms = (
            0.0
            if hand is None
            else (hand.callback_timestamp_ns - hand.capture_timestamp_ns) / 1_000_000
        )
        lines = (
            f"pose={pose_names} confidence={confidence:.2f}",
            f"engagement={engine.engagement.name} gesture={engine.gesture.name}",
            f"frame={frame_id} callback_ms={callback_latency_ms:.1f}",
        )
        for line, origin in zip(lines, debug_text_origins(height, len(lines)), strict=True):
            self._cv2.putText(
                image,
                line,
                origin,
                self._cv2.FONT_HERSHEY_SIMPLEX,
                DEBUG_FONT_SCALE,
                DEBUG_TEXT_OUTLINE_BGR,
                2,
                self._cv2.LINE_AA,
            )
            self._cv2.putText(
                image,
                line,
                origin,
                self._cv2.FONT_HERSHEY_SIMPLEX,
                DEBUG_FONT_SCALE,
                DEBUG_TEXT_BGR,
                1,
                self._cv2.LINE_AA,
            )

    def close(self) -> None:
        self._window.close()
