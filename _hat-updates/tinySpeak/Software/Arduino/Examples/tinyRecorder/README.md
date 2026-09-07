# tinyRecorder

---

A standalone voice recorder that captures audio from the MEMS microphone and saves it as a standard 16-bit 16kHz WAV file on the SD card. Hold the RX button to record and release to stop — the recording is saved to `/recording.wav` and can be played back immediately by pressing `p`.

WAV files are standard PCM format, so you can pull the SD card and open them on any computer.

  **SD card**

  **RX button** recommended (or use `r` in Serial Monitor)

  **Libraries:** ESP32-audioI2S

Our intelligent code snippets let you flash a tinyCore from the web.

  Click the **Flash tinyCore** button above!

**Serial Monitor Controls**

---

## Open it

- **tinyStudio (web)** — [open this project](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyRecorder)
- **tinyStudio (desktop)** — Examples tab → *tinyRecorder*
- **Arduino IDE** — open `tinyRecorder/tinyRecorder.ino`

## Where this came from

From the tinyDocs page [Example Code](https://tinydocs.cc/3_tiny-hats/tinyspeak/example-code/).

Section: *tinyRecorder*

> This sketch was one-shot by Claude Sonnet 4.5 and checked by hand.

## Files

```
tinyRecorder/
  tinyRecorder.ino   ← the sketch
  README.md
```

---

_Generated from tinyDocs by `tools/sync-examples.py`. Edit the docs page above, not this file — regenerating overwrites it._
