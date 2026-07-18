# Handover Attachments

## Give Codex

Place these files at the repository root before implementation:

1. `CODEX_HANDOVER.md` — author responsibilities, implementation scope, PR workflow, and guardrails.
2. `CODEX_START_PROMPT.txt` — ready-to-paste initial Codex instruction.
3. `PLAN.md` — frozen product and architecture plan.
4. `PHASE_0_CHECKLIST.md` — hardened Phase 0 execution checklist.
5. `PROGRESS.md` — shared implementation and validation record.
6. `.github/PULL_REQUEST_TEMPLATE.md` — mandatory PR evidence package.

Paste `CODEX_START_PROMPT.txt` after the files are in the repository.

## Give Claude after Codex raises the PR

1. `CLAUDE_REVIEW_HANDOVER.md` — independent validation scope and verdict rules.
2. `CLAUDE_REVIEW_PROMPT.txt` — ready-to-paste review instruction.
3. Pull-request URL.
4. Repository access and the exact commit SHA to review.
5. Access to the target Mac when independent hardware reproduction is expected.
6. The same frozen `PLAN.md`, `PHASE_0_CHECKLIST.md`, and updated `PROGRESS.md`.

Paste `CLAUDE_REVIEW_PROMPT.txt` only after Codex marks the PR ready and identifies the exact commit SHA.

## Workflow

```text
Codex implements on feature branch
        ↓
Codex runs tests and updates evidence
        ↓
Codex raises PR → develop
        ↓
Claude independently validates and reviews
        ↓
REQUEST CHANGES / INCOMPLETE EVIDENCE
        ↘ Codex fixes and updates same PR ↗
        ↓
Claude APPROVE
        ↓
User makes final merge decision
```
