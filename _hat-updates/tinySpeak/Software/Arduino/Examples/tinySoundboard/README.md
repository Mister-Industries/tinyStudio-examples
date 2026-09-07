# tinySoundboard

---

A motion-triggered soundboard that plays sound effects when you shake the board. It reads the tinyCore's built-in LSM6DSO IMU to detect a shake gesture — when acceleration exceeds a configurable threshold, it fires off the current sound effect from the SD card.

Load `.mp3` or `.wav` files into the root of your SD card and tinySoundboard picks them up automatically. You can also trigger sounds with the RX button or cycle through files from the Serial Monitor.

  **SD card** with `.mp3`/`.wav` files

  **Libraries:** ESP32-audioI2S, Adafruit LSM6DS, Adafruit Unified Sensor

Our intelligent code snippets let you flash a tinyCore from the web.

  Click the **Flash tinyCore** button above!

---

## Open it

- **tinyStudio (web)** — [open this project](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinySoundboard)
- **tinyStudio (desktop)** — Examples tab → *tinySoundboard*
- **Arduino IDE** — open `tinySoundboard/tinySoundboard.ino`

## Where this came from

From the tinyDocs page [Example Code](https://tinydocs.cc/3_tiny-hats/tinyspeak/example-code/).

Section: *tinySoundboard*

> This sketch was one-shot by Claude Sonnet 4.5 and checked by hand.

## Files

```
tinySoundboard/
  tinySoundboard.ino   ← the sketch
  README.md
```

---

_Generated from tinyDocs by `tools/sync-examples.py`. Edit the docs page above, not this file — regenerating overwrites it._
