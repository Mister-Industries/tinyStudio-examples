#!/usr/bin/env python3
"""
Move the tinyDocs PWM/buzzer code off the ESP32 core 2.x LEDC API.

Espressif removed ledcSetup()/ledcAttachPin()/ledcDetachPin() in Arduino-ESP32
3.0.x: the channel is now allocated for you and every call is addressed by PIN.

  ledcSetup(ch, freq, res); ledcAttachPin(pin, ch);  ->  ledcAttach(pin, freq, res);
  ledcWrite(ch, duty)                                ->  ledcWrite(pin, duty)
  ledcWriteTone(ch, hz)                              ->  ledcWriteTone(pin, hz)
  ledcDetachPin(pin)                                 ->  ledcDetach(pin)

The blink-led page was already on the new API — only its troubleshooting note
mentions ledcSetup, and that has to stay (it's explaining the error).
"""
import os, sys

DOCS = os.path.expanduser("~/mnt/site-tinydocs-cc/src/content/docs")

EDITS = {
"2_tiny-core/basics/buzz-buzzer.mdx": [
# ---- Step 2: basic beep -------------------------------------------------
("""const int buzzerPin = 2;        // GPIO pin connected to buzzer
const int pwmChannel = 0;       // PWM channel (ESP32 has 16 channels)
const int resolution = 8;       // 8-bit resolution (0-255 values)

void setup() {
  Serial.begin(115200);
  
  // Configure the PWM channel
  ledcSetup(pwmChannel, 1000, resolution);  // 1000 Hz frequency, 8-bit resolution
  
  // Attach the PWM channel to our buzzer pin
  ledcAttachPin(buzzerPin, pwmChannel);
  
  Serial.println("Buzzer ready! Making some noise...");
}

void loop() {
  // Play a 1000 Hz tone
  ledcWriteTone(pwmChannel, 1000);
  delay(500);  // Beep for half a second
  
  // Stop the sound
  ledcWriteTone(pwmChannel, 0);
  delay(500);  // Silence for half a second
}""",
"""const int buzzerPin = 2;        // GPIO pin connected to buzzer
const int resolution = 8;       // 8-bit resolution (0-255 values)

void setup() {
  Serial.begin(115200);
  
  // Set up PWM on the buzzer pin: 1000 Hz, 8-bit resolution.
  // A hardware channel is allocated for you — you address the pin from here on.
  ledcAttach(buzzerPin, 1000, resolution);
  
  Serial.println("Buzzer ready! Making some noise...");
}

void loop() {
  // Play a 1000 Hz tone
  ledcWriteTone(buzzerPin, 1000);
  delay(500);  // Beep for half a second
  
  // Stop the sound
  ledcWriteTone(buzzerPin, 0);
  delay(500);  // Silence for half a second
}"""),
# ---- Step 3: scale ------------------------------------------------------
("""const int pwmChannel = 0;
const int resolution = 8;

// Musical note frequencies (in Hz)""",
"""const int resolution = 8;

// Musical note frequencies (in Hz)"""),
("""  ledcSetup(pwmChannel, 2000, resolution);
  ledcAttachPin(buzzerPin, pwmChannel);
  
  Serial.println("Playing musical scale...");""",
"""  ledcAttach(buzzerPin, 2000, resolution);
  
  Serial.println("Playing musical scale...");"""),
("""  if (frequency > 0) {
    ledcWriteTone(pwmChannel, frequency);
  } else {
    ledcWriteTone(pwmChannel, 0);  // Rest (silence)
  }
  delay(duration);
  ledcWriteTone(pwmChannel, 0);  // Stop sound""",
"""  if (frequency > 0) {
    ledcWriteTone(buzzerPin, frequency);
  } else {
    ledcWriteTone(buzzerPin, 0);  // Rest (silence)
  }
  delay(duration);
  ledcWriteTone(buzzerPin, 0);  // Stop sound"""),
# ---- Step 4: song -------------------------------------------------------
("""  ledcSetup(pwmChannel, 2000, resolution);
  ledcAttachPin(buzzerPin, pwmChannel);
  
  Serial.println("Playing Twinkle Twinkle Little Star!");""",
"""  ledcAttach(buzzerPin, 2000, resolution);
  
  Serial.println("Playing Twinkle Twinkle Little Star!");"""),
("""    if (melody[i] > 0) {
      ledcWriteTone(pwmChannel, melody[i]);
    } else {
      ledcWriteTone(pwmChannel, 0);  // Rest
    }
    
    delay(noteDurations[i]);
    ledcWriteTone(pwmChannel, 0);  // Stop sound""",
"""    if (melody[i] > 0) {
      ledcWriteTone(buzzerPin, melody[i]);
    } else {
      ledcWriteTone(buzzerPin, 0);  // Rest
    }
    
    delay(noteDurations[i]);
    ledcWriteTone(buzzerPin, 0);  // Stop sound"""),
# ---- Step 5: interactive ------------------------------------------------
("""const int buzzerPin = 2;
const int pwmChannel = 0;
const int resolution = 8;

void setup() {
  Serial.begin(115200);
  ledcSetup(pwmChannel, 2000, resolution);
  ledcAttachPin(buzzerPin, pwmChannel);
  
  Serial.println("=== Interactive Buzzer Control ===");""",
"""const int buzzerPin = 2;
const int resolution = 8;

void setup() {
  Serial.begin(115200);
  ledcAttach(buzzerPin, 2000, resolution);
  
  Serial.println("=== Interactive Buzzer Control ===");"""),
("""void playNote(int frequency, int duration) {
  ledcWriteTone(pwmChannel, frequency);
  delay(duration);
  ledcWriteTone(pwmChannel, 0);
}

void playSiren() {
  for (int freq = 400; freq < 2000; freq += 50) {
    ledcWriteTone(pwmChannel, freq);
    delay(20);
  }
  for (int freq = 2000; freq > 400; freq -= 50) {
    ledcWriteTone(pwmChannel, freq);
    delay(20);
  }
  ledcWriteTone(pwmChannel, 0);
}

void playR2D2() {
  for (int i = 0; i < 5; i++) {
    ledcWriteTone(pwmChannel, 1000 + (i * 200));
    delay(100);
    ledcWriteTone(pwmChannel, 800 - (i * 100));
    delay(100);
  }
  ledcWriteTone(pwmChannel, 0);
}""",
"""void playNote(int frequency, int duration) {
  ledcWriteTone(buzzerPin, frequency);
  delay(duration);
  ledcWriteTone(buzzerPin, 0);
}

void playSiren() {
  for (int freq = 400; freq < 2000; freq += 50) {
    ledcWriteTone(buzzerPin, freq);
    delay(20);
  }
  for (int freq = 2000; freq > 400; freq -= 50) {
    ledcWriteTone(buzzerPin, freq);
    delay(20);
  }
  ledcWriteTone(buzzerPin, 0);
}

void playR2D2() {
  for (int i = 0; i < 5; i++) {
    ledcWriteTone(buzzerPin, 1000 + (i * 200));
    delay(100);
    ledcWriteTone(buzzerPin, 800 - (i * 100));
    delay(100);
  }
  ledcWriteTone(buzzerPin, 0);
}"""),
("""        ledcWriteTone(pwmChannel, 0);""",
 """        ledcWriteTone(buzzerPin, 0);"""),
# ---- prose --------------------------------------------------------------
("""ledcSetup(pwmChannel, 2000, resolution);  // Configure PWM channel
ledcAttachPin(buzzerPin, pwmChannel);     // Connect channel to GPIO pin""",
"""ledcAttach(buzzerPin, 2000, resolution);  // Set up PWM on this pin"""),
("""ledcWriteTone(pwmChannel, frequency);  // Play a frequency
ledcWriteTone(pwmChannel, 0);          // Stop sound (frequency = 0)""",
"""ledcWriteTone(buzzerPin, frequency);  // Play a frequency
ledcWriteTone(buzzerPin, 0);          // Stop sound (frequency = 0)"""),
("""- You can try adjusting the duty cycle with `ledcWrite(channel, 128)` instead of `ledcWriteTone()`""",
 """- You can try adjusting the duty cycle with `ledcWrite(buzzerPin, 128)` instead of `ledcWriteTone()`"""),
("""- This can happen with some buzzers - try `ledcDetachPin(buzzerPin)` to completely disconnect""",
 """- This can happen with some buzzers - try `ledcDetach(buzzerPin)` to completely disconnect"""),
],

"5_reference/advanced/pwm.mdx": [
("""// Step 1: Configure a PWM channel
ledcSetup(channel, frequency, resolution);
// channel: 0–7 (which PWM channel to configure)
// frequency: in Hz (e.g., 5000 for LEDs, 50 for servos)
// resolution: bit depth (e.g., 8 = 256 steps, 13 = 8192 steps)

// Step 2: Attach the channel to a GPIO pin
ledcAttachPin(pin, channel);

// Step 3: Set the duty cycle
ledcWrite(channel, dutyCycle);
// dutyCycle: 0 to (2^resolution - 1)
// For 8-bit: 0–255. For 13-bit: 0–8191.""",
"""// Step 1: Set up PWM on a pin (a free channel is allocated for you)
ledcAttach(pin, frequency, resolution);
// pin: the GPIO to drive
// frequency: in Hz (e.g., 5000 for LEDs, 50 for servos)
// resolution: bit depth (e.g., 8 = 256 steps, 13 = 8192 steps)

// Step 2: Set the duty cycle — addressed by PIN, not by channel
ledcWrite(pin, dutyCycle);
// dutyCycle: 0 to (2^resolution - 1)
// For 8-bit: 0–255. For 13-bit: 0–8191.

// When you're done with the pin
ledcDetach(pin);"""),
("""const int ledPin = 21;     // LED_BOOT on tinyCore
const int channel = 0;
const int freq = 5000;     // 5 kHz — no visible flicker
const int resolution = 8;  // 8-bit: 0–255

void setup() {
  ledcSetup(channel, freq, resolution);
  ledcAttachPin(ledPin, channel);
}

void loop() {
  // Fade up
  for (int duty = 0; duty <= 255; duty++) {
    ledcWrite(channel, duty);
    delay(10);
  }
  // Fade down
  for (int duty = 255; duty >= 0; duty--) {
    ledcWrite(channel, duty);
    delay(10);
  }
}""",
"""const int ledPin = 21;     // LED_BOOT on tinyCore
const int freq = 5000;     // 5 kHz — no visible flicker
const int resolution = 8;  // 8-bit: 0–255

void setup() {
  ledcAttach(ledPin, freq, resolution);
}

void loop() {
  // Fade up
  for (int duty = 0; duty <= 255; duty++) {
    ledcWrite(ledPin, duty);
    delay(10);
  }
  // Fade down
  for (int duty = 255; duty >= 0; duty--) {
    ledcWrite(ledPin, duty);
    delay(10);
  }
}"""),
("""const int buzzerPin = 2;
const int channel = 0;

void setup() {
  ledcSetup(channel, 1000, 8);
  ledcAttachPin(buzzerPin, channel);
}

void loop() {
  ledcWriteTone(channel, 440);   // play A4 (440 Hz)
  delay(500);
  ledcWriteTone(channel, 523);   // play C5 (523 Hz)
  delay(500);
  ledcWriteTone(channel, 0);     // silence
  delay(500);
}""",
"""const int buzzerPin = 2;

void setup() {
  ledcAttach(buzzerPin, 1000, 8);
}

void loop() {
  ledcWriteTone(buzzerPin, 440);   // play A4 (440 Hz)
  delay(500);
  ledcWriteTone(buzzerPin, 523);   // play C5 (523 Hz)
  delay(500);
  ledcWriteTone(buzzerPin, 0);     // silence
  delay(500);
}"""),
("""**The Arduino `analogWrite()` and `tone()` functions don't work on ESP32.** The LEDC functions (`ledcSetup`, `ledcAttachPin`, `ledcWrite`, `ledcWriteTone`) are more powerful and flexible — they just have different names. Every ESP32 PWM tutorial will use these functions.""",
"""**The Arduino `analogWrite()` and `tone()` functions don't work on ESP32.** The LEDC functions (`ledcAttach`, `ledcWrite`, `ledcWriteTone`, `ledcDetach`) are more powerful and flexible — they just have different names. Every ESP32 PWM tutorial will use these functions.

Older tutorials (and most AI-generated code) still use `ledcSetup()` and `ledcAttachPin()`, where you picked a channel number yourself. Espressif removed those in Arduino-ESP32 **3.0.x** and folded them into `ledcAttach()`, which allocates a channel for you — so every LEDC call now takes the **pin**, not a channel. If you see *'ledcSetup' was not declared in this scope*, that's what happened."""),
("""| Key functions | `ledcSetup()`, `ledcAttachPin()`, `ledcWrite()` |
| Tone function | `ledcWriteTone(channel, frequency)` |""",
"""| Key functions | `ledcAttach()`, `ledcWrite()`, `ledcDetach()` |
| Tone function | `ledcWriteTone(pin, frequency)` |"""),
],
}

def main():
    total = 0
    for rel, edits in EDITS.items():
        path = os.path.join(DOCS, rel)
        raw = open(path, encoding="utf-8", newline="").read()
        nl = "\r\n" if "\r\n" in raw else "\n"
        src = raw.replace("\r\n", "\n")
        for old, new in edits:
            n = src.count(old)
            if n != 1:
                print(f"ABORT {rel}: pattern matched {n} times, expected 1:\n"
                      f"  {old.splitlines()[0][:70]!r}")
                return 1
            src = src.replace(old, new, 1)
            total += 1
        open(path, "w", encoding="utf-8", newline="").write(
            src.replace("\n", nl) if nl == "\r\n" else src)
        print(f"{rel}: {len(edits)} edits applied")
    print(f"\n{total} edits total")

    leftovers = []
    for root, dirs, files in os.walk(DOCS):
        dirs[:] = [d for d in dirs if d not in ("_templates", "assets")]
        for fn in files:
            if not fn.endswith(".mdx"): continue
            p = os.path.join(root, fn)
            for i, line in enumerate(open(p, encoding="utf-8"), 1):
                if any(k in line for k in ("ledcSetup", "ledcAttachPin", "ledcDetachPin")):
                    leftovers.append(f"{os.path.relpath(p, DOCS)}:{i}: {line.strip()[:90]}")
    print("\nremaining old-API mentions (should only be the two error explanations):")
    for l in leftovers:
        print("  ", l)
    return 0

sys.exit(main())
