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
  - `num_hands=1`
  - `min_hand_detection_confidence=0.7`
  - `min_hand_presence_confidence=0.7`
  - `min_tracking_confidence=0.6`
- Supplies strictly monotonically increasing integer-millisecond timestamps to `detect_async()`.
- Treats live-stream callbacks as asynchronous, tolerant of dropped input frames, and executed in a MediaPipe-controlled callback context.
- The callback performs no UI work, OS-event dispatch, blocking work, or direct FSM mutation. It creates an immutable result and overwrites a single-slot latest-result handoff for the pipeline thread.
- Pins the MediaPipe package and model asset version.
- Emits:

```python
HandState {
    image_landmarks[21],
    world_landmarks[21],
    handedness,
    handedness_score,
    frame_id,
    capture_timestamp,
    mediapipe_timestamp_ms,
    callback_timestamp,
    valid
}
```

- Defines and tests a single mirroring convention. Pointer X mirroring, preview mirroring, and handedness correction must not be handled independently in several modules.

#### `features/`

Calculates reusable geometry and motion once per result:

```python
HandFeatures {
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
- Initial palm center is a weighted centroid of landmarks 0, 5, 9, 13, and 17 rather than only the midpoint of 5 and 17.
- Finger extension is based on joint angles in a palm-relative coordinate system, not only fingertip Y-position.
- `hand_scale` must remain usable under moderate palm rotation. Start with world-space `dist(5,17)` and evaluate a robust combined scale during calibration.

#### `gestures/`

- Contains stateless pose predicates plus stateful recognizers and a master FSM.
- Pose predicates are strict and mutually exclusive where possible.
- Gesture transitions use elapsed monotonic time.
- Emits intentions, not screen coordinates or OS calls:

```python
POINT(anchor)
PINCH_START(kind)
PINCH_END(kind)
SCROLL_START(origin)
SCROLL_UPDATE(velocity)
SCROLL_END
CLUTCH_ON
CLUTCH_OFF
ENGAGE_REQUEST
MACRO_REQUEST(id)
CANCEL
```

- `UNKNOWN` emits nothing.
- Dangerous recognitions are prioritized over cosmetic recognitions: safety, active-button release, active continuous gesture, pinch, scroll, point.

#### `control/`

- Applies One Euro filtering or another validated filter to pointer anchors.
- Converts gesture intent into semantic OS events.
- Supports absolute mapping first, then relative movement with acceleration and clutch.
- Owns pointer acceleration, dead zones, display mapping, scroll gain, scroll momentum, and mode baselines.
- Re-establishes baselines whenever entering pointer, scroll, or relative-control modes to avoid jumps.
- Emits:

```python
POINTER_MOVE(screen_x, screen_y)
LEFT_DOWN
LEFT_UP
RIGHT_CLICK
SCROLL(pixel_dx, pixel_dy)
KEY_CHORD(keys)
MEDIA_ACTION(action)
```

#### `actions/`

- Thin Quartz and AppKit dispatch layer.
- Knows nothing about hands.
- Posts mouse movement, button, pixel-scroll, keyboard, and supported media events.
- Tracks locally held buttons and modifier keys.
- Implements idempotent `safe_release_all()`.
- Calls `safe_release_all()` on every abnormal or terminal path.
- Tests double-click behavior explicitly instead of assuming two ordinary clicks are always interpreted identically by every application.

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
4. Pending clicks are cancelled when confidence drops or the recognised hand becomes invalid.
5. A newly reacquired hand must remain stable briefly before cursor movement resumes.
6. Physical trackpad and mouse input always remain available.
7. The panic mechanism must include an external recovery path. A keyboard shortcut handled only by the same frozen process is not sufficient by itself.

### 2.3 Master state machine

```text
DISENGAGED
    └─ wake pose stable for configured dwell ─▶ ARMING
ARMING
    ├─ dwell completes with valid confidence ─▶ ENGAGED
    └─ pose breaks / confidence falls ─────────▶ DISENGAGED
ENGAGED
    ├─ brief tracking loss ────────────────────▶ SUSPENDED
    ├─ no hand for configured timeout ─────────▶ DISENGAGED
    ├─ explicit HUD or keyboard action ────────▶ DISENGAGED
    └─ fatal subsystem error ──────────────────▶ FAULT
SUSPENDED
    ├─ hand reacquired and stabilised ─────────▶ ENGAGED
    ├─ timeout expires ────────────────────────▶ DISENGAGED
    └─ fatal subsystem error ──────────────────▶ FAULT
FAULT
    └─ user restarts or explicitly resets after safe release
```

Initial timing hypotheses:

```text
wake dwell:                  800–1,000 ms
pose stability:              80–120 ms
short hand-loss grace:       150–250 ms
full no-hand disengagement:  2–3 s
reacquisition stability:     150–250 ms
```

Within `ENGAGED`:

```text
NEUTRAL
POINTING
PINCH_PENDING
TWO_FINGER_PENDING
DRAGGING
SCROLLING
RIGHT_CLICK_COMMITTED
CLUTCHED
UNKNOWN
```

Rules:

- While dragging, only pinch release, safety cancellation, and disengagement may interrupt the drag.
- Scroll and relative-pointer modes establish a fresh baseline when entered.
- `UNKNOWN` never dispatches an action.
- Discrete gestures return through neutral unless an explicit transition is tested and allowed.
- The wake-pose meaning is recognised only while disengaged or arming. While engaged, a relaxed open hand may belong to the pointer-pose family without toggling engagement.

---

## 3. Gesture vocabulary — v1.1 candidate

The vocabulary is an initial candidate, not permanently locked. It becomes v1 only after confusion-matrix testing confirms acceptable safety and usability.

| Pose, initially right hand | Strict initial detection | Action |
|---|---|---|
| Pointer-pose family | Valid tracked hand with no higher-priority command pose; confidence valid | Move pointer using the One Euro-filtered, weighted palm centroid of landmarks 0, 5, 9, 13, and 17; never use the index fingertip as the pointer anchor |
| Thumb–index pinch | Index pinch ratio enters closed threshold while middle-pinch ratio remains clearly open | Left button down; release threshold emits left button up |
| Held thumb–index pinch | A recognised thumb–index pinch remains closed | Drag by keeping the left button down; there is no separate drag gesture |
| Thumb–middle pinch | Middle pinch ratio enters closed threshold while the index-pinch ratio remains clearly open | Arm right-click; emit exactly once on release, then require neutral |
| Two-finger scroll pose | Index and middle extended; ring and pinky curled; fingers sufficiently separated | Enter `TWO_FINGER_PENDING`; commit only when cumulative displacement or filtered velocity exceeds the configured threshold; scroll never moves the pointer |
| Fist | All four fingers curled for configured dwell, with pinch recognition suppressed while the fist forms | Release any held input, then clutch: pointer frozen; fist release establishes a new relative baseline |
| Open palm, palm facing camera | All digits extended, stable, valid orientation; engagement meaning recognised only while disengaged | Engage |
| Thumbs-down | Thumb extended downward with the other fingers curled, stable for the configured 1 s dwell | Disengage; the full no-hand timeout remains a second disengagement path |
| Hand loss | Recognised hand absent | After the short configured grace period, release all held inputs; after the full configured timeout, disengage |
| Two-finger stillness dwell, disabled fallback | Two-finger scroll pose remains inside a stillness radius for the configured dwell, and the fallback is explicitly enabled in configuration | Right-click once, then require neutral; disabled by default and not part of the v1.1 vocabulary |

Cross-pinch exclusion is mandatory: an index pinch is valid only while the middle pinch is clearly open, a middle pinch is valid only while the index pinch is clearly open, and the ambiguous zone emits neither action.

### 3.1 Two-finger scroll arbitration

```text
NEUTRAL
    └─ stable two-finger pose ─▶ TWO_FINGER_PENDING
TWO_FINGER_PENDING
    ├─ cumulative displacement or filtered velocity exceeds threshold ─▶ SCROLLING
    └─ pose breaks before commitment ──────────────────────────────────▶ NEUTRAL
```

- Two fingers at rest do nothing.
- Committing to `SCROLLING` locks the episode to scrolling until the pose ends.
- Scroll entry uses both cumulative displacement and filtered velocity so a deliberately slow scroll can still commit without assigning stillness another default meaning.
- The two-finger stillness-dwell right-click recognizer remains available only as a disabled configuration fallback. When explicitly enabled, it retains branch locking and cannot transition directly between right-click and scrolling.

### 3.2 Pinch hysteresis

Initial normalized thresholds:

```text
closed: ratio < 0.35
open:   ratio > 0.50
```

The interval between them is a dead zone. Calibration may recommend per-user values. No fixed threshold is considered final until measured across distance, lighting, hand rotation, and both supported hands.

### 3.3 Gesture priority

```text
fault and emergency handling
→ release of active held inputs
→ explicit disengagement dwell
→ fist recognition, including release-before-clutch
→ active drag continuation or pinch release
→ active scroll continuation or end
→ active two-finger episode branch lock
→ cross-exclusive thumb–index and thumb–middle pinch recognizers
→ two-finger pending arbitration
→ point recognizer
→ unknown
```

### 3.4 Design invariants

- Pinch metrics are normalized for hand size and camera distance.
- Hysteresis prevents boundary flicker.
- Cross-pinch exclusion makes the ambiguous index/middle pinch zone non-actionable.
- Pointer anchoring uses the weighted palm centroid of landmarks 0, 5, 9, 13, and 17, not a pinching fingertip.
- Pointer anchoring is One Euro filtered.
- All gesture dwells, grace periods, and stability checks use monotonic elapsed time and validated configuration values.
- Engagement and disengagement use distinct interaction paths.
- Similar gestures are not assigned to different destructive actions without confusion testing.
- Fist formation suppresses pinch recognition and releases held inputs before entering clutch.
- Fist release re-baselines the pointer before movement resumes.
- A held thumb–index pinch is the drag state; drag has no separate gesture.
- Thumb–middle pinch emits right-click only on release and must return through neutral.
- Two-finger stillness never emits an action in the default vocabulary; scroll requires configured displacement or velocity and never moves the pointer.
- Pointer, scroll, and command poses are mutually exclusive whenever possible.
- Natural-scrolling direction is a first-class configuration option.

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

### Phase 1 — Core five and safety (3–5 focused days)

**Goal:** provide basic trackpad replacement with safe failure behavior.

- [ ] Record a 30-second landmark fixture and a short video fixture using `scripts/record_landmarks.py` and `scripts/record_video_fixture.py`.
- [ ] Implement `HandState`, `HandFeatures`, `GestureIntent`, and `SemanticEvent` types.
- [ ] Implement palm-relative finger-angle classification.
- [ ] Add strict index-point, relaxed-open-hand pointer, two-finger, fist, wake-palm, and pinch predicates.
- [ ] Add fixture-based unit tests for geometry and pose classification.
- [ ] Implement the top-level engagement FSM and inner gesture FSM with timestamp-based transitions.
- [ ] Implement left-pinch hysteresis and cross-pinch exclusion.
- [ ] Implement `TWO_FINGER_PENDING` arbitration for motion-gated scrolling; keep the stationary two-finger right-click fallback disabled by default.
- [ ] Add One Euro filtering to the palm centroid; start with `min_cutoff=1.0`, `beta=0.007`, then tune empirically.
- [ ] Implement absolute mapping from a configurable central control box to the active display region.
- [ ] Define mirroring and handedness behavior in one module and test it.
- [ ] Emit real left-button down and up events; implement safe drag release.
- [ ] Implement right-click once on cross-exclusive thumb–middle pinch release, then require neutral.
- [ ] Implement pixel scroll without momentum initially.
- [ ] Implement clutch and fresh-baseline behavior; fist has no disengagement meaning in v1.
- [ ] Implement `safe_release_all()` and call it from all terminal and error paths.
- [ ] Add `config.yaml` plus schema validation. No untracked magic thresholds.
- [ ] Add `--debug` rendering of landmarks, pose, confidence, FSM state, and timing every Nth frame; off by default.
- [ ] Add structured state-transition logs and false-action counters.

**Accept:**

- Browse, open applications, drag a file, and scroll a page without touching the trackpad for five minutes.
- Targets at least 44 display-coordinate units wide are acquired reliably in absolute mode.
- Zero false clicks during 10 minutes of normal pointing.
- Fewer than one false click during a 30-minute adversarial test containing normal conversational hand motion.
- Hand loss during drag releases the mouse within the short grace period.
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
point → left click
scroll → left click
thumb–index pinch ↔ thumb–middle pinch (wrong-button click)
fist formation → pinch or click
fist clutch → thumbs-down disengagement
natural hand drop → thumbs-down disengagement
ordinary hand motion → engage
brief hand loss → unintended disengage
tracking loss during drag
reacquisition → pointer jump
two thumb–index pinch cycles → application-level double-click
swipe → unintended system action
```

A gesture is not promoted into the stable vocabulary until its dangerous confusion rates are acceptable. Before v1 promotion, tests must explicitly cover the thumb–index versus thumb–middle pair, false pinch during fist formation, fist versus thumbs-down, natural hand drop versus thumbs-down, and application-level double-click behavior from two thumb–index pinch cycles.

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
| Ghost actions during natural gesturing | Disengaged-by-default operation, rare wake pose, strict predicates, elapsed-time dwell, neutral transitions, cooldowns, confusion testing |
| Stuck mouse button or modifier | Idempotent `safe_release_all()`, short hand-loss release, terminal-path cleanup, replay tests |
| Gesture overlap | Mutually exclusive predicates, recognition priority, cross-pinch exclusion, two-finger pending arbitration with branch locking, provisional vocabulary |
| Arm fatigue, “gorilla arm” | Relative mode, clutch, low-amplitude acceleration, elbow-on-desk ergonomics, short sessions during tuning |
| Lighting and backlight instability | Confidence floors, calibration, exposure guidance, video regression tests, fault-safe suspension |
| Palm rotation breaks 2D geometry | Palm-relative joint angles, world landmarks, robust scale normalization, orientation validity checks |
| OpenCV camera buffering | Latest-frame slot, timestamped frame-age measurement, native AVFoundation fallback |
| MediaPipe Python API or packaging changes | Pin dependency and model versions, early bundle spike, isolate perception contract, Swift decision gate |
| Battery use on fanless MacBook Air | 640×480 input, no normal preview, inference throttling, measured—not assumed—power savings, native fallback if needed |
| Permission mismatch between Terminal and app bundle | Phase 1.5 bundle test, onboarding authorization checks, stable bundle identity |
| Keyboard shortcuts differ by user | Configurable bindings, onboarding validation, profile-aware mappings |
| Double-click semantics vary by application | Explicit click-state and timing tests across representative apps |
| Multiple displays complicate mapping | Default to main-display support until global coordinates and topology-change reset are explicitly implemented and tested |
| Physical mouse and gesture controller fight | Preserve physical input; optionally suspend gesture output after detected physical pointer activity |
| Right-click conflicts with left click or scroll | Cross-pinch exclusion; two-finger motion-versus-stillness arbitration; require neutral after right-click; keep thumb–middle pinch experimental |
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

1. **Wake pose:** Is open palm rare enough in actual use, or should engagement use a more distinctive pose or HUD action? Decide through adversarial testing in Phase 1.
2. **Disengagement — decided 2026-07-18:** Use a thumbs-down pose with a configured 1 s monotonic dwell as the explicit gesture path. Keep the configured 2–3 s no-hand timeout as the second path; the short hand-loss grace still releases held inputs first. Fist remains clutch only.
3. **Right-click — decided 2026-07-18:** Use cross-exclusive thumb–middle pinch and emit one right-click on release, followed by neutral. Two fingers are scroll-only in the default vocabulary; retain stationary two-finger dwell only as a disabled configuration fallback.
4. **Hand support:** Start with right hand for reduced complexity. Add handedness-agnostic support only after mirroring and geometry tests pass.
5. **Scroll direction:** Provide a natural-scrolling configuration flag from the first implementation.
6. **Pointer mode:** Keep both absolute and relative modes; select the default after Fitts, fatigue, and reliability testing.
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
