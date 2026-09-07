/*
 * Using the Button and Buzzer
 *
 * Board:  tinyCore (ESP32-S3)
 * Docs:   https://tinydocs.cc/3_tiny-hats/tinysniff/example-code/
 * Studio: https://app.tinystudio.cc/Mister-Industries/tinySniff/Software/Arduino/Examples/tinySniff_ButtonBuzzer
 *
 * Part of the MR.INDUSTRIES tinyStudio examples collection.
 * Generated from tinyDocs — edit the docs page, not this file.
 */

/*
 * Project: tinySniff - Using the Button and Buzzer
 * Author: Geoff McIntyre (w/ help from Claude)
 * Revision Date: 3/17/26
 * License: GNU General Public License v3.0
 *
 * Description:
 *   The Basic Demo plus the two parts of the HAT it ignores: the button
 *   and the buzzer.
 *
 *   The button (RX) starts and stops the graph, with a short confirmation
 *   beep either way. The buzzer (pin 13) also chirps whenever any channel
 *   climbs past ALERT_THRESHOLD, which makes the board useful without a
 *   screen attached.
 *
 *   Still Serial Plotter compatible. The menu text is ignored by the
 *   plotter, so you can graph and type commands at the same time.
 *
 *   Sensors:
 *     H2S  (Hydrogen Sulfide)          - A0 - GM-602B
 *     CO   (Carbon Monoxide)           - A1 - GM-702B
 *     CH4  (Methane / Combustible Gas) - A2 - GM-402B
 *
 * Requirements:
 *   - Libraries: none (raw ADC only)
 *   - Hardware: tinyCore ESP32-S3 + tinySniff HAT
 *
 * Controls:
 *   [r]  Print a single reading
 *   [u]  Toggle units: raw ADC or millivolts
 *   [a]  Toggle the audible alert
 *   [b]  Test the buzzer
 *   [?]  Show menu
 *   [Button]  Start / stop the graph
 */

#include <Arduino.h>

// --- PINS ---
#define PIN_H2S     A0   // GM-602B - Hydrogen Sulfide
#define PIN_CO      A1   // GM-702B - Carbon Monoxide
#define PIN_CH4     A2   // GM-402B - Methane / Combustible Gas
#define PIN_BUZZER  13
#define PIN_BUTTON  RX

// --- ADC CONFIG ---
#define ADC_BITS  12
#define ADC_MAX   4095.0f
#define VCC       3.3f

// --- STREAMING ---
#define STREAM_INTERVAL_MS  500   // 2 Hz, comfortable for the plotter

// --- ALERT ---
// Raw ADC counts. This is a placeholder. Watch your own clean-air readings
// first, then set it above where the channels normally sit.
#define ALERT_THRESHOLD   1200
#define ALERT_COOLDOWN_MS 3000    // Minimum gap between chirps

// --- BUZZER TONES ---
#define TONE_ON     2200   // Rising confirmation
#define TONE_OFF    1100   // Falling confirmation
#define TONE_ALERT  2600
#define BEEP_MS     80

// --- GLOBALS ---
bool streamEnabled = true;
bool showMv        = false;   // false = raw ADC, true = millivolts
bool alertEnabled  = true;

unsigned long lastStreamTime = 0;
unsigned long lastAlertTime  = 0;

// Debounce
unsigned long lastDebounceTime = 0;
int lastButtonState = HIGH;

// ---------------------------------------------------------------
// Buzzer
// ---------------------------------------------------------------

// tone() is non-blocking on the ESP32, so the delay is what actually
// holds the note. noTone() afterwards releases the pin.
void beep(unsigned int freq, unsigned long ms) {
    tone(PIN_BUZZER, freq, ms);
    delay(ms);
    noTone(PIN_BUZZER);
}

// ---------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------

float toMv(int raw) { return (raw / ADC_MAX) * VCC * 1000.0f; }

void printMenu() {
    Serial.println("\n--- Button and Buzzer Menu ---");
    Serial.println("[r]  Single reading");
    Serial.println("[u]  Toggle units: raw ADC or millivolts");
    Serial.println("[a]  Toggle the audible alert");
    Serial.println("[b]  Test the buzzer");
    Serial.println("[?]  Show menu");
    Serial.println("[Button]  Start / stop the graph");
    Serial.println("Plotter labels: CH4, H2S, CO");
    Serial.print("Alert threshold: ");
    Serial.println(ALERT_THRESHOLD);
    Serial.println("------------------------------");
}

void printReading(int ch4, int h2s, int co) {
    if (showMv) {
        Serial.printf("CH4_mV:%.1f,H2S_mV:%.1f,CO_mV:%.1f\n",
            toMv(ch4), toMv(h2s), toMv(co));
    } else {
        Serial.printf("CH4:%d,H2S:%d,CO:%d\n", ch4, h2s, co);
    }
}

// Chirp if any channel is over the line, but no more than once
// per ALERT_COOLDOWN_MS so a sustained event doesn't scream forever.
void checkAlert(int ch4, int h2s, int co) {
    if (!alertEnabled) return;
    if (ch4 <= ALERT_THRESHOLD && h2s <= ALERT_THRESHOLD && co <= ALERT_THRESHOLD) return;
    if (millis() - lastAlertTime < ALERT_COOLDOWN_MS) return;

    lastAlertTime = millis();
    Serial.println("*** ALERT: a channel is over threshold ***");
    beep(TONE_ALERT, BEEP_MS);
}

// ---------------------------------------------------------------
// Setup
// ---------------------------------------------------------------

void setup() {
    Serial.begin(115200);
    delay(2000);

    analogReadResolution(ADC_BITS);
    pinMode(PIN_H2S,    INPUT);
    pinMode(PIN_CO,     INPUT);
    pinMode(PIN_CH4,    INPUT);
    pinMode(PIN_BUZZER, OUTPUT);
    pinMode(PIN_BUTTON, INPUT_PULLUP);

    printMenu();
    beep(TONE_ON, BEEP_MS);   // One chirp so you know it booted
}

// ---------------------------------------------------------------
// Loop
// ---------------------------------------------------------------

void loop() {

    // 1. Timed streaming, plus the alert check
    if (streamEnabled && (millis() - lastStreamTime >= STREAM_INTERVAL_MS)) {
        lastStreamTime = millis();
        int ch4 = analogRead(PIN_CH4);
        int h2s = analogRead(PIN_H2S);
        int co  = analogRead(PIN_CO);
        printReading(ch4, h2s, co);
        checkAlert(ch4, h2s, co);
    }

    // 2. Serial commands
    if (Serial.available()) {
        char cmd = Serial.read();
        switch (cmd) {
            case 'r':
                printReading(analogRead(PIN_CH4), analogRead(PIN_H2S), analogRead(PIN_CO));
                break;
            case 'u':
                showMv = !showMv;
                Serial.printf("Units: %s\n", showMv ? "millivolts" : "raw ADC");
                break;
            case 'a':
                alertEnabled = !alertEnabled;
                Serial.printf("Audible alert: %s\n", alertEnabled ? "ON" : "OFF");
                beep(alertEnabled ? TONE_ON : TONE_OFF, BEEP_MS);
                break;
            case 'b':
                Serial.println("Buzzer test");
                beep(TONE_ALERT, BEEP_MS);
                break;
            case '?':
                printMenu();
                break;
        }
    }

    // 3. Button, debounced. A mechanical switch bounces for a few
    //    milliseconds, so we only believe a reading once it holds still.
    int reading = digitalRead(PIN_BUTTON);
    if (reading != lastButtonState) lastDebounceTime = millis();
    if ((millis() - lastDebounceTime) > 50) {
        static int buttonState = HIGH;
        if (reading != buttonState) {
            buttonState = reading;
            if (buttonState == LOW) {          // Active low
                streamEnabled = !streamEnabled;
                Serial.println(streamEnabled ? "Streaming ON" : "Streaming OFF");
                beep(streamEnabled ? TONE_ON : TONE_OFF, BEEP_MS);
            }
        }
    }
    lastButtonState = reading;
}
