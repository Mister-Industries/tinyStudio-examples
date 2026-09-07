# SD Card Logger

---

Writes a CSV to the micro SD card instead of your screen. Leave it running for a day and pull the card into a spreadsheet. A new file (`/LOG_0001.CSV` upward) is created every boot, so power-cycling never overwrites yesterday's run.

  **SD card** formatted FAT32

  **Libraries:** none, `SD` and `FS` ship with the ESP32 core

<SerialTerminal baudRate={115200} mode="console" client:visible />

## Open it

- **tinyStudio (web)** — [open this project](https://app.tinystudio.cc/Mister-Industries/tinySniff/Software/Arduino/Examples/tinySniff_SDLogger)
- **tinyStudio (desktop)** — Examples tab → *SD Card Logger*
- **Arduino IDE** — open `tinySniff_SDLogger/tinySniff_SDLogger.ino`

## Where this came from

From the tinyDocs page [Example Code](https://tinydocs.cc/3_tiny-hats/tinysniff/example-code/).

Section: *SD Card Logger*

> This sketch was one-shot by Claude Opus 4.5 and checked by hand.

## Files

```
tinySniff_SDLogger/
  tinySniff_SDLogger.ino   ← the sketch
  README.md
```

---

_Generated from tinyDocs by `tools/sync-examples.py`. Edit the docs page above, not this file — regenerating overwrites it._
