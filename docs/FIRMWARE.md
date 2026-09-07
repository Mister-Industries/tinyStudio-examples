# Prebuilt firmware

Every example in this repo ships a compiled image so a reader can flash it
straight from a tinyDocs page — no Arduino IDE, no tinyStudio, no tinyService.
Opening tinyStudio is for *editing* the code, never a prerequisite for running it.

```
firmware/<category>/<name>/firmware.bin     one merged image, flashed at offset 0
firmware/<category>/<name>/manifest.json    the ESP Web Tools manifest
firmware/report.json                        what built, what didn't, and why
```

Categories mirror the sources: `basics/`, `advanced/`, and `hats/<HAT name>/`.

## How a Flash button finds its firmware

A smart code block on tinyDocs carries a `firmwarePath`:

```jsx
<InteractiveFlasher
  studioPath="basics/blink-basic"      // Edit in tinyStudio → the source
  firmwarePath="basics/blink-basic"    // Flash tinyCore    → the binary
  ... />
```

`InteractiveFlasher` turns that into
`${FIRMWARE_BASE}/basics/blink-basic/manifest.json`, where `FIRMWARE_BASE` is a
single constant at the top of the component:

```
https://cdn.jsdelivr.net/gh/Mister-Industries/tinyStudio-examples@main/firmware
```

jsDelivr fronts this repo as a CDN and sends the `Access-Control-Allow-Origin`
header ESP Web Tools needs to read a manifest from another origin.
`raw.githubusercontent.com/Mister-Industries/tinyStudio-examples/main/firmware`
also works and is always fresh, it just isn't a CDN. Changing hosts is a
one-line edit in the component.

Part paths inside a manifest are resolved **against the manifest's own URL**, so
`"path": "firmware.bin"` stays relative and the whole folder can move hosts
without editing 65 manifests.

> jsDelivr caches a branch URL for up to 12 hours. After pushing new firmware
> either wait it out or purge:
> `curl https://purge.jsdelivr.net/gh/Mister-Industries/tinyStudio-examples@main/firmware/<path>/firmware.bin`
> Tagging a release and pinning `@v1.0.0` instead of `@main` avoids the question
> entirely, at the cost of a tag per firmware update.

## Why the images are ~360 KB and not 8 MB

The ESP32 core's own build produces `<sketch>.ino.merged.bin` with
`esptool merge_bin --fill-flash-size 8MB`, which pads every image out to the
full flash. A blink sketch is 296 KB of program in an 8 MB file.

`tools/build-firmware.py` merges the same four pieces without that padding:

| Offset  | Piece            |
|---------|------------------|
| `0x0`     | bootloader       |
| `0x8000`  | partition table  |
| `0xe000`  | `boot_app0.bin`  |
| `0x10000` | the sketch       |

Identical bytes where it matters, 23× smaller. Across the whole collection that
is ~35 MB instead of ~550 MB, and a flash that starts immediately instead of
after an 8 MB download.

## Building

```bash
python3 tools/build-firmware.py                  # everything
python3 tools/build-firmware.py --only blink-basic
python3 tools/build-firmware.py --skip-deps -j8  # deps already installed
python3 tools/build-firmware.py --clean
```

The script finds `arduino-cli` in this order: `--cli`, `$ARDUINO_CLI`,
tinyStudio's vendored copy (`../tinyStudio/vendor/arduino-cli/<platform>/`), then
`PATH`. On the first run it installs the `tinyCore:esp32` core and clones every
third-party library at a pinned version into `.arduino/libraries/` — nothing
touches your global Arduino setup, and the Library Manager index is never
needed. Expect a few hundred MB of downloads once, then ~30 s per sketch.

Exit code is non-zero if anything failed, so this can gate CI.

### Two things the script works around

**Pinned libraries.** Versions are in the `LIBRARIES` table at the top. They are
pinned because "latest" bites: `ESP32-audioI2S` 3.4.7 and 4.0.0 both fail to
compile against this core (`ps_ptr<char> has no member append` — the library uses
a C++20 `requires` clause the core's C++17 build won't take). 3.2.1 is the newest
that works, and that is what the nine tinySpeak examples build against.

**Prototype generation.** Arduino lets a `.ino` call a function defined later in
the file; the builder normally synthesises the missing C++ prototypes with a
patched `ctags` it downloads from `downloads.arduino.cc`. Where that host is
unreachable, substituting a different `ctags` is worse than nothing — it reports
different line numbers and the builder splices prototypes into the middle of a
statement, producing errors like *expected constructor before ';'* in code that
is perfectly valid. So the script detects the missing tool, disables `ctags`
outright, and generates the prototypes itself, inserting them just before the
first function definition (after all globals, typedefs and structs — a safer
point than the builder's "right after the last `#include`"). It skips string
literals and comments while scanning, which matters: `tinyWebSynth` embeds a web
UI in an `R"rawliteral(...)"` block, and a naive scan emits its JavaScript
`function` declarations as C++ prototypes.

When the real tool is present none of this runs.

## What doesn't build

`firmware/report.json` carries the full compiler output for every failure. The
current set are all docs excerpts that were never complete sketches — they
reference helpers the snippet doesn't define:

| Example | Why |
|---|---|
| `bluetooth-rgb-mood-light` | uses `pService` / `RGB_CHAR_UUID`; the snippet says *"Setup BLE (similar to basic example) // ..."* |
| `wifi-basic-web-server` | calls `readTemperature()` / `readHumidity()`, never defined |
| `wifi-mqtt-client` | same |
| `wifi-websocket-server` | same |

None of these has a Flash button on tinyDocs — they are plain fenced blocks — so
nothing is broken for a reader today. They do appear in the Examples tab as
openable projects, so they are worth completing in the docs (or dropping from
the tutorial) rather than leaving as excerpts.
