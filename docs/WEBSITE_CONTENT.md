# Aang-Airbender website content

## Communication job

By the end, MVP judges and early users should understand what Aang-Airbender does, feel the delight
of controlling a Mac through deliberate hand movement, and trust that the prototype was engineered
around safety and responsiveness rather than a flashy but brittle gesture demo.

This is content and implementation direction for Claude. It is not a request to copy OpenAI's
website or imply an OpenAI affiliation. Use an OpenAI-inspired editorial treatment: restrained,
spacious, precise, warm, and mostly monochrome, with one quiet green accent.

## Global voice

- Clear, curious, and human.
- Confident about what works; candid that this is an MVP.
- Short sentences over inflated AI language.
- Let the journey carry the joy. Do not add generic claims such as “revolutionary,” “seamless,” or
  “the future of computing.”
- Product name in display copy: **Aang-Airbender**.
- One-line description: **A local macOS controller that turns deliberate hand gestures into cursor,
  click, drag, scroll, and safety actions.**

## Recommended page flow

### 1. Hero — make the product understandable in five seconds

Eyebrow:

> A spatial controller for macOS

Headline:

> Your Mac, at arm's length.

Body:

> Move the pointer with your palm. Pinch to click or drag. Raise two fingers to scroll.
> Aang-Airbender turns a small set of deliberate hand poses into everyday Mac control.

Primary CTA:

> Watch the demo

Secondary CTA:

> Follow the 20-hour journey

Trust line:

> Runs locally on macOS · No automatic recording · Unknown gestures do nothing

Visual direction for Claude: use the product's compact camera overlay as the hero motif. Keep the
hero mostly typographic. A slow cursor trail or a single hand-landmark treatment can add motion, but
do not make the page look like a generic AI dashboard.

### 2. Interaction — show the language before explaining the machinery

Section title:

> A small language for everyday control.

Intro:

> The vocabulary stays intentionally compact. Each pose has one job, and ambiguous poses fail
> closed instead of guessing.

Gesture copy:

| Gesture | Visible label | Supporting copy |
|---|---|---|
| Open palm | Wake | Hold a facing palm briefly to engage the controller. |
| Palm movement | Move | The weighted center of the palm guides the cursor—not a shaky fingertip. |
| Thumb + index | Click and drag | Pinch to press. Open to release. Keep holding to drag. |
| Thumb + middle | Context click | Hold a clear middle pinch, then release for one right click. |
| Two fingers + motion | Scroll | Vertical motion scrolls; holding two fingers still does nothing. |
| Fist | Clutch | Freeze the pointer and release any held input before repositioning your hand. |
| Thumbs-down | Sleep | Hold to disengage deliberately. Natural hand loss remains a separate safety path. |

Closing line:

> One pose. One meaning. No action when the intent is unclear.

### 3. Product idea — explain why this is more than a webcam trick

Section title:

> The hard part was never drawing landmarks.

Body:

> A gesture demo can look convincing while acting on an old frame, clicking the wrong target, or
> leaving a button held after the hand disappears. Aang-Airbender treats freshness and release
> behavior as product features. Camera capture stays independent. Only one inference request can be
> in flight. New frames replace stale work instead of joining a queue. Every failure and shutdown
> path releases owned mouse state.

Evidence callouts:

> **2,015.87 ms → 51.71 ms**
> Debug-run p95 capture-to-Quartz latency after replacing the inference backlog with latest-only
> scheduling.

> **5 / 5 clicks registered**
> Browser target check after the freshness correction, with balanced Quartz down/up cycles.

> **Safe release verified**
> Controlled failure and normal shutdown both ended with the combined-session left button up.

Footnote:

> Evidence comes from the target-Mac validation log. Phase 1's broader acceptance checklist was
> deliberately stopped before completion when the project moved into MVP demo preparation.

### 4. Architecture — make the system legible

Section title:

> Camera in. Intent out.

Pipeline labels:

> AVFoundation camera → MediaPipe Hand Landmarker → palm-relative features → monotonic gesture FSM
> → filtered control → Quartz events

Supporting copy:

> Frames are processed locally. The finite-state machine separates a pose candidate from an action,
> enforces dwell and release rules, and cancels conflicting gestures. The control layer smooths palm
> movement, preserves fractional scroll motion, and re-baselines the pointer after clutching so the
> cursor does not jump.

Three architecture principles:

> **Fresh beats queued.** The newest usable frame wins.
> **Ambiguity means no action.** Similar pinches never compete by array order or guesswork.
> **Release is unconditional.** Failure, shutdown, hand loss, and clutch transitions all protect
> held input.

### 5. Journey — the joyful 20-hour build story

Section title:

> Twenty hours. One stubborn cursor. Better questions every round.

Intro:

> The prototype did not arrive in a straight line. It moved forward through recordings, failed
> assumptions, owner feedback, and small corrections that made the interaction feel more honest.

Journey node 1:

> **First, make one frame move one cursor.**
> The technical spike proved the complete Mac path: camera permission, live hand landmarks, palm
> geometry, filtered screen mapping, and Quartz input. The first success was wonderfully simple—the
> cursor followed a raised palm.

Journey node 2:

> **Then teach the hand a compact vocabulary.**
> Pinch became click-and-drag. Two fingers became motion-gated scroll. A fist became a clutch.
> Thumbs-down became deliberate disengagement. Safety rules were designed alongside the gestures,
> not added afterward.

Journey node 3:

> **We tried a stricter two-hand idea. The human rejected it.**
> A right-index pointer plus left-hand pinch looked precise on paper and felt wrong in practice.
> The experiment was reverted. Palm control returned because the user's body—not the spec—made the
> final decision.

Journey node 4:

> **Five clicks were detected. Only three landed.**
> The first suspect was pinch recognition. The evidence showed something else: MediaPipe requests
> were queuing, so correct clicks arrived at stale cursor positions. Latest-only inference cut the
> p95 software path from more than two seconds to about 52 milliseconds in the matching debug test.

Journey node 5:

> **Scroll worked, but it did not feel alive.**
> Fractional motion was being rounded away, and one-frame pose dropouts kept restarting the scroll
> state. Accumulated pixel residuals and a short continuity grace made small movement respond,
> remain continuous, and stop without phantom motion.

Journey node 6:

> **The fist froze the pointer—and taught it where to return.**
> Releasing a clutch initially caused a cursor jump. A fresh baseline now preserves the last cursor
> position and resumes from deliberate hand displacement.

Journey node 7:

> **Right-click became a lesson in honesty.**
> Thumb-index and thumb-middle contacts can look nearly identical to a camera. Replays, synchronized
> video, hysteresis, dwell, and release ordering improved recognition without weakening the rule
> that an ambiguous contact must emit nothing.

Journey node 8:

> **Finally, make the machine visible.**
> The MVP now carries a small mirrored, rounded, click-through camera overlay in the bottom-left.
> It makes the demo legible while the controller continues working underneath.

Journey closer:

> The result is not a finished replacement for the mouse. It is a working argument that spatial Mac
> control can feel understandable when responsiveness, restraint, and recovery are designed
> together.

### 6. Current state and next gesture

Section title:

> The MVP works. The next step gives it a voice.

Current-state copy:

> Today, Aang-Airbender can engage, point, click, drag, context-click, scroll, clutch, disengage, and
> recover safely from hand loss or shutdown. It runs as a local Python application on Apple Silicon
> macOS and exposes its camera view through a compact always-on overlay.

Next-step copy:

> A deliberate thumbs-up will trigger a user-selected Whisper Flow shortcut. The exact key
> combination is still being chosen, so the current build emits no guessed keyboard action.

Roadmap labels:

- Thumbs-up → Whisper Flow shortcut
- Per-user calibration and pointer feel
- Menu-bar packaging and permission onboarding
- Broader gesture-confusion and false-action testing
- Voice and command workflows beyond pointer control

### 7. Final node — demo video payoff

Section title:

> Now watch the interface disappear.

Body:

> One camera. One hand. One Mac. See the palm move the cursor, pinches become clicks, two fingers
> scroll, and the fist pause everything long enough to reposition.

Video label:

> Aang-Airbender MVP demo

Caption under video:

> Recorded on the target M2 MacBook Air. The bottom-left camera overlay shows the hand pose driving
> each visible macOS action.

Final CTA row:

> **View the source on GitHub**
> **Read the build journey**

Final line:

> Move with intent. Let the computer meet you halfway.

## Demo-video content order

This is production guidance, not visible website copy. Use a 60–90 second video and keep the compact
camera overlay visible throughout:

1. Open palm engages.
2. Palm moves the cursor across the screen.
3. Thumb-index pinch opens an application or link.
4. Held thumb-index pinch drags an object and releases it.
5. Thumb-middle pinch opens a context menu once.
6. Two fingers scroll a page smoothly, then stop.
7. Fist clutches; hand repositions; opening resumes without a cursor jump.
8. Thumbs-down disengages.
9. End card: “Aang-Airbender — Your Mac, at arm's length.”

Do not use any private validation recording as the public demo unless the owner separately approves
that exact file. Add captions; the page must remain understandable with audio muted.

## Visual and interaction direction for Claude

- Warm off-white background, near-black text, muted gray rules, and one restrained green accent.
- Large editorial typography, generous negative space, thin dividers, and subtle grid alignment.
- Avoid glassmorphism, glowing gradients, chatbot bubbles, dashboard cards, or OpenAI logos.
- Use one continuous vertical story. The journey can follow a fine line that bends gently between
  nodes; keep it editorial rather than game-like.
- Animate only to explain causality: palm movement, newest-frame replacement, state transitions,
  and the journey line. Respect reduced-motion settings.
- Keep the demo video as the final major content block. Do not autoplay with sound.
- Include a visible “Independent project; not affiliated with OpenAI” footer note.
- Mobile order must preserve the same narrative and keep the demo controls accessible.
