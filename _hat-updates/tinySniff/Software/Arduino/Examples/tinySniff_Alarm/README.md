# Text Notifications

---

Watches all three channels against thresholds you set. If one goes over, the tinyCore emails you over SMTP. Point that email at your carrier's SMS gateway and it arrives as a text.

  **WiFi**, 2.4GHz only

  **An SMTP account.** Gmail works, but needs an [App Password](https://myaccount.google.com/apppasswords), not your normal password. The sketch header walks through generating one.

  **Libraries:** ESP Mail Client, by Mobizt

<SerialTerminal baudRate={115200} mode="console" client:visible />

Send a test email with `e` before you trust it. SMTP fails for boring reasons: wrong port, App Password not generated, provider blocking an unfamiliar IP. If it fails, flip `smtp.debug(0)` to `smtp.debug(1)` and the library will tell you where the handshake died.

## Open it

- **tinyStudio (web)** — [open this project](https://app.tinystudio.cc/Mister-Industries/tinySniff/Software/Arduino/Examples/tinySniff_Alarm)
- **tinyStudio (desktop)** — Examples tab → *Text Notifications*
- **Arduino IDE** — open `tinySniff_Alarm/tinySniff_Alarm.ino`

## Where this came from

From the tinyDocs page [Example Code](https://tinydocs.cc/3_tiny-hats/tinysniff/example-code/).

Section: *Text Notifications*

> This sketch was one-shot by Claude Opus 4.5 and checked by hand.

## Files

```
tinySniff_Alarm/
  tinySniff_Alarm.ino   ← the sketch
  README.md
```

---

_Generated from tinyDocs by `tools/sync-examples.py`. Edit the docs page above, not this file — regenerating overwrites it._
