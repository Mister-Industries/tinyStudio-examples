# tinyStudio Examples

Ready-to-open, ready-to-flash Arduino projects for the **tinyCore** (ESP32-S3)
and the tinyHAT expansion boards, from [MR.INDUSTRIES](https://mr.industries).

Every project is generated from the code published on
[tinyDocs](https://tinydocs.cc) and compiled here, so the code in the tutorial,
the project you open in the IDE, and the binary you flash are all the same
bytes. The docs page is the source of truth; this repo is its machine-readable
mirror.

## Three ways in

1. **Flash it** — the green **Flash tinyCore** button on any tinyDocs code block
   writes the prebuilt image over Web Serial. No IDE, no tinyStudio, no
   tinyService, nothing to install.
2. **Edit it** — the green pencil **Edit in tinyStudio** button opens the same
   sketch in [tinyStudio](https://app.tinystudio.cc).
3. **Browse it** — the **Examples** tab in tinyStudio lists everything in
   `examples.json`, grouped by category. Desktop can download the whole set to
   *Documents/tinyStudio Examples*.

Direct URLs work too: `https://app.tinystudio.cc/<owner>/<repo>/<path>`, e.g.
[`…/tinyStudio-examples/basics/blink-basic`](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/blink-basic)

## Layout

```
basics/<name>/<name>.ino     tinyCore fundamentals — LEDs, buttons, sensors, SD, WiFi, BLE
basics/<name>/README.md      the tutorial text that goes with the sketch
advanced/<name>/…            peripheral-level reference sketches — ADC, DAC, PWM
firmware/<cat>/<name>/       prebuilt firmware.bin + manifest.json for browser flashing
examples.json                the manifest tinyStudio reads
examples.pending.json        entries waiting on a HAT repo push
_hat-updates/                docs-current copies of the tinyHAT sketches
tools/                       the generators that build this repo from tinyDocs
docs/PIPELINE.md             how sources are generated
docs/FIRMWARE.md             how firmware is built and served
```

Each project is a standard Arduino sketch folder — folder name matches the
`.ino` name — so it opens in tinyStudio, the Arduino IDE, or `arduino-cli` with
no conversion.

## The tinyHATs stay in their own repos

HAT examples are **not copied here**. Each HAT repo already uses the layout
tinyStudio loads, so `examples.json` points straight at it:

| HAT | Repo | Linked examples |
|---|---|---|
| tinySniff | [`Mister-Industries/tinySniff`](https://github.com/Mister-Industries/tinySniff) | 4 |
| tinySpeak | [`Mister-Industries/tinySpeak`](https://github.com/Mister-Industries/tinySpeak) | 9 |

Push a HAT sketch to its own repo and everyone gets it, with nothing to re-sync
here. `_hat-updates/` exists to make drift between a HAT repo and the docs
visible — see [docs/PIPELINE.md](docs/PIPELINE.md). Their **firmware** is built
here, under `firmware/hats/`, because that is where the flasher looks.

## Prebuilt firmware

```bash
python3 tools/build-firmware.py          # compile everything, ~30s per sketch
python3 tools/build-firmware.py --only blink-basic
```

Images are merged without the ESP32 core's 8 MB flash padding, so a blink build
is ~360 KB rather than 8 MB — 23x smaller, and the flash starts immediately.
[docs/FIRMWARE.md](docs/FIRMWARE.md) covers the flash layout, how a docs page
resolves a firmware URL, and what currently doesn't build.

## Regenerating

```bash
python3 tools/extract-blocks.py       # parse every code block out of tinyDocs
python3 tools/build-examples.py       # write basics/ + advanced/ projects
python3 tools/build-manifest.py       # link the HATs, write examples.json
python3 tools/inject-docs-links.py    # write studioPath + firmwarePath back into the .mdx
python3 tools/verify.py               # check the whole thing lines up
python3 tools/build-firmware.py       # compile every sketch to a flashable image
```

**Edit the docs page, not the `.ino`.** The generators delete and rewrite the
output tree on every run.

---

## The collection

### Basics (50)

| Example | Board | Open |
|---|---|---|
| **Alternating Blink Pattern**<br/><sub>Hint: Try changing the values of the delay() functions to create different speeds.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/blink-alternate) |
| **Appending to a File**<br/><sub>Appending to a File — from the tinyDocs “How to use SD Cards on the tinyCore” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/sdcard-append-file) |
| **Basic beeping code**<br/><sub>But don't worry - the ESP32's PWM system is actually way more powerful and flexible than the…</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/buzzer-basic-beep) |
| **Basic BLE Server Example**<br/><sub>Basic BLE Server Example — from the tinyDocs “Bluetooth Low Energy (BLE)” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/bluetooth-ble-server) |
| **Basic Blink Program**<br/><sub>Both LEDs on your tinyCore should now be flashing On and Off like the GIF above.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/blink-basic) |
| **Basic button reading**<br/><sub>You'll see it constantly telling you whether the button is pressed or not.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/button-press-basic) |
| **Basic Code: Write and Read a File**<br/><sub>Basic Code: Write and Read a File — from the tinyDocs “What is an SD Card?” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/sd-card-write-and-read) |
| **Basic output example**<br/><sub>Make sure the baud rate dropdown (bottom right) is set to 115200 to match your code.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/serial-monitor-basic-output) |
| **Basic Web Server**<br/><sub>Basic Web Server — from the tinyDocs “WiFi” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/wifi-basic-web-server) |
| **Basic WiFi Connection**<br/><sub>Basic WiFi Connection — from the tinyDocs “WiFi” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/wifi-basic-connection) |
| **Code for External LED**<br/><sub>Code for External LED — from the tinyDocs “How to Control LEDs with the tinyCore” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/blink-external-led) |
| **CSV Data Logging**<br/><sub>CSV Data Logging — from the tinyDocs “How to use SD Cards on the tinyCore” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/sdcard-csv-logger) |
| **Debugging with timestamps**<br/><sub>This creates professional-looking debug logs with timestamps, making it easier to understand…</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/serial-monitor-timestamps) |
| **Delete and List Files**<br/><sub>Delete and List Files — from the tinyDocs “How to use SD Cards on the tinyCore” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/sdcard-delete-and-list) |
| **Detecting button events**<br/><sub>Constantly checking if a button is pressed gets annoying fast.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/button-press-events) |
| **Flash the tinyCore**<br/><sub>Our IMU example demonstrates how to initialize the IMU and view it’s data graphed out via th…</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/imu-serial-plotter) |
| **Flash the tinyCore**<br/><sub>Our IMU example demonstrates how to initialize the IMU and view it’s data graphed out via th…</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/imu-motion-plotter) |
| **Hello World (Text on Screen!)**<br/><sub>The tinyCore does all the math in its own memory first, and then blasts the entire finished…</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/i2c-display-hello-world) |
| **Initializing the SD Card**<br/><sub>Initializing the SD Card — from the tinyDocs “How to use SD Cards on the tinyCore” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/sdcard-init) |
| **Interactive buzzer**<br/><sub>Interactive buzzer — from the tinyDocs “How to Control a Buzzer (Analog Output)” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/buzzer-interactive) |
| **Interactive Physics: The IMU Digital Hourglass**<br/><sub>Displaying static text is great, but your tinyCore has a built-in 6DOF IMU!</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/i2c-display-imu-hourglass) |
| **Light sensor (photoresistor)**<br/><sub>An LDR (Light Dependent Resistor) changes its resistance based on how much light hits it.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/read-sensor-photoresistor) |
| **Manual Brightness Control**<br/><sub>Manual Brightness Control — from the tinyDocs “How to Control LEDs with the tinyCore” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/blink-brightness) |
| **Memory and performance monitoring**<br/><sub>Memory and performance monitoring — from the tinyDocs “How to use the Serial Monitor and Ser…</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/serial-monitor-memory-stats) |
| **MQTT Client**<br/><sub>MQTT Client — from the tinyDocs “WiFi” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/wifi-mqtt-client) |
| **Multiple buttons, multiple behaviors**<br/><sub>This gives you two different interaction modes: button 1 toggles the LED state permanently,…</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/button-press-multiple-buttons) |
| **Multiple sensors at once**<br/><sub>Multiple sensors at once — from the tinyDocs “How to Read Sensor Values (Analog Input)” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/read-sensor-multiple-sensors) |
| **Multiple variable plotting**<br/><sub>This creates four different colored lines on the plotter.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/serial-plotter-multi-variable) |
| **On the tinyCore**<br/><sub>ESP-NOW is built into the ESP32-S3 — no libraries to install, no extra hardware.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/esp-now-basic) |
| **OTA (Over-the-Air) Updates**<br/><sub>OTA (Over-the-Air) Updates — from the tinyDocs “WiFi” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/wifi-ota-updates) |
| **Play a real song**<br/><sub>Play a real song — from the tinyDocs “How to Control a Buzzer (Analog Output)” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/buzzer-song) |
| **Playing different tones**<br/><sub>Playing different tones — from the tinyDocs “How to Control a Buzzer (Analog Output)” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/buzzer-tones) |
| **PWM Control for All Three LEDs**<br/><sub>PWM Control for All Three LEDs — from the tinyDocs “How to Control LEDs with the tinyCore” g…</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/blink-pwm-wave) |
| **Reading a potentiometer**<br/><sub>Middle pin of potentiometer → GPIO 1 on tinyCore 3.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/read-sensor-potentiometer) |
| **Reading from a File**<br/><sub>Reading from a File — from the tinyDocs “How to use SD Cards on the tinyCore” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/sdcard-read-file) |
| **Reading input from Serial Monitor**<br/><sub>The Serial Monitor isn't just for output - you can send commands to your tinyCore too.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/serial-monitor-read-input) |
| **Real sensor data visualization**<br/><sub>This example shows how to plot real sensor data alongside simulated signals.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/serial-plotter-sensor-data) |
| **RGB Mood Light Controller**<br/><sub>RGB Mood Light Controller — from the tinyDocs “Bluetooth Low Energy (BLE)” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/bluetooth-rgb-mood-light) |
| **Single variable plotting**<br/><sub>You'll see a beautiful sine wave scrolling across the screen in real-time.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/serial-plotter-single-variable) |
| **Smart LED control**<br/><sub>Cover the sensor to make it "dark" and watch the LED turn on.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/read-sensor-smart-led) |
| **Smooth Breathing Effect**<br/><sub>You should see your LEDs fading off and on smoothly, almost like two fireflies!</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/blink-breathing) |
| **SOS Signal**<br/><sub>SOS Signal — from the tinyDocs “How to Control LEDs with the tinyCore” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/blink-sos) |
| **The Complete Motion Tracker Code**<br/><sub>The Complete Motion Tracker Code — from the tinyDocs “Building Your First Project: A Smart M…</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/motion-tracker) |
| **The I2C Scanner: Your Best Debugging Tool**<br/><sub>An I2C scanner is a short program that checks every possible address (1–127) and reports whi…</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/i2c-scanner) |
| **Toggle behavior vs direct control**<br/><sub>This is like a light switch in your house - press once for on, press again for off.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/button-press-toggle-vs-direct) |
| **Understanding NOT logic**<br/><sub>The LED should be glowing when you're not touching the button, and turn off the moment you p…</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/button-press-not-logic) |
| **Using It in Code**<br/><sub>The tinyCore reads the LSM6DSOX via I2C using the Adafruit LSM6DS Arduino library.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/imu-read-orientation) |
| **Visualizing with Serial Plotter**<br/><sub>Reading numbers is okay, but seeing the data as a graph is way cooler.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/read-sensor-plotter) |
| **WebSocket Server**<br/><sub>WebSocket Server — from the tinyDocs “WiFi” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/wifi-websocket-server) |
| **Writing to a File**<br/><sub>Writing to a File — from the tinyDocs “How to use SD Cards on the tinyCore” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/sdcard-write-file) |

### Advanced (5)

| Example | Board | Open |
|---|---|---|
| **Basic Connection Code**<br/><sub>That IP is what you type into a browser to reach a web server running on the tinyCore.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/advanced/wifi-connect-reference) |
| **Fade an LED**<br/><sub>Fade an LED — from the tinyDocs “What is PWM?” guide.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/advanced/pwm-fade-led) |
| **MCP4725 (I2C, 12-bit)**<br/><sub>One output channel, 4,096 voltage steps, dead-simple I2C interface.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/advanced/dac-mcp4725) |
| **Play a Tone on a Buzzer**<br/><sub>The Arduino analogWrite() and tone() functions don't work on ESP32.</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/advanced/pwm-play-tone-buzzer) |
| **Reading an Analog Value**<br/><sub>The ESP32-S3 stores factory calibration data in its eFuse memory, and analogReadMilliVolts()…</sub> | tinyCore (ESP32-S3) | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/advanced/adc-read-analog) |

### tinyHATs (13 — sources linked from the HAT repos, firmware built here)

| Example | Board | Open |
|---|---|---|
| **tinySniff: Basic Demo**<br/><sub>Reads all three tinySniff MEMS gas sensors and streams them out as a graph.</sub> | tinyCore + tinySniff HAT | [open](https://app.tinystudio.cc/Mister-Industries/tinySniff/Software/Arduino/Examples/tinySniff_Monitor) |
| **tinySniff: Google Sheets**<br/><sub>Logs all three tinySniff gas sensors to a Google Sheet in real time over WiFi.</sub> | tinyCore + tinySniff HAT | [open](https://app.tinystudio.cc/Mister-Industries/tinySniff/Software/Arduino/Examples/tinySniff_Sheets) |
| **tinySniff: SD Card Logger**<br/><sub>Logs all three tinySniff MEMS gas sensors to a timestamped CSV file on the SD card.</sub> | tinyCore + tinySniff HAT | [open](https://app.tinystudio.cc/Mister-Industries/tinySniff/Software/Arduino/Examples/tinySniff_SDLogger) |
| **tinySniff: Text Notifications**<br/><sub>Monitors all three tinySniff gas sensors against configurable thresholds and sends an email…</sub> | tinyCore + tinySniff HAT | [open](https://app.tinystudio.cc/Mister-Industries/tinySniff/Software/Arduino/Examples/tinySniff_Alarm) |
| **tinySpeak: tinyAIText**<br/><sub>A text-based AI assistant.</sub> | tinyCore + tinySpeak HAT | [open](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyAIText) |
| **tinySpeak: tinyAIVoice**<br/><sub>Full Voice Assistant Pipeline.</sub> | tinyCore + tinySpeak HAT | [open](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyAIVoice) |
| **tinySpeak: tinyAIVoice (ElevenLabs)**<br/><sub>Premium Voice Assistant Pipeline using ElevenLabs TTS.</sub> | tinyCore + tinySpeak HAT | [open](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyAIVoice_EL) |
| **tinySpeak: tinyMP3Player**<br/><sub>Plays MP3 files from the SD card.</sub> | tinyCore + tinySpeak HAT | [open](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyMP3Player) |
| **tinySpeak: tinyRecorder**<br/><sub>A standalone voice recorder.</sub> | tinyCore + tinySpeak HAT | [open](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyRecorder) |
| **tinySpeak: tinySoundboard**<br/><sub>A motion-triggered soundboard.</sub> | tinyCore + tinySpeak HAT | [open](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinySoundboard) |
| **tinySpeak: tinyTheremin**<br/><sub>A motion-controlled musical instrument.</sub> | tinyCore + tinySpeak HAT | [open](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyTheremin) |
| **tinySpeak: tinyWalkieTalkie**<br/><sub>Push-to-Talk Intercom using ESP-NOW.</sub> | tinyCore + tinySpeak HAT | [open](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyWalkieTalkie) |
| **tinySpeak: tinyWebSynth**<br/><sub>Chiptune synthesizer: live piano, 2-track melodic step sequencer, 3-track drum machine (Kick…</sub> | tinyCore + tinySpeak HAT | [open](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyWebSynth) |

### tinyStudio demos (3 — with Circuit + Visual views)

| Example | Board | Open |
|---|---|---|
| **Blink LED (Circuit + Visual)**<br/><sub>Blink the onboard LED and mirror its state in the Visual view.</sub> | tinyCore / Arduino | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio/demo/Blink Example) |
| **Fade LED (Circuit + Visual)**<br/><sub>PWM-fade an LED and chart the brightness curve live.</sub> | tinyCore / Arduino | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio/demo/Fade Example) |
| **Joystick (Circuit + Visual)**<br/><sub>Read a Qwiic joystick and visualize the stick position.</sub> | tinyCore + Qwiic Joystick | [open](https://app.tinystudio.cc/Mister-Industries/tinyStudio/demo/Joystick Example) |

---

GPL-3.0, same as tinyStudio. Questions →
[support@mr.industries](mailto:support@mr.industries) or
[Discord](https://discord.gg/hvJZhwfQsF).
