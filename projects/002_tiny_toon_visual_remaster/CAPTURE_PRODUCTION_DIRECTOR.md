# Capture Production Director — Project #002

`capture_production_director.py` is the shortest safe path from a local MesenCE capture into the HD art pipeline.

It does **not** replace Guided Capture Marathon and it never marks Gate A–D complete. Its purpose is to remove manual orchestration after a capture session while keeping the same fingerprint-bound evidence rules.

## Windows one-click

Run:

```text
windows/Capture_To_Art_Pipeline.bat
```

Select the current MesenCE HD Pack capture and, when available, the previous accepted capture. The pipeline then performs fresh Capture Coverage Acceptance before any production state can be mutated.

## Decisions

The director always emits two explicit decisions.

### Capture decision

- `FIX_REGRESSION` — current capture lost previously observed coverage or puts verified mission evidence at risk. Production is blocked.
- `FIX_CAPTURE_INTEGRITY` — structural/integrity/provenance evidence is unsafe. Production is blocked.
- `CAPTURE_MORE` — capture is structurally safe but authoritative missions/groups remain incomplete.
- `READY_FOR_GATE_A_REVIEW` — all hard metadata/provenance checks are clean. Real MesenCE gameplay evidence must still be reviewed manually before any ROADMAP checkbox changes.

### Production decision

- `BLOCK_PRODUCTION` — do not touch `ART_QUEUE.csv` or `MasterWorkspace`.
- `SAFE_INCREMENTAL_ART` — incomplete but safe capture may feed incremental art production while Gate A remains blocked.
- `FULL_CAPTURE_READY` — full capture acceptance is ready for manual Gate A evidence review and safe production promotion.

With `--promote-safe`, safe modes call the existing acceptance-gated Capture Promotion Director. Unsafe modes stop before production sync. `--create-sprint` can additionally prepare the next art sprint after a safe promotion.

## Reports

The director writes:

```text
Reports/CaptureProductionDirector/CAPTURE_PRODUCTION_DIRECTOR.json
Reports/CaptureProductionDirector/CAPTURE_PRODUCTION_DIRECTOR.html
```

The dashboard exposes the exact capture decision, production decision, fingerprint, hard blockers and one `DO THIS NEXT` instruction.

Reports are metadata-only. They intentionally exclude ROM bytes, save states, capture pixels, emulator binaries and absolute local paths.

## Recommended operating loop

```text
Guided_Capture_Marathon.bat
  ↓
Local Capture Bridge / fingerprint-bound evidence
  ↓
Capture_To_Art_Pipeline.bat
  ├─ FIX_REGRESSION → repair capture first
  ├─ FIX_CAPTURE_INTEGRITY → repair evidence/capture first
  ├─ CAPTURE_MORE + SAFE_INCREMENTAL_ART → continue art safely, then capture more
  └─ READY_FOR_GATE_A_REVIEW → manually verify gameplay evidence before Gate A changes
```

This keeps the original ROM as the authoritative source of gameplay, physics, levels, timing and logic while accelerating only the HD presentation workflow.
