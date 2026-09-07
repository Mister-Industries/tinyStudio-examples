# tinyAIVoice

A full voice-in, voice-out AI assistant. Hold the RX button and speak your question, release the button, and the device runs a three-stage pipeline: your speech is transcribed by OpenAI Whisper (speech-to-text), the transcript is sent to ChatGPT for a response, and the reply is spoken aloud using OpenAI TTS. The entire round trip typically completes in a few seconds.

Audio is recorded to the SD card as a WAV file before being uploaded to Whisper, and the TTS response is streamed directly to SD as an MP3 before playback. This avoids buffering large audio payloads in the ESP32's limited RAM.

If you don't have the RX button installed, toggle recording with the `r` command in the Serial Monitor.

  **SD card**

  **WiFi**

  **OpenAI API key**

  **RX button** recommended

  **Libraries:** ESP32-audioI2S, ArduinoJson

  See [WiFi & API Key Configuration](#wifi--api-key-configuration) below for setup instructions.

Our intelligent code snippets let you flash a tinyCore from the web.

  Click the **Flash tinyCore** button above!

**Serial Monitor Controls**

---

## Open it

- **tinyStudio (web)** — [open this project](https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyAIVoice)
- **tinyStudio (desktop)** — Examples tab → *tinyAIVoice*
- **Arduino IDE** — open `tinyAIVoice/tinyAIVoice.ino`

## Where this came from

From the tinyDocs page [Example Code](https://tinydocs.cc/3_tiny-hats/tinyspeak/example-code/).

Section: *tinyAIVoice*

## Files

```
tinyAIVoice/
  tinyAIVoice.ino   ← the sketch
  README.md
```

---

_Generated from tinyDocs by `tools/sync-examples.py`. Edit the docs page above, not this file — regenerating overwrites it._
