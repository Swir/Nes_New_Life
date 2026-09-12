# Rapid HD Playtest — Project #002

The fastest local loop is now:

```text
MesenCE capture
  -> resume-safe production sync
  -> automatic baseline for untouched masters
  -> combined batch apply
  -> pixel QA
  -> HD-pack validation
  -> install to MesenCE/HdPacks/<ROM name>
  -> reload ROM and play-test
```

## Windows one-click

Double-click:

```text
windows/Build_HD_Playtest.bat
```

Choose:

1. the local MesenCE HD Pack Builder capture folder containing `hires.txt` and PNG sheets,
2. the local Project #002 workspace created by the Remaster Studio,
3. your local Tiny Toon `.nes` file,
4. the MesenCE `HdPacks` folder (the conventional Windows location is offered automatically).

The builder then performs the entire production chain and installs the QA-passed runtime pack under a folder whose name exactly matches the ROM filename without `.nes`.

Example:

```text
ROM: C:\ROMs\Tiny Toon Adventures (USA).nes
Pack: %USERPROFILE%\Documents\MesenCE\HdPacks\Tiny Toon Adventures (USA)\hires.txt
```

Mesen-style HD packs are resolved by ROM filename, so this exact folder-name relationship is important.

## Safety guarantees

- the ROM is never copied into the HD-pack directory,
- ROM/save/patch payloads are rejected before deployment,
- generated JSON/HTML/CSV production reports are not copied into the runtime pack,
- an existing installed pack is moved to a timestamped backup before replacement,
- `hires.txt` must remain byte-for-byte mapping-preserved through art apply,
- pixel QA must pass before deployment,
- structural HD-pack validation must pass before deployment,
- existing manually edited master art is preserved; the automatic baseline only seeds untouched masters.

## Command line

```powershell
python tools/rapid_hd_playtest.py `
  "C:\Work\TinyToon\MesenCapture" `
  "C:\Work\TinyToon" `
  --rom-name "Tiny Toon Adventures (USA).nes" `
  --hdpacks-root "$env:USERPROFILE\Documents\MesenCE\HdPacks"
```

Use `--no-baseline` when you want to compose only manual master edits. Use `--no-backup` only when you intentionally do not want a backup of the currently installed HD pack.

## What PLAYTEST READY means

`PLAYTEST READY` means the **currently captured content** produced a valid 4x HD pack whose mapping survived unchanged and whose batch art changes passed pixel QA. It does not mean every route, animation, enemy, boss, effect, ending screen or other unseen game state has already been captured or hand-finished.

The path to a truthful final release remains: keep expanding the MesenCE capture until full-game evidence is complete, then replace automatic baseline masters with final reviewed artwork and finish the readiness checklist.
