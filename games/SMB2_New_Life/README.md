# SMB2 New Life

Project #001 in **NES New Life**.

## Goal

Rebuild the gameplay feel of the NES reference in Unity using a modern codebase and original/public-safe presentation assets.

## Current milestone

`0.1.0-foundation`

### Implemented in source
- player horizontal movement
- acceleration / deceleration
- variable jump
- ground detection
- crouch state
- optional charged crouch jump hook
- carryable object interface
- pickup / carry / throw foundation

## Unity setup

1. Create/open a Unity 2D project.
2. Copy the contents of `UnityProject/Assets` into the Unity project's `Assets` folder.
3. Create a `Player` GameObject with:
   - `Rigidbody2D`
   - `Collider2D`
   - `PlayerController2D`
   - `CarrySystem2D`
4. Add a child transform called `GroundCheck` near the feet and assign it to `PlayerController2D`.
5. Add a child transform called `CarryAnchor` above/in front of the player and assign it to `CarrySystem2D`.
6. Put floor colliders on a layer included in the player's `groundMask`.
7. Create a test object with `Rigidbody2D`, `Collider2D` and `CarryableObject2D`.

The first code uses Unity's classic input axes (`Horizontal`, `Jump`) plus configurable keys for crouch/action so it can run without an additional package. A dedicated input abstraction will replace this in a later milestone.

## Controls in the prototype

- Left / Right: `Horizontal` axis (default arrows / A-D)
- Jump: `Jump` button (default Space)
- Crouch: Down Arrow / S
- Pick up / throw: Left Shift

## Important

All physics values in the current foundation are **prototype defaults**, not claims about the exact original game. Verified measurements should replace them once captured during reference testing.
