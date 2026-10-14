# Native HD importer validation — October 15, 2026

Dated evidence for drafts [#315](https://github.com/chrissotraidis/bluewake/pull/315) and
[#347](https://github.com/chrissotraidis/bluewake/pull/347). This records the revisions
and checks below; it is not release or phone acceptance. Current usage is in
[WWHD_TEXTURES.md](../WWHD_TEXTURES.md), and the remaining work is in
[PRIORITIES.md](../PRIORITIES.md). Private discs, packs and captures remain local.

### Native importer memory check (October 15, 2026)

The importer now feeds PNG scanlines to zlib one row at a time, caps queued
and active PNG image data at 32 MiB (one larger image may run alone), and
shares unchanged mip chains across GameCube formats. Archive traversal borrows
uncompressed containers. The English layout pack retains only the heart
outline and HD badge needed by other members, then processes members in their
original order instead of keeping every member alive.

On the same M3 Max, using the same decrypted USA HD tree and revision 0
GameCube disc, a standalone native import with four PNG workers measured:

| Version | Peak resident RAM | Wall time |
| --- | ---: | ---: |
| PR #315 at `6232826`, before this change | 993 MiB (1,041,235,968 bytes) | 26.49 s |
| With streaming and shorter buffer lifetimes | 538 MiB (563,806,208 bytes) | 28.94 s |

Measured with `/usr/bin/time -l`, compiled with Apple Clang at `-O2`.
Peak RAM fell 46%. Other work was running on the Mac, so these times are not
an isolated speed benchmark. These are importer process measurements, not
the combined memory of an app importing while a game runs or an iPhone/iPad test.

Both native runs produced the same 3,546 texture keys, 33,861 filenames,
124 skipped conflicts and 17 unsupported entries. All 33,859 PNGs, including
every mip level, were byte-identical; matching metadata and all 91 generated
HUD/title textures were unchanged.

A fresh Python import from those inputs also matched every PNG's decoded
pixels and every texture chain's SHA-256, with the same matching metadata,
conflicts and unsupported entries. The native exact-report run produced the
same PNG bytes as its four-worker run, using 394 MiB peak resident RAM
(413,024,256 bytes) in 143.87 seconds with serial writing and SHA-256 enabled.

`tests/wwhd_native_test.cpp` checks generated nested SARC/RARC/Yaz0 archives,
empty members, malformed inputs and callback errors, plus streamed PNGs
against whole-image zlib compression and decoded pixels. It passes with
AddressSanitizer and UndefinedBehaviorSanitizer on this Mac. Build the development
importer and disc checks through the configured host build, so they use
the same pinned disc-crypto dependencies as the app. For an existing Mac
builder tree (replace `BUILD` with its CMake build directory):

```sh
cmake -S scripts/builder/training -B BUILD \
  -DBLUEWAKE_WWHD_TEST_PYTHON="$PWD/build/wwhd-tools/bin/python"
cmake --build BUILD --target bluewake_wwhd_native_import \
  bluewake_wwhd_disc_image_test bluewake_wwhd_disc_crypto_test \
  bluewake_wwhd_wiiu_disc_test bluewake_wwhd_import_job_test
ctest --test-dir BUILD/host --output-on-failure -R '^bluewake_wwhd_'
```

The test Python needs only `pycryptodome==3.23.0`; the app needs no Python.
Windows and Linux CI compile and run these generated-input checks too.
For a development import, run `BUILD/host/bluewake_wwhd_native_import`
with the HD content folder (or disc image), GameCube ISO and a new output
folder, in that order. An image can take three additional paths: disc key,
common key, title-key override (use an empty argument to skip the common
key). `game.key` and `common.key` beside the image are the defaults. Key
values never go in the command line. `WWHD_EXACT_REPORT=1` selects the slower,
serial SHA-256 report.
To compare native or Python packs, including every PNG and all available
RGBA-chain SHA-256s:

```sh
build/wwhd-tools/bin/python tests/wwhd_compare_packs.py OLD-PACK NEW-PACK
```

Keep both packs and their reports private. Windows/Linux interaction and
imports on phone/tablet hardware still need their own checks.

### Mac in-app check (October 15, 2026)

On the M3 Max with Metal, the native import was started through F1 > Mods
from the supplied decrypted USA content folder while a copied GameCube save
was running at Outset. Closing the menu let gameplay continue during the
conversion. The menu reported 3,546 textures and selected the resulting pack
in the isolated session's data folder. After selecting that installed pack,
resuming to save the preference and restarting, the renderer registered all
3,546 replacements; the HD HUD and textures were visible and movement worked.
The copied card's SHA-256 was unchanged.

The complete process peaked at 1,400,389,632 bytes (1,336 MiB) resident RAM,
sampled every 250 ms across startup, gameplay and import. This includes the
game and renderer and is not directly comparable to the standalone importer
table. It does not establish memory acceptance on iPhone, iPad or Android.

Keyboard navigation was used for the menu and the native folder picker.
Mouse clicks did not consistently activate the ImGui controls through the
automation surface; this run does not establish desktop mouse acceptance.

### Stopping an import

The desktop background job is owned until its worker exits. Closing the app
cancels and joins the worker before destroying its progress/status state;
completion, cancellation, a second import, missing input and shutdown are
covered by `bluewake_wwhd_import_job_test` on the desktop build paths. This
regression fails against the earlier detached worker and passes with AddressSanitizer
and UndefinedBehaviorSanitizer on the Mac. It uses generated inputs and a
controlled worker; it is not a mobile lifecycle or full-disc cancellation test.

Cancellation now also reaches folder and GameCube scans, archive members,
disc blocks, texture/mipmap work and PNG workers. It clears queued PNG jobs,
joins workers before cleanup, and checks again immediately before publishing
the finished folder. Once that rename succeeds, a late Cancel still reports
success. Files are explicitly closed and checked before publication so a
buffered write failure cannot silently produce an incomplete pack.

Generated checks on the Mac cover 23 cancellation points, both real PNG-worker
wait paths, cleanup and existing-pack preservation, late cancellation after
publication, and two buffered-close failures. Seven CTests, six ASan/UBSan
checks and two TSan checks pass. A fresh full import after these changes still
produces all 3,546 keys and 33,859 byte-identical PNGs, including every mip and
the 91 generated HUD/title textures; matching metadata is unchanged. The
complete iOS Simulator app also links with the changes. The iOS operation's six Foundation cases cover
success/error, cancellation before starting, while waiting for a provider,
during conversion, and after a completed commit. They verify grant lifetime,
suppression of late progress and one completion; they also run in the Mac CI
audit under sanitizers. They do not establish UIKit or Files-provider acceptance.

Cancellation cannot interrupt an OS read that is already stalled. Abrupt process
termination also bypasses exception cleanup and can leave hidden staging folders;
ownership/restart recovery and reporting failed cleanup remain open work.

### Native iOS Simulator check (October 15, 2026)

An isolated test app linked all eight production importer source files from
`a640108` for arm64 iOS Simulator 27.0 (iPhone 17e), using the iOS path's two
PNG workers. Seven generated-input cases passed: empty/missing HD folders,
missing GameCube disc, malformed-resource cleanup, successful import, refusing
to overwrite an installed pack, and repeat import to a new folder. Both packs'
12 PNGs passed independent CRC, dimension, pixel and mip-chain checks. The
production `BWGameOverlay.mm` also compiled without diagnostics.

This checks the importer in an actual Simulator process. The production menu,
Files picker, security-scoped external folder access, alerts, saved preferences
and next-launch renderer loading were not part of that harness. No game data
or physical device was used; full-dump iPhone/iPad memory acceptance remains open.

A separate full production simulator build from `a640108` with RecompCore
`ee99bbc` also linked and reached Outset on the iPad Air 11-inch (M4) / iPadOS
27.0 simulator. The game and touch overlay were visible. Its distinct test
bundle used a copied card, whose hash stayed unchanged. Device Hub returned
`noWindowsAvailable` for automation input, so this run did not verify the Mods
menu or file picker. The test app was uninstalled and the simulator shut down;
the physical iPad was not touched.

### Combined runtime check (October 15, 2026)

The native-import branch at `6bc56e5` also builds on macOS and iOS Simulator
with the newly approved Picto recognition pin, RecompCore `57123c6`. Five Mac
host checks passed (import-worker lifecycle, save state, cache flush, frame
interpolation and FIFO worker), as did the alpha, destination-alpha and early-depth
Metal pixel fixtures. A Mac Outset run registered all 3,546 replacements with
the HD look enabled and exited normally; the copied card stayed unchanged.
The temporary cache folder was missing in this smoke run, so SQLite caching
was disabled. This was not a performance measurement or first-photo test.
The exact combined iOS revision was compiled, not played or imported on hardware.

The expanded importer was also executed in a fresh iPhone 17e / iOS 27.0
Simulator fixture app after the WUD/WUX core was added (`46846e2`, with source
hashes checked again at `b23787d`). All fourteen production importer/crypto
units linked. The same seven generated folder cases and twelve PNG checks
passed; the test app was removed and the simulator returned to Shutdown.
This fixture did not execute an encrypted import or the production picker.

The new iOS folder/image/key flow compiles for arm64 device and simulator,
and the complete production simulator app links with RecompCore `57123c6`.
It holds security-scoped access while selecting and importing, and coordinates
all external input reads together on a worker queue using the returned URLs.
A Foundation-only check covers three coordinated reads, a coordination error
that prevents reads, and completion order. It does not test UIKit, iCloud or
another Files provider; those interaction checks remain open.

### Native WUX/WUD progress (October 15, 2026)

The native reader now handles WUD/WUX sector mapping, partitions, the Wii U
file table and title metadata, locally supplied keys, AES-CBC decryption,
and file-table / hashed-content checksums. It reads resources directly into
the existing texture matcher without expanding an entire WUD. The CLI and
desktop/iOS menus can select either a decrypted folder or an image with key files.

The reader's generated fixtures cover reordered/duplicated sectors, reads
above 4 GiB, a 64 GiB logical image backed by less than 9 MiB of test data,
raw/CBC/hashed content across block boundaries, title/common/override keys,
wrong keys, malformed tables and damaged content. The encrypted fixtures are
checked independently by the existing Python reader. Mac CTest and the
parser's AddressSanitizer / UndefinedBehaviorSanitizer run pass. The updated
production Mac and iOS Simulator apps compile and link. Windows and Linux CI
passed for the image/key menu at `ea31b24`; the later cancellation changes need
their own results.

An end-to-end generated fixture also checks folder import against WUD and
mapped WUX in four key modes: nine successful imports have identical PNGs,
with every mip's dimensions, pixels and CRC independently checked. Twelve
failure cases verify wrong-key rejection, existing-pack preservation, and
staging cleanup after corrupt content. Five more imports put the folder/image,
GameCube disc, keys and output beneath accented, Japanese and emoji paths;
their PNGs match the ASCII-path baseline on the Mac. The Windows development
CLI and fixtures now use the app's existing UTF-8 manifest; Windows execution
of these cases remains a CI check. A fresh full import of the supplied
decrypted HD tree still matches all 3,546 keys and all 33,859 PNG bytes from
the earlier pack; this run peaked at 561,643,520 bytes RSS on the Mac.

The Mac menu also completed a WUX import using generated disc metadata and
synthetic keys around one private HD resource. Image/disc/common-key selection,
cancelling and reopening a key picker, completion, pack selection and resumed
gameplay worked. Its nine PNGs matched the CLI output byte for byte; settings
contained no key paths, the report contained no key values, and the copied
card's SHA-256 was unchanged. This used keyboard navigation and native file
pickers. The title-key menu route and a renderer restart with this small pack
were not part of that check.

Still required before advertising image support: an authentic image-to-pack
comparison, Windows/Linux and iOS picker interaction, Android integration, and
phone/tablet memory and lifecycle validation. The supplied reference is a
decrypted folder; generated encrypted fixtures do not establish acceptance
of an authentic disc dump. The committed automated fixtures contain no game
assets or private keys; the Mac menu check's HD resource and output stay private.

### Android core check (October 15, 2026)

At `ea31b24`, the native development importer and three reader/crypto test
executables built for arm64 with NDK r29 (`29.0.14206865`, minimum API 28).
They ran on a fresh Android API 36 ARM64 emulator. Five generated imports
(folder, WUD and WUX with common/title key modes) produced thirty PNGs whose
pixels, CRCs and mip sizes passed the independent fixture checks; each image
pack also matched the folder pack byte for byte. The three reader tests passed,
and a wrong key was rejected without an output folder. Only generated fixtures
were used. The temporary emulator was stopped and removed afterward.

This is core execution, not the Android app, a Files picker, real-phone memory
or gameplay performance. Android #93 at `42610f2` has an existing-pack installer
but no native HD import entry. Its settings also still use one fixed pack folder;
selecting a completed native import must be wired into both launch settings
and the displayed count.

The input adapter needs to handle document URIs through Android's
[Storage Access Framework](https://developer.android.com/training/data-storage/shared/documents-files),
not treat them as filesystem paths. The
[ContentResolver contract](https://developer.android.com/reference/android/content/ContentResolver#openFileDescriptor(android.net.Uri,java.lang.String,android.os.CancellationSignal))
allows a read-only descriptor to be a pipe. Image imports need a checked,
seekable source or a cancellable local staging copy; they must not request
write access merely to obtain seeking. Folder traversal, key access, cancellation,
storage exhaustion and activity recreation are integration checks. The candidate
below implements this adapter and records which checks have passed.


### Android app integration candidate (October 15, 2026)

Draft [#347](https://github.com/chrissotraidis/bluewake/pull/347) combines the unmerged Android port
(#93 at `42610f2`) with #315 at `254195d` to prepare the hookup separately.
It does not change `main`, the port's performance gate or any download.

The menu now offers **Mods › Wind Waker HD Textures › Import from Wind Waker HD…**.
Players choose a decrypted folder, or an image and transient key files. The
job owns read-only document access until native conversion and cleanup finish.
A seekable image uses a private alias to its retained descriptor; a pipe is
copied with cancellation checks. Folder imports stage only the resource types
the shared importer reads. Cancel and backgrounding request cleanup while the
progress screen holds the game; completion waits for an active activity.
Only a completed pack is saved as the selected next-launch folder. Existing
PNG/DDS installations continue to use their own GZLE01 folder.

Validation so far: the complete Android Java shell compiles, and the production
ARM64 `libmain.so` links with NDK r29/API 33 and the approved RecompCore `57123c6`.
Its importer JNI entry points are exported, and its dynamic dependencies are
Android system libraries. Cross-builds disable host pkg-config by default after
a Mac zstd package leaked into the first link attempt; the successful build
compiles the pinned zstd source for Android. The APK packaging code now copies
the Mbed TLS license used by the image reader. The production packaging method
passed a source-only APK check on the Mac, adapting Windows tool filenames to
their Mac equivalents: all 79 compiled Java classes survived dexing, required
JNI exports and license/pipeline-cache bytes matched, and synthetic signing plus
16 KiB ZIP/ELF alignment passed. The unmodified Activity loaded SDL/JNI and
reached the expected missing-game-executable diagnostic on an API 36 ARM64
emulator. That dialog blocks the game/menu flow, so this proves startup, not
interactive importing. Execution used 4 KiB pages; a 16 KiB kernel and the actual
Windows packaging invocation remain unchecked. The test app and AVD were removed.

A generated document provider passed 33 cases on an API 36 ARM64 emulator:
folder/name validation, size mismatches, key validation, raw/WUX native alias
reads, reliable-pipe errors and cancellation during query, open, copy and an
idle pipe. The test package and temporary emulator were removed afterward.
The production JNI bridge passed 428 assertions on the Mac JVM, including
16 generated imports and 96 independent PNG checks through ASCII/Unicode paths,
concurrent/stale session rejection, cleanup and late-cancel success. The same
428 assertions and 16 imports / 96 PNG checks also pass through JNI in four ART
processes on a fresh API 36 ARM64 emulator, with output matching the host baseline.
The temporary emulator was then stopped and removed. Complete Files/menu
interaction, activity recreation, physical-phone memory and authentic-disc
import remain to be established.

Reproduce the generated adapter check with
`python3 tests/wwhd_android_inputs_test.py --serial emulator-NNNN` on an explicitly
selected emulator; omitting `--serial` builds the test APK only. The JNI harness
is `tests/wwhd_android_native_test.py`. Both use generated inputs, not game data.

### Full Android folder import (October 15, 2026)

The production JNI bridge and shared importer sources from `ea6e55e`, with
RecompCore `57123c6`, were compiled with NDK r29/API 28 for a standalone ART
harness on a fresh API 36 ARM64 emulator. It imported the supplied decrypted
HD content folder with the GameCube disc. All 3,546 replacement keys and
33,861 filenames matched the Mac baseline; all 33,859 PNGs were byte-identical.
Matching report metadata, 124 skipped conflicts and 17 unsupported entries
also matched. The baseline already has pixel parity with the Python importer.

The standalone JNI process recorded 386,848 KiB (377.8 MiB) peak resident RAM
in `/proc`'s high-water mark. This excludes the Android app, game and renderer;
it is not a phone memory or speed result. This harness targets API 28, while
the separately linked production app targets native API 33.

Input, baseline and source hashes were unchanged. Private emulator copies,
temporary output archives and all task AVDs were removed. The final replay
followed corrections to two comparison-harness errors; no production fix was
needed. Actual Files/menu use, activity lifecycle, physical-phone memory and
an authentic WUD/WUX comparison remain open.

### Removal failures and complete-pack comparison (`71642ec`, October 15)

The native core at `5fbb596` rejects an import if a conflicting texture or superseded mipmap cannot be
removed. The generated A/B conflict plus independent C fixture reproduces the earlier false success; the
fixed synchronous and threaded cases pass under ASan/UBSan. The mipmap-removal check is source-reviewed,
not separately fault-injected. Windows and Linux CI both pass at `5fbb596`.

A fresh optimized Mac import after this fix produces all 3,546 keys, 33,861 files and 33,859 PNGs
byte-identical to the earlier complete pack. The 124 conflicts, 17 unsupported entries and report metadata
apart from the creation time match. HD inputs, GameCube disc, baseline and tested binary are unchanged.
This is a decrypted-folder correctness check under concurrent build load, not a speed measurement or an
authentic WUD/WUX image check.

The full-input Debug ASan/UBSan attempt hit a 300-second limit. Killing it left 12,537 files in its private,
owned staging directory, which was then removed after confirming the process had exited and no pack was
published. The completed full-pack comparison used Release optimization; the targeted failure suite retains
its sanitizer evidence. This confirms the separate forced-process recovery gap. Work on owned-staging
recovery is underway in #315; it is not included in the `5fbb596` result. Android input-cache recovery is a
separate concern from output-pack staging.
