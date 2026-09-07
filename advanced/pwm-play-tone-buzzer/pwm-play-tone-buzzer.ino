/*
 * Play a Tone on a Buzzer
 *
 * Board:  tinyCore (ESP32-S3)
 * Docs:   https://tinydocs.cc/5_reference/advanced/pwm/
 * Studio: https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/advanced/pwm-play-tone-buzzer
 *
 * Part of the MR.INDUSTRIES tinyStudio examples collection.
 * Generated from tinyDocs — edit the docs page, not this file.
 */

const int buzzerPin = 2;

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
}
