# Aang-Airbender — control your Mac with your hands in the air

> Webcam-based gesture control for macOS. Phase 1 replaces core trackpad actions; later phases add system navigation and, through blended modalities, absorb selected keyboard roles. Aang-Airbender evokes controlling the environment through deliberate movement, matching the app's air-gesture interaction model.

**Target stack:** Python 3.11 · MediaPipe Tasks Hand Landmarker · OpenCV for capture initially · PyObjC (`Quartz`, `AppKit`, `AVFoundation` as needed) · YAML configuration with schema validation · macOS 13+ · Apple Silicon, initially an M2 MacBook Air

**Workflow:** This file is the source of truth. Track execution in `PROGRESS.md`. One phase is one milestone, normally one PR-sized chunk. Thresholds and gesture definitions are initial hypotheses until validated against recorded data.

---

## 1. Vision & product principles

**End goal:** perform the useful roles of a trackpad and selected keyboard interactions in the air—pointer movement, clicks, drag, scroll, system navigation, app switching, media control, and text or command input through blended modalities such as gesture plus voice. Later versions should add per-app capabilities that a physical trackpad cannot offer.

Principles that govern every design decision:

1. **Never fight the OS.** Inject standard mouse, scroll, and keyboard events and inherit macOS behavior where practical. Do not recreate operating-system semantics unless testing proves native behavior is insufficient.
2. **Deliberate over sensitive.** A gesture application that misfires while the user talks, reaches for an object, or adjusts posture is unusable. Engagement, strict gesture predicates, hysteresis, dwell time, cooldowns, neutral transitions, and cancellation rules are required.
3. **Feel is the product.** Target motion-to-visible-cursor latency below 80 ms, low stationary jitter, rapid response to intentional motion, and predictable acceleration. Every phase ships with measurable feel and reliability targets.
4. **Safety is a system invariant.** No mouse button may remain logically held after tracking loss, disengagement, an exception, camera failure, configuration reload, profile change, or process shutdown.
5. **Modular event core.** Capture emits frames; perception emits `HandState`; feature extraction emits `HandFeatures`; gesture recognizers emit `GestureIntent`; control converts intentions into semantic events; actions dispatch them to macOS. New models, gestures, modalities, and per-app behaviors plug into this pipeline.
6. **Time, not frame count, defines intent.** Gesture stability, cooldowns, hand-loss handling, and wake-pose dwell use monotonic timestamps. Frame counts may be recorded for diagnostics but never define behavior.
7. **Configurable, but not unbounded.** Thresholds, mappings, profiles, and macros live in versioned configuration validated against a schema. Invalid or unsafe values fail closed.
8. **Privacy by default.** Camera frames stay local. Frames are never stored unless the user explicitly starts fixture or diagnostics recording.
9. **Honest about the keyboard.** Air-typing QWERTY is not a primary goal. Prose input uses dictation or local speech recognition; commands use contextual gesture macros; an on-screen keyboard remains the universal fallback.
10. **Validate packaging early.** A Terminal prototype is not proof that the eventual `.app` bundle can obtain permissions, load native libraries, find model assets, and run reliably.

---

## 2. Architecture

```text
┌───────────┐   latest frame   ┌─────────────┐   HandState    ┌────────────┐
│ capture/  │ ───────────────▶ │ perception/ │ ─────────────▶ │ features/  │
│ OpenCV or │                  │ MediaPipe   │                │ geometry + │
│ AVFound.  │                  │ Tasks       │                │ motion     │
└───────────┘                  └─────────────┘                └─────┬──────┘
                                                                    │ HandFeatures
                                                                    ▼
┌───────────┐   OS events   ┌─────────────┐   SemanticEvent   ┌──────────────┐
│ macOS     │ ◀──────────── │ actions/    │ ◀─────────────── │ control/     │
│ Quartz    │               │ CGEvent     │                  │ filter, map, │
└───────────┘               │ dispatcher  │                  │ acceleration│
                            └──────┬──────┘                  └──────┬───────┘
                                   │                                │ GestureIntent
                             ┌─────▼─────┐                    ┌─────▼────────┐
                             │ hud/      │                    │ gestures/    │
                             │ menu bar  │                    │ recognizers │
                             │ + overlay │                    │ + FSM       │
                             └───────────┘                    └──────────────┘

config/      versioned YAML + schema
calibrate/   user-specific threshold and control-box wizard
metrics/     timestamps, counters, traces, Fitts-style tests
profiles/    bundle-identifier-based per-app behavior
```

### 2.1 Module contracts

#### `capture/`

- Starts with OpenCV using the AVFoundation backend at 640×480 and a requested 30 fps.
- Runs on a dedicated worker.
- Uses a single-slot latest-frame handoff: overwrite stale frames; never queue them.
- Attempts `CAP_PROP_BUFFERSIZE=1`, but never assumes the backend honors it.
- Records a capture timestamp as close to frame acquisition as possible.
- Measures actual resolution, achieved frame rate, and frame age.
- May be replaced by native `AVCaptureSession` through PyObjC if OpenCV buffering or permission behavior is unacceptable.

#### `perception/`

- Uses MediaPipe Tasks `HandLandmarker` in `LIVE_STREAM` mode.
- Initial configuration:
  - `num_hands=2`
  - `min_hand_detection_confidence=0.7`
  - `min_hand_presence_confidence=0.7`
  - `min_tracking_confidence=0.6`
- Supplies strictly monotonically increasing integer-millisecond timestamps to `detect_async()`.
- Treats live-stream callbacks as asynchronous, tolerant of dropped input frames, and executed in a MediaPipe-controlled callback context.
- The callback performs no UI work, OS-event dispatch, blocking work, or direct FSM mutation. It creates an immutable result and overwrites a single-slot latest-result handoff for the pipeline thread.
- Pins the MediaPipe package and model asset version.
- Emits one immutable frame containing zero, one, or two immutable hand results:

```python
HandFrame {
    hands: tuple[HandState, ...],
    frame_id,
    capture_timestamp,
    mediapipe_timestamp_ms,
    callback_timestamp,
}

HandState {
    image_landmarks[21],
    world_landmarks[21],
    handedness,
    handedness_score,
    valid
}
```

- Defines and tests a single mirroring convention. Pointer X mirroring, preview mirroring, and handedness correction must not be handled independently in several modules.
- Assigns physical left/right roles from corrected handedness and confidence, never MediaPipe result-array ordering. Missing, low-confidence, or duplicate role results fail closed.

#### `features/`

Calculates reusable geometry and motion once per result:

```python
HandFeatures {
    index_tip,
    palm_center,
    palm_orientation,
    palm_facing_score,
    hand_scale,
    finger_extension[5],
    finger_joint_angles,
    pinch_ratio_index,
    pinch_ratio_middle,
    palm_velocity,
    anchor_velocity,
    confidence,
    timestamp
}
```

Rules:

- Prefer world-space distances when sufficiently stable.
- Fall back to robust image-space normalization when needed.
- The active Phase 1 pointer anchor is the right-hand index fingertip at image landmark 8.
- Palm center remains reusable geometry and is a weighted centroid of landmarks 0, 5, 9, 13, and 17 rather than only the midpoint of 5 and 17.
- Finger extension is based on joint angles in a palm-relative coordinate system, not only fingertip Y-position.
- `hand_scale` must remain usable under moderate palm rotation. Start with world-space `dist(5,17)` and evaluate a robust combined scale during calibration.

#### `gestures/`

- Contains stateless pose predicates plus stateful recognizers and a master FSM.
- Pose predicates are strict and mutually exclusive where possible.
- Gesture transitions use elapsed monotonic time.
- Emits intentions, not screen coordinates or OS calls:

```python
POINT(index_tip)
CLICK_ARM
CLICK_COMMIT
CLICK_CANCEL
CANCEL
```

- `UNKNOWN` emits nothing.
- Dangerous recognitions are prioritized: safety, pending-click cancellation, left-pinch lifecycle, right-index point, unknown.

#### `control/`

- Applies a low-latency One Euro filter or another validated filter to the right index-fingertip pointer anchor.
- Converts gesture intent into semantic OS events.
- Supports absolute mapping from the configured control box to the main display.
- Freezes the pointer at its current mapped location when a left-hand pinch candidate begins. A stable pinch followed by release commits exactly one click at that frozen location; an invalid or lost role cancels it.
- Emits:

```python
POINTER_MOVE(screen_x, screen_y)
LEFT_CLICK(screen_x, screen_y)
```

#### `actions/`

- Thin Quartz and AppKit dispatch layer.
- Knows nothing about hands.
- Posts pointer movement and atomic single left clicks.
- Tracks locally held buttons and modifier keys.
- Implements idempotent `safe_release_all()`.
- Calls `safe_release_all()` on every abnormal or terminal path.
- Ensures each committed pinch is one single-click event. Two rapid pinch cycles remain two single clicks and are not promoted to an explicit double-click.

#### `hud/`

- Menu-bar application plus an optional minimal, non-activating, always-on-top status pill.
- Runs UI work on the AppKit main thread.
- Displays engagement, tracking confidence, current pose, pinch state, clutch state, active profile, and fault state.
- Feedback is a usability and safety feature, not only a debugging aid.

#### `config/`

- Versioned `config.yaml` plus a schema.
- Includes thresholds, timings, mappings, acceleration settings, scroll behavior, macros, and per-app profiles.
- Rejects invalid values at startup and keeps the system disengaged.
- Includes `config_version` and rejects unsupported versions with a clear diagnostic. Migration support is added only when the first incompatible schema change exists.
- Uses macOS bundle identifiers for application profiles.

#### `calibrate/`

Interactive wizard that:

- Captures relaxed open and closed pinch samples.
- Measures user-specific palm scale and hand orientation range.
- Recommends hysteresis thresholds rather than blindly accepting fixed defaults.
- Defines absolute control box and relative gain.
- Validates left- versus right-click confusion.
- Provides a manual recalibration command.

#### `metrics/`

Records:

```text
capture timestamp
inference start and result timestamps
control timestamp
dispatch timestamp
frame age
software processing latency
stationary jitter
false action counters
state transitions with reason codes
CPU and memory
battery percentage per hour during controlled tests
```

### 2.2 Safety invariants

These rules are mandatory:

1. Every emitted `LEFT_DOWN` has exactly one eventual `LEFT_UP`.
2. Tracking loss longer than the short grace period releases all held inputs immediately; it does not wait for the full disengagement timeout.
3. Disengagement, camera failure, model failure, exception, profile reload, display topology change, app shutdown, and panic action call `safe_release_all()`.
4. Pending clicks are cancelled when confidence drops or either required hand role becomes invalid or disappears.
5. A newly reacquired hand must remain stable briefly before cursor movement resumes.
6. Physical trackpad and mouse input always remain available.
7. The panic mechanism must include an external recovery path. A keyboard shortcut handled only by the same frozen process is not sufficient by itself.

### 2.3 Phase 1 v1.2 state machine

```text
INACTIVE
    ├─ right index-point pose stable for configured dwell ─▶ POINTING
    └─ fatal subsystem error ───────────────────────────────▶ FAULT
POINTING
    ├─ right index-point pose breaks or right hand is lost ─▶ INACTIVE
    ├─ left thumb-index pinch closes ───────────────────────▶ CLICK_PENDING
    └─ fatal subsystem error ───────────────────────────────▶ FAULT
CLICK_PENDING
    ├─ pinch remains closed for configured stability ───────▶ CLICK_ARMED
    ├─ pinch opens early or either role becomes invalid ────▶ POINTING or INACTIVE, with click cancelled
    └─ fatal subsystem error ───────────────────────────────▶ FAULT
CLICK_ARMED
    ├─ left pinch opens ────────────────────────────────────▶ POINTING, with one single click at the frozen anchor
    ├─ either hand role becomes invalid ────────────────────▶ POINTING or INACTIVE, with click cancelled
    └─ fatal subsystem error ───────────────────────────────▶ FAULT
FAULT
    └─ user restarts or explicitly resets after safe release
```

Initial timing hypotheses:

```text
right-point stability:       80–120 ms
left-pinch stability:        80–120 ms
short hand-loss grace:       150–250 ms
reacquisition stability:     150–250 ms
```

Rules:

- Movement is active only while a stable physical-right-hand index-point pose is recognised.
- Only a physical-left-hand thumb-index pinch may arm a click, and only while right-hand pointing is valid.
- The click anchor freezes when the pinch candidate begins and remains frozen until release or cancellation.
- No OS button is held across perception frames; click commit posts one owned down/up pair atomically.
- Loss of either required role cancels the pending click immediately. Right-hand loss also freezes pointer output.
- `UNKNOWN` never dispatches an action.
- A reacquired right-hand point pose must remain stable for the configured interval before cursor movement resumes.

---

## 3. Gesture vocabulary — v1.2 owner-approved Phase 1 scope

Owner-approved exception dated 2026-07-18: this v1.2 vocabulary supersedes v1.1 for Phase 1. All former Phase 1 meanings—wake/open palm, palm pointer, right-hand click, drag, right-click, scroll, fist clutch, thumbs-down, and gesture double-click—are disabled, not reassigned. Safety cleanup remains mandatory.

| Physical role and pose | Strict initial detection | Action |
|---|---|---|
| Right hand: index-point ☝🏻 | Index extended; middle, ring, and pinky curled; thumb unconstrained; confidence valid and pose stable for the configured interval | Move cursor from the One Euro-filtered index fingertip at landmark 8 |
| Left hand: thumb-index pinch | Normalized thumb-index ratio enters the closed threshold while a valid right-hand point controls the cursor | Freeze the current pointer location; after the configured pinch stability, release commits exactly one left click at the frozen location |
| Either required role lost or invalid during click | Physical-left or physical-right role is absent, ambiguous, duplicated, or below confidence | Cancel the click; never emit a partial click |

### 3.1 Disabled gestures

Open palm, palm movement, right-hand pinch, held-pinch drag, thumb-middle pinch, two fingers, fist, thumbs-down, and all other poses emit no action in Phase 1 v1.2. They must not remain reachable behind a runtime flag in the active Phase 1 pipeline.

### 3.2 Pinch hysteresis

Initial normalized thresholds:

```text
closed: ratio < 0.35
open:   ratio > 0.50
```

The interval between them is a dead zone. Calibration may recommend per-user values. No fixed threshold is considered final until measured across distance, lighting, hand rotation, and the supported left-click hand.

### 3.3 Gesture priority

```text
fault and emergency handling
→ cancellation of an armed or pending click
→ active left-pinch lifecycle
→ right index-point recognizer
→ unknown
```

### 3.4 Design invariants

- Pinch metrics are normalized for hand size and camera distance.
- Hysteresis prevents boundary flicker.
- Physical handedness defines roles: only the right hand moves the pointer and only the left hand clicks. Result ordering never defines roles.
- Pointer anchoring uses right-hand image landmark 8 and is low-latency One Euro filtered.
- Pointer movement requires a strict right index-point pose; ordinary hand motion emits nothing.
- A click is anchored at the mapped pointer location present when the left pinch candidate begins.
- A stable left pinch commits only on release; holding it has no drag meaning.
- No OS left button is held across perception frames.
- All gesture dwells, grace periods, and stability checks use monotonic elapsed time and validated configuration values.
- Missing, invalid, low-confidence, or ambiguous role assignment fails closed.
- Loss of either required role cancels a pending click; right-hand loss freezes pointer output.
- Each committed pinch posts exactly one single click. Rapid successive pinches do not request explicit double-click semantics.
- All non-v1.2 gestures are disabled and emit nothing.

---

## 4. Phases

### Phase 0 — Technical spike (1 day)

**Goal:** prove the end-to-end pipeline on the target M2 MacBook Air before adding gesture-spec complexity.

- [ ] Create a minimal `uv` environment with pinned MediaPipe, OpenCV, PyObjC, and the exact Hand Landmarker model asset.
- [ ] Document and verify Camera and Accessibility permissions for the Terminal-run spike.
- [ ] Capture through OpenCV AVFoundation using a single-slot latest-frame handoff; measure actual frame age and achieved rate.
- [ ] Run `HandLandmarker` in `LIVE_STREAM` mode with strictly monotonic input timestamps and a callback-to-pipeline latest-result handoff.
- [ ] Move the cursor with a raw Quartz mouse event using one tracked hand coordinate.
- [ ] Record a timestamp trace from capture through callback and event dispatch.
- [ ] Simulate tracking loss after a mouse-down and verify explicit safe release.

**Accept:**

- Cursor follows hand motion on the target Mac.
- Native ARM64 dependencies install from a clean environment.
- Processing builds no unbounded frame or result queue.
- Frame age, inference/callback cadence, and dispatch timing are measured.
- No held mouse state survives the simulated failure path.

Do not add the full gesture vocabulary, calibration, HUD, acceleration curves, configuration migration, or production abstractions during this spike.

### Phase 1 — Right-point, left-click, and safety (3–5 focused days)

**Goal:** provide basic trackpad replacement with safe failure behavior.

- [ ] Record a 30-second landmark fixture and a short video fixture using `scripts/record_landmarks.py` and `scripts/record_video_fixture.py`.
- [ ] Implement `HandState`, `HandFeatures`, `GestureIntent`, and `SemanticEvent` types.
- [ ] Configure two-hand tracking and assign physical left/right roles by corrected handedness, never result ordering.
- [ ] Implement palm-relative finger-angle classification.
- [ ] Add the strict physical-right index-point predicate and physical-left thumb-index pinch hysteresis.
- [ ] Add fixture-based unit tests for geometry and pose classification.
- [ ] Implement the v1.2 point/click FSM with timestamp-based stability and cancellation transitions.
- [ ] Implement left-pinch hysteresis and anchor one click at the location where the pinch candidate begins.
- [ ] Disable all former Phase 1 gesture meanings in the active pipeline.
- [ ] Add low-latency One Euro filtering to the right index fingertip and test stationary jitter plus moving response.
- [ ] Implement absolute mapping from a configurable central control box to the active display region.
- [ ] Define mirroring and handedness behavior in one module and test it.
- [ ] Emit an atomic real single left click on stable pinch release; never hold a button across frames.
- [ ] Implement `safe_release_all()` and call it from all terminal and error paths.
- [ ] Add `config.yaml` plus schema validation. No untracked magic thresholds.
- [ ] Add `--debug` rendering of landmarks, pose, confidence, FSM state, and timing every Nth frame; off by default.
- [ ] Add structured state-transition logs and false-action counters.
- [ ] Add role-order, role-loss, click-anchor, click-cancellation, and repeated-single-click regression tests.

**Accept:**

- Point at and open applications without touching the trackpad for five minutes.
- Targets at least 44 display-coordinate units wide are acquired reliably in absolute mode.
- Zero false clicks during 10 minutes of normal pointing.
- Fewer than one false click during a 30-minute adversarial test containing normal conversational hand motion.
- Right-hand pinch, left-hand pointing, open palms, fists, two fingers, thumbs-down, and hand loss emit no click.
- Loss or invalidation of either required hand role cancels a pending click without a down event.
- Each committed left pinch emits exactly one down/up pair with single-click semantics at the frozen anchor.
- Disengagement, exception simulation, camera shutdown, and process exit release all held inputs.

### Phase 1.5 — Bundle and permission viability (1–2 days)

**Goal:** prove that the Python implementation can operate as a macOS application before investing further.

- [ ] Build an unsigned local `.app` bundle with a stable bundle identifier.
- [ ] Include MediaPipe native libraries and model assets in the bundle.
- [ ] Add `NSCameraUsageDescription` and any required bundle metadata.
- [ ] Add onboarding checks for Camera and Accessibility authorization.
- [ ] Verify that the UI runs on the AppKit main thread while capture and inference use workers.
- [ ] Verify permissions apply to the bundled app rather than only Terminal.
- [ ] Confirm permissions and model loading survive app restart and rebuild scenarios.
- [ ] Record packaging limitations and decision criteria for an early Swift pivot.

**Accept:**

- The local `.app` launches outside Terminal.
- Camera and Accessibility prompts behave correctly.
- The MediaPipe model loads from the bundle.
- Cursor movement and one click work from the bundled application.
- Permissions remain usable after a normal restart of the app.

### Phase 2 — Precision, calibration, and feel (5–10 focused days)

**Goal:** move from a demo to a plausible daily-use controller.

- [ ] Add relative mapping: palm velocity to cursor velocity through a configurable acceleration curve.
- [ ] Preserve absolute mode for comparison and accessibility preferences.
- [ ] Make clutch repositioning comfortable in relative mode.
- [ ] Add stationary dead zone and rapid-motion responsiveness tuning.
- [ ] Add scroll baseline, gain, maximum velocity, and optional momentum.
- [ ] Ensure scroll mode cannot move the pointer.
- [ ] Build the calibration wizard for pinch thresholds, orientation range, control box, relative gain, and right-click confusion.
- [ ] Build menu-bar HUD and optional corner status pill.
- [ ] Add `SUSPENDED` state and stable reacquisition behavior.
- [ ] Add inference throttling when no hand is detected; measure whether it actually reduces power consumption.
- [ ] Evaluate native AVFoundation capture if OpenCV frame age remains excessive.
- [ ] Add motion-to-visible-cursor latency probe.
- [ ] Add Fitts-style target acquisition test.
- [ ] Add stationary-jitter test.
- [ ] Add 30-minute reliability and battery test.
- [ ] Add multi-display behavior or explicitly keep it outside the supported scope.
- [ ] Temporarily suspend gesture pointer output after detected physical mouse or trackpad movement if testing shows input conflict.

**Accept:**

- Acquire 20-unit targets reliably in relative mode under controlled testing.
- Measured motion-to-visible-cursor latency is below 80 ms at the median and has a documented high-percentile value.
- Stationary pointer jitter remains within the configured tolerance.
- Zero false clicks in a normal 30-minute work session target; any observed failure is captured as a replayable fixture.
- No stuck drag, scroll burst, or cursor jump occurs after temporary hand loss and reacquisition.
- CPU, memory, and battery usage are documented on the target Mac.

### Phase 3 — System control (4–7 focused days)

**Goal:** reproduce useful macOS navigation through configurable shortcuts and add the first interaction patterns that go beyond a trackpad.

- [ ] Define the system-command pose in the gesture vocabulary and confusion matrix, then add horizontal swipe from that pose with distance, velocity, duration, and vertical-deviation constraints; it must remain distinct from the relaxed-open-hand pointer pose.
- [ ] Map validated swipes to configurable Spaces shortcuts.
- [ ] Add swipe up and down for configurable Mission Control and App Exposé shortcuts.
- [ ] Validate configured shortcuts during onboarding because users may change or disable them.
- [ ] Build app-switcher mode: hold the switcher modifier, step selection with lateral motion, release to commit, cancel safely on tracking loss.
- [ ] Add a volume-dial experiment using pinch-and-twist.
- [ ] Implement media actions through a dedicated path rather than assuming all are ordinary key chords.
- [ ] Add application-shortcut zoom through configurable per-app bindings; do not claim it is identical to native multitouch pinch in every app.
- [ ] Add generic `gesture → action` macro configuration.
- [ ] Add cooldowns and neutral-transition requirements for every discrete system action.

**Accept:**

- Switch Spaces, open Mission Control, use App Exposé, and complete app switching by air alone.
- Every held modifier is released on cancellation, hand loss, disengagement, and process shutdown.
- Volume adjustment works on the target macOS version or is explicitly deferred with measured findings.
- At least one custom macro is added through configuration without code changes.

### Phase 4 — Text and commands: replacing keyboard roles (exploratory epics)

**Goal:** replace important keyboard roles, not physical key-by-key typing.

#### Phase 4A — System dictation trigger

- [ ] Add a dedicated, rare dictation gesture.
- [ ] Trigger the user's configured macOS dictation shortcut.
- [ ] Provide obvious HUD feedback for dictation state.
- [ ] Ensure gesture input does not interfere with text selection or insertion.

**Accept:** dictate and send a short message using gesture plus macOS dictation.

#### Phase 4B — Contextual macro pad

- [ ] Enter command mode with an explicit pose.
- [ ] Recognise one of eight directional flicks using angle, distance, duration, and return-to-neutral constraints.
- [ ] Resolve actions by frontmost application's bundle identifier.
- [ ] Display command hints in the HUD.

**Accept:** trigger five daily-use commands reliably across at least two applications.

#### Phase 4C — On-screen keyboard fallback

- [ ] Integrate with the macOS Accessibility Keyboard through pointer and pinch.
- [ ] Add a quick action to show or hide it.

**Accept:** complete a short text entry without a physical keyboard, with no claim of speed.

#### Phase 4D — Local speech recognition, optional research track

- [ ] Obtain microphone permission separately from camera permission.
- [ ] Capture audio, implement voice-activity detection, transcribe locally, and insert text safely.
- [ ] Provide cancellation, error, privacy, and model-download behavior.

**Accept:** local transcription is meaningfully better than the system-dictation workflow for a defined use case; otherwise retain system dictation.

#### Phase 4E — Air-writing moonshot

- [ ] Prototype a `$1` Unistroke Recognizer over fingertip trails for a small symbol set.
- [ ] Limit the first experiment to commands, digits, or launcher shortcuts rather than prose.

**Accept:** ship only if users find it delightful and confusion remains low. Otherwise archive the experiment.

### Phase 5 — Productization and research epics

- [ ] Harden the menu-bar application and packaging.
- [ ] Add code signing, notarization, update strategy, and login-item behavior if distribution is pursued.
- [ ] Add per-app profiles through `NSWorkspace.frontmostApplication` and bundle identifiers.
- [ ] Add profile-change safety release and state reset.
- [ ] Research two-hand vocabulary with stable hand identity under occlusion.
- [ ] Use the non-dominant hand as a modifier layer only after one-hand reliability is established.
- [ ] Research a custom gesture recorder; treat classifier generation as an epic, not a small feature.
- [ ] Maintain a decision gate for Python versus Swift.
- [ ] If battery, latency, native UI integration, or packaging exceeds defined limits, port capture and perception to Swift using Vision while preserving gesture, control, configuration, and semantic event contracts where practical.
- [ ] Perform product-name and trademark review for `Aang-Airbender` before any public release.

---

## 5. Engineering standards

### 5.1 Performance budgets

- Requested capture rate: 30 fps initially.
- Software processing budget from available frame to dispatched semantic event: target ≤33 ms at steady state.
- Motion-to-visible-cursor latency: target median <80 ms; record high-percentile latency.
- Frame age must be measured independently of inference time.
- No preview rendering outside debug or calibration workflows.
- No unbounded queues anywhere in the real-time path.

### 5.2 Testing layers

1. **Geometry unit tests**
   - Joint angles
   - Finger extension
   - Palm orientation
   - Palm centroid
   - Hand scale
   - Pinch ratios

2. **FSM sequence tests**
   - Timestamp-based dwell
   - Hysteresis
   - Cooldowns
   - Neutral transitions
   - Hand loss
   - Drag cancellation
   - Reacquisition
   - Exception and shutdown paths

3. **Landmark replay tests**
   - Recorded JSONL sequences
   - Expected states and emitted events
   - Regression tests for every observed false action

4. **Video perception tests**
   - Front light, backlight, low light
   - Distance changes
   - Palm rotation
   - Partial occlusion
   - Fast movement
   - MediaPipe or model upgrades

5. **End-to-end macOS tests**
   - Finder drag and double-click
   - Safari and Chromium scrolling
   - Text selection
   - Window movement and resizing
   - Menu interaction
   - Multiple displays if supported
   - Permission loss and restoration

6. **Feel and reliability tests**
   - Fitts-style target acquisition
   - Stationary jitter
   - Motion-to-visible latency
   - False-action sessions
   - CPU, memory, and battery

### 5.3 Gesture confusion matrix

For every candidate vocabulary, record:

```text
intended gesture × recognised gesture
```

Prioritize dangerous confusions:

```text
right index-point → left click
ordinary right-hand motion → pointer movement
left ordinary motion or fist → left click
right thumb-index pinch → left click
left thumb-index pinch without valid right point → left click
MediaPipe result reordering or duplicate handedness → role swap
left or right role loss during a pending click → partial click
right-hand reacquisition → pointer jump
two left-pinch cycles → explicit double-click semantics
```

A gesture is not promoted into the stable vocabulary until its dangerous confusion rates are acceptable. Before v1 promotion, tests must explicitly cover role/order stability, ordinary motion versus strict right pointing, wrong-hand pinch, role loss during click, non-clicking left-hand poses, pointer reacquisition, and two rapid left-pinch cycles remaining two single clicks.

### 5.4 Configuration discipline

- Every threshold, timing, mapping, gain, macro, and application profile is represented in validated configuration.
- Safe defaults are version-controlled.
- User calibration is stored separately from defaults.
- Unknown fields and invalid values produce clear diagnostics.
- Configuration reload performs `safe_release_all()` and re-enters `DISENGAGED`.

### 5.5 Observability

Structured logs must include:

```text
timestamp
frame_id
state_before
state_after
transition_reason
confidence
active gesture
held inputs
frame age
processing latency
active application profile
```

Debug recording is opt-in and clearly indicated in the HUD.

### 5.6 Safety valve

- Menu-bar quit action.
- Configurable keyboard panic action.
- Signal and exception handlers that call `safe_release_all()`.
- External recovery through ordinary physical mouse, trackpad, Force Quit, or process termination.
- The application must never claim that an in-process shortcut can recover every possible freeze.

---

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Ghost actions during natural gesturing | Movement only during a strict physical-right index-point pose; clicks only from a stable physical-left pinch; elapsed-time stability, fail-closed role assignment, confusion testing |
| Stuck mouse button or modifier | Idempotent `safe_release_all()`, short hand-loss release, terminal-path cleanup, replay tests |
| Gesture overlap | Two-role vocabulary with one action per role, strict predicates, recognition priority, and all other gesture meanings disabled |
| Arm fatigue, “gorilla arm” | Small absolute control box, elbow-on-desk ergonomics, short sessions during tuning, and later evidence-based pointer-mode work outside Phase 1 |
| Lighting and backlight instability | Confidence floors, calibration, exposure guidance, video regression tests, fault-safe suspension |
| Palm rotation breaks 2D geometry | Palm-relative joint angles, world landmarks, robust scale normalization, orientation validity checks |
| OpenCV camera buffering | Latest-frame slot, timestamped frame-age measurement, native AVFoundation fallback |
| MediaPipe Python API or packaging changes | Pin dependency and model versions, early bundle spike, isolate perception contract, Swift decision gate |
| Battery use on fanless MacBook Air | 640×480 input, no normal preview, inference throttling, measured—not assumed—power savings, native fallback if needed |
| Permission mismatch between Terminal and app bundle | Phase 1.5 bundle test, onboarding authorization checks, stable bundle identity |
| Keyboard shortcuts differ by user | Configurable bindings, onboarding validation, profile-aware mappings |
| Rapid pinches accidentally request double-click semantics | Atomic single-click events with click count one and regression tests across representative apps |
| Multiple displays complicate mapping | Default to main-display support until global coordinates and topology-change reset are explicitly implemented and tested |
| Physical mouse and gesture controller fight | Preserve physical input; optionally suspend gesture output after detected physical pointer activity |
| Handedness or result ordering swaps roles | Central mirroring correction, confidence floors, physical-role assignment by label, duplicate-role fail-closed behavior, and reordered-result tests |
| Product name conflict | Treat Aang-Airbender as a working name until name and trademark review |
| Privacy concerns | Local processing, no frame retention by default, explicit recording indicator and controls |

---

## 7. Repo layout

```text
aang-airbender/
├── PLAN.md
├── PROGRESS.md
├── pyproject.toml
├── uv.lock
├── config.yaml
├── config.schema.json
├── models/
│   └── hand_landmarker.task
├── src/aang_airbender/
│   ├── app.py
│   ├── types.py
│   ├── capture/
│   │   ├── base.py
│   │   ├── opencv_capture.py
│   │   └── avfoundation_capture.py
│   ├── perception/
│   │   └── mediapipe_landmarker.py
│   ├── features/
│   │   ├── geometry.py
│   │   └── motion.py
│   ├── gestures/
│   │   ├── poses.py
│   │   ├── recognizers.py
│   │   └── fsm.py
│   ├── control/
│   │   ├── one_euro.py
│   │   ├── mapping.py
│   │   ├── acceleration.py
│   │   └── scroll.py
│   ├── actions/
│   │   ├── mouse.py
│   │   ├── keyboard.py
│   │   ├── media.py
│   │   └── safety.py
│   ├── hud/
│   │   ├── menu_bar.py
│   │   └── overlay.py
│   ├── calibrate/
│   │   └── wizard.py
│   ├── metrics/
│   │   ├── tracing.py
│   │   └── counters.py
│   └── profiles/
│       └── resolver.py
├── tests/
│   ├── unit/
│   │   ├── test_geometry.py
│   │   ├── test_poses.py
│   │   ├── test_fsm.py
│   │   └── test_safety.py
│   ├── replay/
│   │   └── test_landmark_sequences.py
│   ├── integration/
│   │   ├── test_video_fixtures.py
│   │   └── test_action_dispatch.py
│   └── fixtures/
│       ├── landmarks/
│       └── videos/
├── scripts/
│   ├── record_landmarks.py
│   ├── record_video_fixture.py
│   ├── latency_probe.py
│   ├── fitts_test.py
│   ├── jitter_test.py
│   ├── confusion_test.py
│   └── bundle_smoke_test.py
└── docs/
    ├── permissions.md
    ├── architecture.md
    ├── gesture_vocabulary.md
    ├── testing.md
    └── privacy.md
```

---

## 8. Open questions and decision gates

These questions should be answered with measured evidence during the indicated phase rather than by preference alone.

1. **Wake pose — decided 2026-07-18 v1.2:** No wake gesture in Phase 1. Cursor output exists only while a stable physical-right index-point pose is recognised.
2. **Disengagement — decided 2026-07-18 v1.2:** No disengagement gesture in Phase 1. Breaking or losing the right index-point pose freezes output; normal terminal and failure cleanup remain mandatory.
3. **Right-click — decided 2026-07-18 v1.2:** Disabled in Phase 1. Do not retain thumb-middle or two-finger right-click behavior in the active pipeline.
4. **Hand support — decided 2026-07-18 v1.2:** Track up to two hands simultaneously. The physical right hand is pointer-only and the physical left hand is click-only; roles are not interchangeable.
5. **Scroll direction — deferred:** Scrolling is disabled in Phase 1 v1.2. Decide direction only if scrolling returns in a later owner-approved vocabulary.
6. **Pointer mode — decided for Phase 1 v1.2:** Use absolute right-index-fingertip mapping. Evaluate other modes only in a separately approved phase.
7. **Camera backend:** Continue with OpenCV only if measured frame age and packaging are acceptable. Otherwise adopt native AVFoundation.
8. **Display scope:** Support only the main display initially. Add global-display mapping later as an explicitly scoped and tested enhancement, including topology-change reset behavior.
9. **Idle power mode:** Call it inference throttling until battery tests demonstrate real camera or power reduction.
10. **Python decision gate:** After Phase 2, compare latency, battery, crash rate, UI integration, and packaging friction against explicit limits before deciding whether to port capture and perception to Swift.
11. **Name:** Treat Aang-Airbender as a working name until public-name and trademark research is complete.
12. **Distribution:** Decide whether the product is a personal tool, open-source utility, or signed consumer application before investing in notarization, updates, and onboarding polish.

---

## Definition of success for the first public-quality milestone

The first public-quality milestone is reached only when all of the following are true:

- The app launches as a macOS bundle and handles Camera and Accessibility permissions predictably.
- Engagement is obvious and defaults to off.
- Pointer, click, drag, scroll, and clutch are useful without repeated unintended actions.
- Every held OS input is released safely during all tested failure paths.
- Motion-to-visible-cursor latency, jitter, false actions, CPU, and battery behavior are measured and documented.
- Gesture thresholds are calibrated or validated rather than merely copied from defaults.
- Every real-world false action found during testing becomes a replayable regression fixture.
- The user can immediately return to a physical trackpad or mouse without fighting the gesture controller.
