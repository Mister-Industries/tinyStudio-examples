# tinyAIVoice (ElevenLabs)

A premium voice assistant that replaces OpenAI's TTS engine with **ElevenLabs** for higher-quality, more natural-sounding speech synthesis. The pipeline is otherwise identical to tinyAIVoice: hold the button to record, release to process through Whisper (speech-to-text), ChatGPT (intelligence), and ElevenLabs (text-to-speech).

ElevenLabs offers a wide variety of voice options and supports voice cloning. The demo defaults to the "Arthur" voice, but you can change the voice ID through the configuration wizard. To find voice IDs, browse the ElevenLabs voice library and copy the ID from your chosen voice's page.

The configuration wizard asks for five values: WiFi SSID, WiFi password, OpenAI API key (for Whisper and ChatGPT), ElevenLabs API key, and ElevenLabs voice ID.

  **SD card**

  **WiFi**

  **OpenAI API key**

  **ElevenLabs API key**

  **RX button** recommended

  **Libraries:** ESP32-audioI2S, ArduinoJson

  See [WiFi & API Key Configuration](#wifi--api-key-configuration) below for setup instructions.

Our intelligent code snippets let you flash a tinyCore from the web.

  Click the **Flash tinyCore** button above!

**Serial Monitor Controls**

---

## Open it

- **tinyStudio (web)** — [open this project](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyAIVoice_EL)
- **tinyStudio (desktop)** — Examples tab → *tinyAIVoice (ElevenLabs)*
- **Arduino IDE** — open `tinyAIVoice_EL/tinyAIVoice_EL.ino`

## Where this came from

From the tinyDocs page [Example Code](https://tinydocs.cc/3_tiny-hats/tinyspeak/example-code/).

Section: *tinyAIVoice (ElevenLabs)*

## Files

```
tinyAIVoice_EL/
  tinyAIVoice_EL.ino   ← the sketch
  README.md
```

---

_Generated from tinyDocs by `tools/sync-examples.py`. Edit the docs page above, not this file — regenerating overwrites it._
