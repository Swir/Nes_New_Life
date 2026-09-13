# Capture → Gate A Review Director

The Capture Review Director is the shortest supported operator path from one real local MesenCE gameplay session to a fingerprint-bound Gate A review decision.

It deliberately keeps the evidence boundary strict: the ROM, save states, capture PNG/JPG pixels, emulator binaries and commercial assets stay local. Only metadata produced by the existing capture/evidence toolchain is consumed by the director.

## One-click path

Run:

```text
windows\Capture_Review_Director.bat
```

The launcher performs, in order:

1. the existing next-best single capture loop unless `-SkipCapture` is supplied;
2. refreshed Capture Integrity / gap / route / Local Capture Bridge / acceptance / Gate A Evidence Matrix outputs through that loop;
3. Gate A Review & Attestation state generation for the exact current capture fingerprint;
4. a single `Capture Review Director` dashboard that classifies the next action as `REVIEW_REQUIRED`, `CAPTURE_WORK_REQUIRED`, or `GATE_A_REVIEW_COMPLETE`;
5. for each evidence-ready criterion, an explicit local attestation prompt requiring the exact token `VERIFIED_GATE_A` after real MesenCE gameplay review;
6. when all 12 Gate A criteria are explicitly verified for the same fingerprint, the existing fail-closed ROADMAP Patch Director is refreshed.

No ROADMAP file is edited automatically.

## Fail-closed rules

`capture_review_director.py` rejects the handoff unless:

- the Gate A review schema is exactly `swir.project002.gate-a-review-attestation.v1`;
- the handoff contains exactly 12 unique Gate A criteria;
- every criterion belongs to the exact top-level capture fingerprint;
- reviewable or verified criteria contain a source fingerprint;
- review status is one of `AWAITING_HUMAN_ATTESTATION`, `VERIFIED_GATE_A`, or `BLOCKED_BY_EVIDENCE`.

The director never creates attestations itself and never upgrades blocked evidence to reviewable evidence.

## Local outputs

`Reports/CaptureReviewDirector/` contains only metadata/UI output:

- `CAPTURE_REVIEW_DIRECTOR.json`
- `CAPTURE_REVIEW_DIRECTOR.html`

These files provide one queue and one `DO THIS NEXT` action. They do not contain capture images or ROM data.

## Authoritative Studio

Authoritative Production Studio exposes this workflow as the preferred Gate A path. The older next-best capture and Gate A review launchers remain available as lower-level tools, but the director is the fastest default because it removes the manual handoff between them.

## ROADMAP meaning

This workflow is an accelerator, not completion evidence by itself. The Project #002 ROADMAP percentage still measures only the 52 authoritative Gate A–D checkboxes. A Gate A checkbox can move only after real local evidence is evidence-ready, explicitly reviewed, attested for the exact capture fingerprint, projected by the ROADMAP Patch Director, reviewed in a repository PR, and accepted with green CI.
