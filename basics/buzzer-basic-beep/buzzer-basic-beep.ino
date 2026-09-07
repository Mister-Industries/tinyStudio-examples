/*
 * Basic beeping code
 *
 * Board:  tinyCore (ESP32-S3)
 * Docs:   https://tinydocs.cc/2_tiny-core/basics/buzz-buzzer/
 * Studio: https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/buzzer-basic-beep
 *
 * Part of the MR.INDUSTRIES tinyStudio examples collection.
 * Generated from tinyDocs — edit the docs page, not this file.
 */

// Simple Buzzer Beep for tinyCore ESP32-S3

const int buzzerPin = 2;        // GPIO pin connected to buzzer
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
}
