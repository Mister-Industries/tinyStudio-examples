# tinyAIText

---

A text-based AI assistant. Type a question into the Serial Monitor, and the ESP32 sends it to OpenAI's ChatGPT API (GPT-4o-mini), converts the text response to speech using OpenAI TTS, saves the MP3 to the SD card, and plays it through the speaker. Text in, voice out — no browser or companion app needed.

This is the simplest of the three AI demos because it skips the microphone entirely. It's a good starting point for understanding the OpenAI API integration before adding voice input.

  **SD card**

  **WiFi**

  **OpenAI API key**

  **Libraries:** ESP32-audioI2S, ArduinoJson

  See [WiFi & API Key Configuration](#wifi--api-key-configuration) below for setup instructions.

On first boot, a configuration wizard will walk you through entering your WiFi SSID, password, and OpenAI API key. These are saved to flash and persist across reboots. Press `c` at any time to reconfigure.

Our intelligent code snippets let you flash a tinyCore from the web.

  Click the **Flash tinyCore** button above!

**Serial Monitor Controls**

---

## Open it

- **tinyStudio (web)** — [open this project](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyAIText)
- **tinyStudio (desktop)** — Examples tab → *tinyAIText*
- **Arduino IDE** — open `tinyAIText/tinyAIText.ino`

## Where this came from

From the tinyDocs page [Example Code](https://tinydocs.cc/3_tiny-hats/tinyspeak/example-code/).

Section: *tinyAIText*

> This sketch was one-shot by Claude Sonnet 4.5 and checked by hand.

## Files

```
tinyAIText/
  tinyAIText.ino   ← the sketch
  README.md
```

---

_Generated from tinyDocs by `tools/sync-examples.py`. Edit the docs page above, not this file — regenerating overwrites it._
