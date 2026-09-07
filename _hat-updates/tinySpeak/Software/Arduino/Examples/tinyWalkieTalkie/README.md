# tinyWalkieTalkie

---

A push-to-talk intercom that streams live audio between two or more tinySpeak units using **ESP-NOW** — Espressif's low-latency peer-to-peer protocol. No WiFi router, no internet connection, no server required.

Audio is captured from the microphone at 8kHz, packed into 240-byte ESP-NOW frames, and broadcast to all nearby tinySpeak devices on the same channel. Incoming packets are written directly into the speaker's I2S DMA buffer for immediate playback. Hold RX to transmit, release to listen.

Press `c` in the Serial Monitor to cycle through WiFi channels 1–11. All units must be on the same channel to hear each other.

  **2+ tinyCore + tinySpeak units**, each with RX button installed

  **No SD card needed**

  **Libraries:** None (WiFi and esp_now are built-in)

Our intelligent code snippets let you flash a tinyCore from the web.

  Click the **Flash tinyCore** button above!

---

## Open it

- **tinyStudio (web)** — [open this project](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyWalkieTalkie)
- **tinyStudio (desktop)** — Examples tab → *tinyWalkieTalkie*
- **Arduino IDE** — open `tinyWalkieTalkie/tinyWalkieTalkie.ino`

## Where this came from

From the tinyDocs page [Example Code](https://tinydocs.cc/3_tiny-hats/tinyspeak/example-code/).

Section: *tinyWalkieTalkie*

> This sketch was one-shot by Claude Sonnet 4.5 and checked by hand.

## Files

```
tinyWalkieTalkie/
  tinyWalkieTalkie.ino   ← the sketch
  README.md
```

---

_Generated from tinyDocs by `tools/sync-examples.py`. Edit the docs page above, not this file — regenerating overwrites it._
