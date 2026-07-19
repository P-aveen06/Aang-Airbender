# Aang-Airbender pitch-deck content

## Communication job

By the end, MVP judges and potential collaborators should believe Aang-Airbender is a delightful,
credible spatial-computing prototype because it already performs useful Mac actions and its hardest
engineering decisions center on freshness, ambiguity, and safe recovery.

This file supplies content only. Claude should build the deck in an OpenAI-inspired editorial style
without copying OpenAI marks or implying affiliation.

## Deck-wide direction

- 16:9, ten slides.
- Warm off-white canvas, near-black typography, restrained green accent, fine gray rules.
- One composition per slide; avoid dense card grids and dashboard chrome.
- Use large takeaway titles. Keep visible copy sparse enough for live presentation.
- Prefer product frames, the camera overlay, gesture stills, and one latency comparison over stock
  images.
- Do not use private validation video or private landmark fixtures without explicit owner approval.

## Slide 1 — Title

Visible copy:

> # Aang-Airbender
>
> Your Mac, at arm's length.
>
> Local hand-gesture control for macOS

Small footer:

> MVP prototype · Apple Silicon macOS

Visual direction: minimal. One cropped hand silhouette or a small bottom-left camera-overlay frame.

## Slide 2 — The mouse assumes your hand is already on the desk

Visible copy:

> Presenting. Recording. Cooking. Moving around a room.
> The screen is visible—but the controls are out of reach.

> Aang-Airbender explores a simple question:
> **Can ordinary Mac control move into the space in front of us?**

Speaker intent, not visible: establish the problem as “distance from the input surface,” not a claim
that every mouse or accessibility workflow should be replaced.

## Slide 3 — A deliberate hand pose becomes a Mac action

Visible copy:

> **Palm** moves the cursor
> **Thumb + index** clicks and drags
> **Thumb + middle** context-clicks
> **Two fingers** scroll
> **Fist** clutches
> **Thumbs-down** disengages

Closing line:

> A compact vocabulary is easier to learn—and safer to distinguish.

Visual direction: one hand sequence across the slide, not six boxed UI cards.

## Slide 4 — The product is best understood in motion

Visible copy:

> Move. Pinch. Scroll. Reposition. Let go.

> The bottom-left camera overlay keeps the cause visible while macOS shows the effect.

Visual direction: make this the demo slide. Use the actual MVP video or a large still with a play
button. If presenting live, place only a short fallback clip here.

## Slide 5 — Useful wherever the keyboard is one step too far away

Visible copy:

> **Creators** can control a recording without reaching across the frame.
> **Presenters** can navigate while staying with the audience.
> **Voice-first users** can pair spatial control with dictation and commands.
> **Accessibility exploration** can test new input paths without specialized hardware.

Closing line:

> The goal is not to remove every mouse. It is to make more moments controllable.

Speaker intent, not visible: avoid medical or universal-accessibility claims until user research and
formal accessibility testing exist.

## Slide 6 — Trust is the real interaction model

Visible copy:

> **Fresh beats queued.** Only one inference request is in flight.
> **Ambiguity means nothing happens.** Similar pinches fail closed.
> **Release is unconditional.** Hand loss, failure, shutdown, and clutch protect held input.

Bottom line:

> A gesture controller earns trust by knowing when not to act.

Visual direction: a restrained three-beat composition. Avoid a complex state-machine diagram.

## Slide 7 — One latency bug explained three missed clicks

Visible copy:

> The recognizer saw all five pinches.
> The clicks still landed on stale cursor positions.

Large comparison:

> **2,015.87 ms** → **51.71 ms**
> p95 capture-to-Quartz latency in the matching debug validation

Result line:

> Latest-only inference restored **5 / 5** browser click registration.

Visual direction: one clean before/after line or two large numerals. Do not add a dense metrics
dashboard.

## Slide 8 — Twenty hours turned failures into product decisions

Visible copy:

> **A cursor moved.** The end-to-end Mac path worked.
> **A stricter two-hand design failed the human test.** Palm control returned.
> **Clicks missed.** Freshness—not thresholds—was the first root cause.
> **Scroll felt jerky.** Fractional motion and continuity fixed the feel.
> **Fist release jumped.** A fresh baseline made clutching predictable.
> **Pinches overlapped.** Replays and synchronized video preserved fail-closed safety.

Closing line:

> Every uncomfortable test made the vocabulary smaller, clearer, or safer.

Visual direction: one chronological line with six short beats. Do not imply exact hour-by-hour
timing; “twenty hours” describes the overall build session.

## Slide 9 — The MVP is local, observable, and ready to demonstrate

Visible copy:

> Camera → MediaPipe → gesture FSM → filtered control → Quartz

> - Local camera processing
> - Click, drag, context-click, scroll, clutch, and disengage
> - Mirrored, rounded, click-through camera overlay
> - Safe-release checks and replayable gesture tests
> - 89 passing host-compatible automated tests

Footnote:

> Phase 1's broader acceptance checklist was stopped before completion when work moved to MVP demo
> preparation; this is a working prototype, not a finished accessibility product.

## Slide 10 — The next release makes spatial control easier to reach

Visible copy:

> Underway now: **bundle Aang-Airbender as a distributable macOS app**

> Next gesture: **thumbs-up → Whisper Flow shortcut**

> Then calibration, guided permission onboarding, broader false-action testing, and voice-command
> workflows.

Closing statement:

> Aang-Airbender is a working argument that computers can meet us beyond the desk—if movement,
> restraint, and recovery are designed together.

Final CTA:

> Watch the demo · Explore the source · Continue the build

Visual direction: resolve the opening question. Use a clean closing product frame, not a generic
“Thank you” slide.

## Evidence and wording guardrails for Claude

- The product is an MVP/prototype; never call it production-ready or fully validated.
- The target-Mac log supports the 2,015.87 ms to 51.71 ms latency comparison and the five-click
  browser result.
- The current host-compatible suite reports 89 passing tests with the official MediaPipe model
  smoke test deselected in the Codex-hosted process.
- Safe release passed on the Accessibility-trusted target Mac after controlled failure and normal
  shutdown.
- Camera processing is local and recording is opt-in. Do not say “no data is ever stored” because
  the tool intentionally supports explicitly authorized diagnostic fixture recording.
- The thumbs-up shortcut is planned but inactive until the owner supplies the exact key and
  modifiers.
- macOS app bundling is underway, but no signed or notarized download is available yet.
- Add “Independent project; not affiliated with OpenAI” wherever the chosen visual treatment could
  otherwise suggest affiliation.
