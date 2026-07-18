from __future__ import annotations

import platform
import sys
import time


def main() -> int:
    failures: list[str] = []
    print(f"Python: {platform.python_version()}")
    print(f"Architecture: {platform.machine()}")
    if sys.version_info[:2] != (3, 11):
        failures.append("Python must be exactly the 3.11 series. Run: uv python pin 3.11")
    if platform.machine() != "arm64":
        failures.append("Architecture must be native arm64; reopen a non-Rosetta terminal.")

    try:
        import ApplicationServices

        accessibility_trusted = bool(ApplicationServices.AXIsProcessTrusted())
        print(f"Accessibility trusted: {accessibility_trusted}")
        if not accessibility_trusted:
            failures.append(
                "Accessibility permission is missing. Open System Settings > Privacy & Security > "
                "Accessibility and enable the terminal application running this command. Then "
                "fully quit the terminal application, reopen it, and rerun this preflight."
            )
    except Exception as error:
        failures.append(f"Could not query Accessibility through ApplicationServices: {error}")

    camera_opened = False
    camera_read = False
    try:
        import cv2

        camera = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
        try:
            camera_opened = camera.isOpened()
            if camera_opened:
                deadline = time.monotonic() + 2.0
                while not camera_read and time.monotonic() < deadline:
                    camera_read, _frame = camera.read()
        finally:
            camera.release()
        print(f"AVFoundation camera opened: {camera_opened}")
        print(f"AVFoundation camera frame read: {camera_read}")
        if not camera_opened or not camera_read:
            failures.append(
                "Camera open/read failed. Open System Settings > Privacy & Security > Camera and "
                "enable the terminal application, close other camera users, then rerun this "
                "preflight."
            )
    except Exception as error:
        failures.append(f"Could not test the AVFoundation camera through OpenCV: {error}")

    if failures:
        print("\nPREFLIGHT FAILED", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("PREFLIGHT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
