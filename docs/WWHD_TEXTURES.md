# Importing textures from Wind Waker HD

BlueWake can use compatible model textures from your own USA Wii U
Wind Waker HD disc (`BCZE`, title `0005000010143500`). The importer converts
them into the same Dolphin-format replacement pack that Aurora loads in
Dusklight and BlueWake. Your GameCube `GZLE01` revision 0 disc is
still required to play.

## Where it is in the app

Mac, Linux, Windows, iPhone and iPad share the same section, first in their Mods tab or menu:
**Mods › Wind Waker HD textures**. It holds the **HD textures** switch, how
many textures the chosen pack has, and a way to add a pack:

- **Mac, Linux and Windows:** F1 › Mods › **Choose texture pack folder…**.
  Windows also has **Open the texture folder**.
- **iPhone and iPad:** ⋯ › Mods › **Install Texture Pack…**, which copies the
  pack into the app.

## Import in the app (draft #315)

The native importer is in [draft #315](https://github.com/chrissotraidis/bluewake/pull/315),
not the 0.7.0 download. Its entry is **Mods › Wind Waker HD textures › Import
from Wind Waker HD…**: F1 on Mac, Linux and Windows, or ⋯ on iPhone and iPad.
Android's equivalent entry is implemented in [draft #347](https://github.com/chrissotraidis/bluewake/pull/347),
on top of #315 and the Android port; its interactive phone checks remain open.
The app needs no Python.

1. Choose **Folder…** for your decrypted Wind Waker HD dump: the folder that
   holds `code`, `content` and `meta` (as Cemu uses it), or its `content` folder.
   Alternatively, choose **WUD/WUX Image…**, then your disc key and either a
   common key or a decrypted title key. Key files are 16-byte binary files or
   text containing 32 hexadecimal digits. The menus show filenames, never key
   values; key selections are used only for this import and are not saved in
   settings. Cancelling a key picker returns to key selection. On iPhone/iPad,
   cancelling the initial folder/image picker ends the flow; reopen **Import
   from Wind Waker HD…** to start again.
2. BlueWake reads it with the GameCube disc it already plays and makes the pack
   in a new folder, preserving existing packs: `Load/Textures/WWHD` in the
   app's data folder (`WWHD-2` and so on if it exists).
3. On desktop, the menu shows progress; you can close it and play while the
   import works, or cancel the job. When it finishes, reopen Mods to see the
   result. The new pack is selected and **HD textures** is on. Resume the game
   to save the choice, then restart BlueWake to load it.
4. On iPhone/iPad, the game pauses behind an import progress sheet. **Cancel**
   keeps it paused while the current read and cleanup finish. Switching apps
   during import also requests cancellation; the result appears after returning.
   When the import completes, the app offers to turn on HD textures for the next
   launch. Restart to load the pack. This path still needs a full-dump test on
   hardware and an interactive check of cancellation/background transitions.
5. In the Android candidate, ⋯ › Mods offers the same folder/image choices.
   Import pauses the game; Cancel or switching apps requests cleanup, and the
   result waits until the app is active again. A successful import selects the
   completed pack and offers to enable HD textures for the next launch. Restart
   to load it. The interactive phone checks are still pending.

The native importer implements the script's matching and conversion: from
the supplied decrypted HD folder and GameCube disc it makes the same 3,546
textures, in about 30 seconds on an M3 Max. On Linux (Arch, X11, NVIDIA),
pdale-boop imported his own dump's `content` folder from the menu, from a path
with spaces and Japanese characters: 3,546 keys and 33,859 PNGs, the same counts
as the Mac, and the restart loaded all 3,546. Cancelling an import kept his
previous pack selected and left no partial pack. The image reader passes
generated encrypted-disc checks, including a Mac menu import. On the iPhone 17e
simulator, a test app running the production iOS menu and importer (without
the game) imported generated inputs through Files, as a folder and as a WUX
image with key files; cancelling a key picker kept the other choices. An
authentic WUD/WUX comparison, a Windows interactive import, and iPhone/iPad
hardware, memory and lifecycle checks remain open. These are distinct from
build and simulator fixture results below.

The output follows the app's data folder, including Linux portable mode and
an explicitly selected desktop settings location.

## The import script

The script makes the same pack from a computer, and also reads WUX and WUD
images with their key files.

## Set up the importer

From the repository root:

```sh
scripts/setup_wwhd_tools.sh
```

This creates a local Python environment in ignored `build/wwhd-tools`, installs
the versions pinned in `scripts/wwhd/requirements.txt`, and builds a small Yaz0
decoder if a C compiler is available. Without a compiler the Python decoder
works, but takes longer. No game data or keys are downloaded by this script.

On Windows, with Python 3.11 or newer installed, run this from PowerShell in the
repository instead (it builds the decoder with Visual Studio's C compiler when
one is installed):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_wwhd_tools.ps1
```

and use `build\wwhd-tools\Scripts\python.exe` wherever the commands below say
`build/wwhd-tools/bin/python`.

## Import your discs

For a WUX/WUD image, supply your disc key and a common key file. Keys are
16-byte binary files or text files containing 32 hexadecimal digits. The
importer decrypts the disc's own embedded ticket to obtain its title key.

```sh
build/wwhd-tools/bin/python scripts/import_wwhd_textures.py WindWakerHD.wux \
  --gc-disc WindWakerGC.iso \
  --disc-key game.key --common-key common.key --install
```

The image is read directly, so a 25 GB expanded WUD is unnecessary. The
importer validates the disc identity, file table checksum and each hashed
content block it reads. It also detects incomplete WUX extraction before
reading any texture content.

`game.key` and `common.key` beside the HD image are used by default. If you
already decrypted that disc's title key, use `--title-key title.key` instead
of `--common-key`. A NUS title key may differ from the disc's title key even
when the title ID is the same. A `.tik` file contains an encrypted title key;
it does not substitute for the WUD disc key.

For a decrypted HD `content` folder, no key files are needed:

```sh
build/wwhd-tools/bin/python scripts/import_wwhd_textures.py /path/to/content \
  --gc-disc WindWakerGC.iso --install
```

On a Mac, the default GameCube disc is the one inside your BlueWake app
(`/Applications/BlueWake.app/Contents/Resources/Game/GZLE01.iso`, or the same
place under `~/Applications`), or else the ISO Wind Waker Recomp imported
(`~/Library/Application Support/Wind Waker Recomp/GZLE01.iso`). You may omit
`--gc-disc` when one of those exists. On Linux it is the disc BlueWake
remembers (`~/.local/share/BlueWake/disc.txt`). On Windows it is the `.iso` or `.gcm` that
BlueWake remembers (`%APPDATA%\BlueWake\disc.txt`), or the ISO it unpacked
from a Dolphin `.rvz` (`%APPDATA%\BlueWake\GZLE01.iso`).

## Keep an existing pack as fallback

Add `--fallback-pack /path/to/existing-pack` to the import command to keep
existing HD artwork for anything the disc importer does not replace:

```sh
build/wwhd-tools/bin/python scripts/import_wwhd_textures.py WindWakerHD.wux \
  --disc-key game.key --common-key common.key \
  --fallback-pack "/path/to/ZWW4K 1.0.0d (4K)" --install
```

The importer searches nested texture folders, so the containing ZWW4K folder
is acceptable. Wind Waker HD artwork takes priority by source texture key,
regardless of PNG/DDS extension or mipmap naming. Only absent keys and their
own mipmaps are copied into a `fallback` subfolder. The original pack is
unchanged. The title copyright texture is excluded from fallback imports so
the disc's Nintendo copyright remains instead of a texture-pack banner. For example, existing HUD replacements can remain active while
compatible character and environment textures come from the HD disc.

## Use the result

On a Mac the default output is
`~/Library/Application Support/BlueWake/Load/Textures/WWHD`.
`--install` selects that folder in the app's settings
(`~/Library/Application Support/BlueWake/settings.ini`) for the next launch
and backs up the previous settings. Restart the app to load it. You can also
omit `--install` and pick the output folder with **Mods › Wind Waker HD
textures › Choose texture pack folder…**. Turn **HD textures** off to go back
to the GameCube textures.

On Linux the default output is `~/.local/share/BlueWake/Load/Textures/WWHD`
(`$XDG_DATA_HOME` when set), and `--install` writes the same setting to
`~/.config/BlueWake/settings.ini` (`$XDG_CONFIG_HOME` when set).

On Windows the default output is `%APPDATA%\BlueWake\Load\Textures\WWHD`.
Close BlueWake first: `--install` turns on **HD textures** and points it at
that folder in `%APPDATA%\BlueWake\settings.ini` (`hd_textures=1`,
`texture_pack=...`), keeping a backup of the previous file, and BlueWake
rewrites that file when its settings change. The settings menu (F1, Mods)
then names the pack's folder, with a button to go back to
`Load\Textures\GZLE01`.

Use `--output /path/to/new-folder` to choose another output folder. Existing
folders are preserved; the importer requires a new destination. For an
iPhone/iPad personal build, choose the generated folder with **Mods › Install
Texture Pack…**, turn on **HD Textures**, and restart.

The pack contains PNG textures, `_mipN` mipmaps and `import-report.json` with
source checksums, tool/dependency records, matches and skipped conflicts.
When a fallback is supplied, its selected keys and file checksums are also
recorded in the report. Unsupported fallback filenames are listed there.
The detailed report is local game-derived metadata; keep it with your private
pack. Never include the resulting textures, keys, tickets or discs in source
commits or public app releases.

## Scope and matching

The importer reads GameCube RARC archives, BTI textures and J3D TEX1 model
chunks, and HD Yaz0/SARC archives, Wii U BFRES v3/v4 FTEX textures, BFLIM
images and FFNT v3 bitmap fonts. Both Picto Box inventory icons and the water bottle have verified
mappings from the HD item layout to the GameCube item archive. The transparent
English HD title logo and its HD badge are fitted to the original logo UVs.
Other redesigned UI images are
not matched by their numbered filenames. For model textures it
matches both the resource identity and texture name; stage rooms are scoped
by stage and room, including the HD `sea_Room0` naming convention. It then
checks that the replacement preserves the original aspect ratio and is at
least the original resolution. The replacement filename hashes the original
GameCube texture bytes, and for indexed textures only the palette entries
those bytes reference, exactly as the renderer does.

The decoded HD component selections and source mipmaps are preserved, with
GameCube I4/I8 replacements using intensity for alpha as the original renderer
expects. Missing levels down to 1x1 are generated. Conflicting artwork for the same GameCube
texture key is skipped, except for explicitly audited shared-artwork variants.
Those choices preserve the original UV composition instead of HD debug-room,
figurine or photographic-cloud variants. Selected alternatives are recorded
in the report. Tiny placeholders and shader ramp textures stay
original. Different UV layouts or changed names need separate, verified
mappings and are not guessed.

This imports compatible model artwork. Wii U models, shaders, lighting,
normal/bake maps, redesigned HUD layouts and gameplay are not imported.
The HD camera mode indicators, minimap frame/check textures and BFRES
Japanese title layers use different transparency or layout rules and are excluded;
the English title uses the transparent HD layout images instead. An existing
fallback pack supplies other compatible missing textures. Verified BFLIM mappings
cover inventory bottles, equipment, trading items, collection icons and charts.
Forest Water's animated sparkle remains supplied by the GameCube game. HD HUD
hearts combine their separate outline and fill into the original sprite's UV
area. The swimming HUD's matching masks and decorations are also imported;
layout masks combine luminance and alpha for GameCube I4/I8 sampling.
Verified English action labels, inventory/quest/save headings, quest-log labels,
item counters, rupee digits and dungeon-floor labels are rebuilt from the HD
disc's own font glyphs. Each sprite retains its original alpha bounds and
transparent padding. A/B/X/Y symbols use the corresponding HD pictograph
font; redesigned L/R/Z and stick prompts retain their existing artwork.
The small HUD key and menu cursor corners are fitted the same way. Lower
resolution HD item-get sprites are not substituted for sharper originals.
The six opening story pictures are cropped to the original composition,
including splitting HD's panorama into the two original sprite planes.
RGBA8 and BC1-5 layout surfaces preserve color, luminance and alpha;
unmapped redesigned HUD images and JPA particle textures remain
unsupported. Unsupported resources and textures are listed in the report.

## Source and verification

The bounded format readers use the layouts documented by
[BFRES-Tool](https://github.com/aboood40091/BFRES-Tool),
[BFLIM-Tool](https://github.com/aboood40091/BFLIM-Tool), and
[JNUSLib](https://github.com/Maschell/JNUSLib). FFNT section layouts are also
documented by [3dstools](https://github.com/ObsidianX/3dstools/blob/master/bffnt.py);
the importer contains its own bounded reader for the audited BC4-alpha and
RGBA8 font surfaces, including GX2 array-page bank rotation. The Wii U address library is
vendored from BFRES-Tool at the exact revision in
`scripts/wwhd/vendor/SOURCE.json`, with its GPL-3.0-or-later license and
copyright notice. The importer has no GUI toolkit dependency.

Generated fixture checks cover decoding, palette hashing, stage/room scope,
malformed inputs, encrypted content integrity, conflicting replacements and
settings preservation, intensity-mask transparency, fallback priority and matching mip chains,
font array pages and malformed section chains, sprite-mask padding and panorama crops:

```sh
build/wwhd-tools/bin/python tests/wwhd_import_test.py
```

Checked by hand on October 12, 2026, on a Mac (M3 Max): a decrypted USA dump's
`content` folder with a revision 0 GameCube ISO gave 3,546 replacements (124
conflicting keys skipped). BlueWake loaded all of them at Outset, with the
Wind Waker HD look on and off; an unpaced run took 9.3 s against 9.2 s without the pack.

### Native importer validation (October 15, 2026)

The importer remains draft work. The detailed revisions, measurements and
reproduction commands are consolidated in the
[native import validation record](status/WWHD_NATIVE_IMPORT_2026-10-15.md).

| Platform | Established | Still to check |
| --- | --- | --- |
| Mac | Full decrypted-folder output: 3,546 keys and 33,859 PNGs matching the Python import's pixels. Menu import, next-launch loading and cancellation fixtures pass; copied save unchanged | Authentic WUD/WUX input; desktop mouse interaction |
| Windows/Linux | Native importer build and generated tests pass Windows/Linux CI at `254195d`, including the cancellation update | Interactive folder/image/key imports |
| iPhone/iPad | Generated importer execution in iOS Simulator, production app linking, and coordinated-read/cancellation lifetime checks | Actual Files/menu interaction, background transitions and full-dump memory on devices |
| Android | Baseline APK `ea6e55e` on API 36: actual folder picker, copy cancellation, full import and restart loading pass; all 33,859 PNG hashes match the Mac baseline, with 3,546 renderer registrations and the HD title visible. Copied card unchanged at import completion | Newly integrated recovery in the app; activity/background transitions, fresh-slot gameplay, physical-phone memory and authentic image import |

Standalone Mac importer peak memory fell from 993 to 538 MiB; the complete
Mac app peaked at about 1.30 GiB while importing during gameplay. These do
not establish a mobile memory budget. Force-quitting can leave hidden staging
folders. A later import using the same output parent recovers recognized output
with a valid ownership marker; completed packs and older unmarked folders stay
untouched. Cleanup failures are reported. A stalled OS read can still delay
cancellation; app-level force-close/retry and mobile input-copy recovery remain
separate from the shared output recovery checks in the dated validation record.
The import also leaves an empty `.bluewake-wwhd-import.lock` in `Load/Textures` by design: it keeps two
imports from writing there at once, and can be deleted while BlueWake isn't running.
