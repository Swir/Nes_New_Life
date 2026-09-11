# SMB2 New Life — Reference ROM Analysis

This file records non-copyrightable technical metadata from the locally supplied research ROM. The ROM itself is intentionally excluded from this repository.

## Supplied reference

- Filename: `Super Mario Bros. 2 (USA) (Rev 1).nes`
- Container supplied by user: ZIP archive
- ROM size: 262,160 bytes
- SHA-256: `6ca47e9da206914730895e45fef4f7393e59772c1c80e9b9befc1a01d7ecf724`

## iNES header

- Magic: `NES 0x1A`
- PRG ROM: 131,072 bytes (128 KiB)
- CHR ROM: 131,072 bytes (128 KiB)
- Mapper: 4 / MMC3 family
- Trainer: no
- Battery flag: no
- Mirroring flag: horizontal
- Flags 6: `0x40`
- Flags 7: `0x00`

## Research rules

- Do not add the ROM to Git.
- Do not add ripped Nintendo sprites, tiles, music or sound effects to public releases.
- Gameplay observations may be documented as measurements and behavior descriptions.
- Public-facing builds should use original or properly licensed replacement assets.

## Next measurements

The following should be measured during gameplay/reference testing rather than guessed:

- horizontal acceleration / deceleration
- max walking and running velocity
- jump impulse and gravity curve
- variable jump behavior
- crouch / charged jump behavior
- object pickup delay by character
- throw velocity and arcs
- enemy contact / damage timing
- invulnerability duration
- camera dead-zone and scroll behavior
- door and subspace transitions

These values will become ScriptableObject character/gameplay profiles in Unity.
