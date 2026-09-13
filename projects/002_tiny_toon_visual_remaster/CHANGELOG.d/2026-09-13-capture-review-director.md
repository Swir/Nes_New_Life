# Project #002 changelog fragment — Capture → Gate A Review Director

- added `capture_review_director.py`, a fingerprint-bound single-queue director over the existing Gate A review handoff
- added `windows/Capture_Review_Director.bat/.ps1` to chain the next-best real MesenCE capture, refreshed evidence, explicit Gate A review and ROADMAP patch preview into one operator path
- fail-closed validation requires exactly 12 unique Gate A criteria, exact current capture fingerprints and source fingerprints for every reviewable/verified row
- the director never records attestations, never upgrades blocked evidence and never edits ROADMAP files automatically
- added focused tests for review priority, blocked capture handoff, all-verified handoff, stale fingerprint rejection and metadata-only output
- documented the one-click workflow and exposed it as the preferred Gate A path in Authoritative Production Studio
- ROADMAP remains unchanged at 0/52 = 0.0% because CI has no real local MesenCE gameplay evidence
