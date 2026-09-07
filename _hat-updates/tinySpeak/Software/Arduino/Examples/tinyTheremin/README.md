# tinyTheremin

---

A motion-controlled musical instrument. Tilt the board left and right to change pitch (200–1000 Hz) and tilt forward and back to change volume. Audio is generated in real time as a pure sine wave, synthesized sample-by-sample and pushed directly to the speaker over I2S — no audio files involved.

The demo auto-calibrates on boot (hold the board flat and still during startup). Recalibrate anytime by pressing `c`. The RX button acts as a mute toggle.

This is the only demo that drives I2S **directly using the ESP-IDF driver** rather than the Audio library — a useful reference if you want to understand raw I2S audio synthesis on the ESP32-S3.

  Nothing beyond tinyCore + tinySpeak

  **Libraries:** Adafruit LSM6DS, Adafruit Unified Sensor

Our intelligent code snippets let you flash a tinyCore from the web.

  Click the **Flash tinyCore** button above!

---

## Open it

- **tinyStudio (web)** — [open this project](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyTheremin)
- **tinyStudio (desktop)** — Examples tab → *tinyTheremin*
- **Arduino IDE** — open `tinyTheremin/tinyTheremin.ino`

## Where this came from

From the tinyDocs page [Example Code](https://tinydocs.cc/3_tiny-hats/tinyspeak/example-code/).

Section: *tinyTheremin*

> This sketch was one-shot by Claude Sonnet 4.5 and checked by hand.

## Files

```
tinyTheremin/
  tinyTheremin.ino   ← the sketch
  README.md
```

---

_Generated from tinyDocs by `tools/sync-examples.py`. Edit the docs page above, not this file — regenerating overwrites it._
