# tinyWebSynth

A chiptune synthesizer with a browser-based UI. The ESP32 runs a local web server and WebSocket endpoint. Connect to its IP address from any device on the same WiFi network and you get a full musical interface: a live piano keyboard, a two-track melodic step sequencer, and a three-track drum machine with kick, snare, and hi-hat. All audio is generated on the ESP32 — the browser is purely a controller.

The audio engine runs five simultaneous channels with selectable waveforms (square, sawtooth, pulse), per-channel envelope control, and configurable BPM. Export your composition as a WAV file to the SD card from the Serial Monitor. Songs are saved in the browser's localStorage between sessions.

On first boot the demo will prompt you for your WiFi credentials through the Serial Monitor.

  **WiFi network** (local only, no internet)

  **SD card** (optional, for WAV export)

  **Libraries:** ESP Async WebServer, AsyncTCP

{/* TODO: manifest needs to be compiled at /firmware/examples/tinyspeak/tinyWebSynth/manifest.json */}

  Open the Serial Monitor at **115200 baud**. The demo will prompt you for your WiFi credentials on first boot, then print the IP address to connect to from your browser.

---

## Open it

- **tinyStudio (web)** — [open this project](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyWebSynth)
- **tinyStudio (desktop)** — Examples tab → *tinyWebSynth*
- **Arduino IDE** — open `tinyWebSynth/tinyWebSynth.ino`

## Where this came from

From the tinyDocs page [Example Code](https://tinydocs.cc/3_tiny-hats/tinyspeak/example-code/).

Section: *tinyWebSynth*

## Files

```
tinyWebSynth/
  tinyWebSynth.ino   ← the sketch
  README.md
```

---

_Generated from tinyDocs by `tools/sync-examples.py`. Edit the docs page above, not this file — regenerating overwrites it._
