# SMB2 New Life

Project #001 in **NES New Life**.

## Goal

Rebuild the gameplay feel of the NES reference in Unity using a modern codebase and original/public-safe presentation assets.

## Current milestone

`0.1.0-foundation`

## Recommended editor

**Unity 6.3 LTS** is the baseline for this project.

The current prototype deliberately avoids extra gameplay packages. It uses `Rigidbody2D`, `Physics2D` and Unity's classic input API so the first milestone stays easy to run and debug.

### Implemented in source
- player horizontal movement
- acceleration / deceleration
- variable-height jump
- coyote time and jump buffering
- ground detection
- crouch state
- charged crouch-jump prototype hook
- pickup / carry / throw foundation
- smooth camera follow
- one-click prototype scene generator

## Fastest way to run the prototype

1. Create a Unity **2D** project using Unity 6.3 LTS.
2. Copy `UnityProject/Assets/NesNewLife` from this repository into the Unity project's `Assets` folder.
3. If the project uses the new Input System exclusively, set **Active Input Handling** to `Both` or `Input Manager (Old)` for this foundation milestone.
4. Wait for scripts to compile.
5. From the Unity menu select:

   `NES New Life > SMB2 > Create Prototype Scene`

6. Open/keep `Assets/NesNewLife/SMB2/Prototype/SMB2_Prototype.unity`.
7. Press **Play**.

The generator creates a visible graybox test room, player, platforms, two carryable objects and a following camera automatically.

## Manual scene setup

If you prefer to build a scene yourself, create a `Player` GameObject with:
- `Rigidbody2D`
- `Collider2D`
- `PlayerController2D`
- `CarrySystem2D`

Add child transforms named `GroundCheck`, `PickupPoint` and `CarryAnchor`, then assign them in the Inspector. Add a test object with `Rigidbody2D`, `Collider2D` and `CarryableObject2D`.

## Controls in the prototype

- Left / Right: `Horizontal` axis (default arrows / A-D)
- Jump: `Jump` button (default Space)
- Crouch: Down Arrow / S
- Pick up / throw: Left Shift

## Important

All physics values in the current foundation are **prototype defaults**, not claims about the exact original game. Verified measurements should replace them once captured during reference testing.

The reference ROM and ripped commercial assets are intentionally excluded from the public repository.
