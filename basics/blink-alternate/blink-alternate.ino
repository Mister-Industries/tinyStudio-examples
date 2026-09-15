/*
 * Morse Code Blink — "I LOVE YOU"
 *
 * Board:  tinyCore (ESP32-S3)
 * Docs:   https://tinydocs.cc/2_tiny-core/basics/blink-led/
 * Studio: https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/blink-alternate
 *
 * Part of the MR.INDUSTRIES tinyStudio examples collection.
 * Generated from tinyDocs — edit the docs page, not this file.
 */

// Blinks "I LOVE YOU" in Morse code on the built-in LEDs.

const int ledBoot = 21;   // LED_BOOT pin
const int ledSig  = 33;   // LED_SIG pin

const int unit = 200;     // base Morse time unit in milliseconds

// One Morse token per letter, separated by spaces; "/" marks a word gap.
// I=..  L=.-..  O=---  V=...-  E=.   Y=-.--  O=---  U=..-
const char* message = ".. / .-.. --- ...- . / -.-- --- ..-";

void ledsOn() {
  digitalWrite(ledBoot, HIGH);
  digitalWrite(ledSig, HIGH);
}

void ledsOff() {
  digitalWrite(ledBoot, LOW);
  digitalWrite(ledSig, LOW);
}

// A dot: on for 1 unit, then a 1-unit gap between symbols.
void dot() {
  ledsOn();
  delay(unit);
  ledsOff();
  delay(unit);
}

// A dash: on for 3 units, then a 1-unit gap between symbols.
void dash() {
  ledsOn();
  delay(unit * 3);
  ledsOff();
  delay(unit);
}

void setup() {
  pinMode(ledBoot, OUTPUT);
  pinMode(ledSig, OUTPUT);
  ledsOff();
}

void loop() {
  for (int i = 0; message[i] != '\0'; i++) {
    char c = message[i];
    if (c == '.') {
      dot();
    } else if (c == '-') {
      dash();
    } else if (c == ' ') {
      delay(unit * 2);   // gap between letters (2 + the 1 already added = 3 units)
    } else if (c == '/') {
      delay(unit * 6);   // gap between words (6 + the 1 already added = 7 units)
    }
  }

  delay(unit * 7);       // pause before repeating the message
}
