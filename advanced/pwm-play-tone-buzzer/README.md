# Play a Tone on a Buzzer

For buzzers, `ledcWriteTone()` sets the frequency directly:

**The Arduino `analogWrite()` and `tone()` functions don't work on ESP32.** The LEDC functions (`ledcAttach`, `ledcWrite`, `ledcWriteTone`, `ledcDetach`) are more powerful and flexible — they just have different names. Every ESP32 PWM tutorial will use these functions.

Older tutorials (and most AI-generated code) still use `ledcSetup()` and `ledcAttachPin()`, where you picked a channel number yourself. Espressif removed those in Arduino-ESP32 **3.0.x** and folded them into `ledcAttach()`, which allocates a channel for you — so every LEDC call now takes the **pin**, not a channel. If you see *'ledcSetup' was not declared in this scope*, that's what happened.

## Open it

- **tinyStudio (web)** — [open this project](https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/advanced/pwm-play-tone-buzzer)
- **tinyStudio (desktop)** — Examples tab → *Play a Tone on a Buzzer*
- **Arduino IDE** — open `pwm-play-tone-buzzer/pwm-play-tone-buzzer.ino`

## Where this came from

From the tinyDocs page [What is PWM?](https://tinydocs.cc/5_reference/advanced/pwm/).

Section: *On the tinyCore (ESP32-S3) › Example: Play a Tone on a Buzzer*

## Files

```
pwm-play-tone-buzzer/
  pwm-play-tone-buzzer.ino   ← the sketch
  README.md
```

---

_Generated from tinyDocs by `tools/sync-examples.py`. Edit the docs page above, not this file — regenerating overwrites it._
