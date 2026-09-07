/*
 * Basic Demo
 *
 * Board:  tinyCore (ESP32-S3)
 * Docs:   https://tinydocs.cc/3_tiny-hats/tinysniff/example-code/
 * Studio: https://app.tinystudio.cc/Mister-Industries/tinySniff/Software/Arduino/Examples/tinySniff_Monitor
 *
 * Part of the MR.INDUSTRIES tinyStudio examples collection.
 * Generated from tinyDocs — edit the docs page, not this file.
 */

/*
 * Project: tinySniff - Basic Demo
 * Author: Geoff McIntyre (w/ help from Claude)
 * Revision Date: 3/17/26
 * License: GNU General Public License v3.0
 *
 * Description:
 *   Reads all three tinySniff MEMS gas sensors and streams them out as a
 *   graph. Nothing else. Open Tools > Serial Plotter in the Arduino IDE,
 *   or connect from the tinyDocs Web Serial Monitor, and watch three
 *   live traces.
 *
 *   Sensors:
 *     H2S  (Hydrogen Sulfide)          - A0 - GM-602B
 *     CO   (Carbon Monoxide)           - A1 - GM-702B
 *     CH4  (Methane / Combustible Gas) - A2 - GM-402B
 *
 * Requirements:
 *   - Libraries: none (raw ADC only)
 *   - Hardware: tinyCore ESP32-S3 + tinySniff HAT
 */

#include <Arduino.h>

// --- PINS ---
#define PIN_H2S     A0   // GM-602B - Hydrogen Sulfide
#define PIN_CO      A1   // GM-702B - Carbon Monoxide
#define PIN_CH4     A2   // GM-402B - Methane / Combustible Gas

// --- CONFIG ---
#define ADC_BITS            12    // 12-bit ADC, so readings run 0 to 4095
#define STREAM_INTERVAL_MS  500   // 2 Hz, comfortable for the plotter

unsigned long lastStreamTime = 0;

void setup() {
    Serial.begin(115200);
    delay(2000);   // Give Web Serial a moment to attach

    analogReadResolution(ADC_BITS);
    pinMode(PIN_H2S, INPUT);
    pinMode(PIN_CO,  INPUT);
    pinMode(PIN_CH4, INPUT);
}

void loop() {
    if (millis() - lastStreamTime < STREAM_INTERVAL_MS) return;
    lastStreamTime = millis();

    // "label:value" pairs are what name the three traces in the plotter.
    Serial.printf("CH4:%d,H2S:%d,CO:%d\\n",
        analogRead(PIN_CH4),
        analogRead(PIN_H2S),
        analogRead(PIN_CO));
}
