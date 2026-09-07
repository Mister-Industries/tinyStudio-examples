# Google Sheets

**WiFi**, 2.4GHz only. Set `WIFI_SSID` and `WIFI_PASS` at the top of the sketch.

  **A Google account** and a spreadsheet

  **Libraries:** none, `WiFi`, `HTTPClient`, and `Preferences` ship with the ESP32 core

1. Make a new Google Sheet, then go to **Extensions → Apps Script**. Delete what's in the editor and paste in the `doGet` function from the comment block at the top of the sketch below.

2. Click **Deploy → New deployment**, type **Web app**. Set **Execute as** to *Me* and **Who has access** to *Anyone*.

    That second setting means anyone who knows the URL can add a row. The URL is a long random string and is the only credential, so treat it like a password.

3. Click **Deploy**, authorize when Google asks, and copy the **Web app URL**.

4. Fill in your WiFi details, upload, and open the console below. On first boot the sketch asks you to paste that URL. It's saved to flash and you won't be asked again.

<SerialTerminal baudRate={115200} mode="console" client:visible />

Press `r` first. If a row lands in your sheet, everything downstream works.

## Open it

- **tinyStudio (web)** — [open this project](https://app.tinystudio.cc/Mister-Industries/tinySniff/Software/Arduino/Examples/tinySniff_Sheets)
- **tinyStudio (desktop)** — Examples tab → *Google Sheets*
- **Arduino IDE** — open `tinySniff_Sheets/tinySniff_Sheets.ino`

## Where this came from

From the tinyDocs page [Example Code](https://tinydocs.cc/3_tiny-hats/tinysniff/example-code/).

Section: *Google Sheets*

> This sketch was one-shot by Claude Opus 4.5 and checked by hand.

## Files

```
tinySniff_Sheets/
  tinySniff_Sheets.ino   ← the sketch
  README.md
```

---

_Generated from tinyDocs by `tools/sync-examples.py`. Edit the docs page above, not this file — regenerating overwrites it._
