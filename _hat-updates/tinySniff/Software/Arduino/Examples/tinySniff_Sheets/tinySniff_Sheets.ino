/*
 * Google Sheets
 *
 * Board:  tinyCore (ESP32-S3)
 * Docs:   https://tinydocs.cc/3_tiny-hats/tinysniff/example-code/
 * Studio: https://app.tinystudio.cc/Mister-Industries/tinySniff/Software/Arduino/Examples/tinySniff_Sheets
 *
 * Part of the MR.INDUSTRIES tinyStudio examples collection.
 * Generated from tinyDocs — edit the docs page, not this file.
 */

/*
 * Project: tinySniff - Google Sheets
 * Author: Geoff McIntyre (w/ help from Claude)
 * Revision Date: 3/17/26
 * License: GNU General Public License v3.0
 *
 * Description:
 *   Logs all three tinySniff gas sensors to a Google Sheet in real time
 *   over WiFi. Uses a Google Apps Script Web App as the receiving endpoint -
 *   no third-party services or API keys required.
 *
 *   The Google Apps Script URL is entered once via the Serial Monitor
 *   and saved to flash (NVS). It survives power cycles - you only need
 *   to enter it again if you deploy a new script or run [u] to update it.
 *
 *   Each posted value is the average of SUPERSAMPLE_COUNT rapid ADC reads
 *   (noise reduction), plus a separate EMA-filtered value per channel.
 *
 *   Setup (one-time, ~5 minutes):
 *   1. Open Google Sheets and create a new spreadsheet.
 *   2. Click Extensions > Apps Script.
 *   3. Paste the Apps Script code from the comment block below into the editor.
 *   4. Click Deploy > New Deployment > Web App.
 *      - Execute as: Me
 *      - Who has access: Anyone
 *   5. Copy the Web App URL (starts with https://script.google.com/...)
 *   6. Fill in WIFI_SSID and WIFI_PASS below, flash, and open Serial Monitor.
 *   7. When prompted, paste the URL into the Serial Monitor and press Enter.
 *      The URL is saved to flash and you won't be asked again.
 *
 *   ---- Apps Script Code (paste into Google Apps Script editor) ----
 *
 *   function doGet(e) {
 *     var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
 *     if (sheet.getLastRow() === 0) {
 *       sheet.appendRow([
 *         "Timestamp", "Millis_ms",
 *         "CH4_avg", "CH4_ema",
 *         "H2S_avg", "H2S_ema",
 *         "CO_avg",  "CO_ema"
 *       ]);
 *     }
 *     var ts = new Date().toLocaleString();
 *     sheet.appendRow([
 *       ts,
 *       e.parameter.ms   || "",
 *       e.parameter.ch4  || "", e.parameter.ch4e || "",
 *       e.parameter.h2s  || "", e.parameter.h2se || "",
 *       e.parameter.co   || "", e.parameter.coe  || ""
 *     ]);
 *     return ContentService.createTextOutput("OK");
 *   }
 *
 *   -----------------------------------------------------------------
 *
 *   Sensors:
 *     H2S  (Hydrogen Sulfide)          - A0 - GM-602B
 *     CO   (Carbon Monoxide)           - A1 - GM-702B
 *     CH4  (Methane / Combustible Gas) - A2 - GM-402B
 *
 * Requirements:
 *   - Libraries: WiFi, HTTPClient, Preferences
 *   - Hardware: tinyCore ESP32-S3 + tinySniff HAT + WiFi network
 *
 * Controls:
 *   [r]  Post a reading now
 *   [u]  Update the Apps Script URL
 *   [w]  Print WiFi status
 *   [?]  Show menu
 *   [Button]  Pause / Resume logging
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <Preferences.h>

// --- WIFI CREDENTIALS ---
#define WIFI_SSID  "your_ssid_here"
#define WIFI_PASS  "your_password_here"

// --- PINS ---
#define PIN_H2S     A0
#define PIN_CO      A1
#define PIN_CH4     A2
#define PIN_BUTTON  RX

// --- ADC CONFIG ---
#define ADC_BITS  12

// --- SUPERSAMPLING CONFIG ---
#define SUPERSAMPLE_COUNT  100

// --- EMA FILTER CONFIG ---
#define EMA_ALPHA  0.1f

// --- LOGGING CONFIG ---
#define LOG_INTERVAL_MS   10000  // Post to Sheets every 10 seconds
#define WIFI_RETRY_DELAY   5000

// --- GLOBALS ---
Preferences prefs;
char scriptUrl[512] = "";   // Loaded from NVS on boot

bool loggingPaused = false;
unsigned long lastLogTime     = 0;
unsigned long lastWifiAttempt = 0;

// EMA state - seeded on first reading
float ema_ch4 = -1.0f;
float ema_h2s = -1.0f;
float ema_co  = -1.0f;

// Debounce
unsigned long lastDebounceTime = 0;
int lastButtonState = HIGH;

// ---------------------------------------------------------------
// Supersampling + EMA
// ---------------------------------------------------------------

float supersample(int pin) {
    long sum = 0;
    for (int i = 0; i < SUPERSAMPLE_COUNT; i++) sum += analogRead(pin);
    return (float)sum / SUPERSAMPLE_COUNT;
}

float updateEma(float &ema, float newValue) {
    ema = (ema < 0.0f) ? newValue : EMA_ALPHA * newValue + (1.0f - EMA_ALPHA) * ema;
    return ema;
}

// ---------------------------------------------------------------
// NVS - URL persistence
// ---------------------------------------------------------------

void loadUrl() {
    prefs.begin("tinySniff", true); // Read-only
    String stored = prefs.getString("scriptUrl", "");
    prefs.end();
    stored.toCharArray(scriptUrl, sizeof(scriptUrl));
}

void saveUrl(const char* url) {
    prefs.begin("tinySniff", false); // Read-write
    prefs.putString("scriptUrl", url);
    prefs.end();
}

// ---------------------------------------------------------------
// Serial URL prompt - blocks until user pastes a URL and hits Enter
// ---------------------------------------------------------------

void promptForUrl() {
    Serial.println("\nEnter your Google Apps Script Web App URL and press Enter:");
    Serial.println("(starts with https://script.google.com/macros/s/...)");
    Serial.print("> ");

    String input = "";
    while (true) {
        if (Serial.available()) {
            char c = Serial.read();
            if (c == '\n' || c == '\r') {
                input.trim();
                if (input.length() > 10) break; // Sanity check - must be a real URL
            } else {
                input += c;
                Serial.print(c); // Echo character back so the user can see what they typed
            }
        }
    }

    Serial.println(); // Newline after user input
    input.toCharArray(scriptUrl, sizeof(scriptUrl));
    saveUrl(scriptUrl);
    Serial.printf("URL saved: %s\n", scriptUrl);
}

// ---------------------------------------------------------------
// WiFi
// ---------------------------------------------------------------

void connectWiFi() {
    if (WiFi.status() == WL_CONNECTED) return;
    Serial.printf("Connecting to %s", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\nConnected! IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\n[WARN] WiFi connection failed. Will retry.");
    }
}

// ---------------------------------------------------------------
// Post to Google Sheets
// ---------------------------------------------------------------

void postToSheets(float ch4_avg, float ch4_ema, float h2s_avg, float h2s_ema, float co_avg, float co_ema) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WARN] Not connected - skipping post.");
        return;
    }
    if (strlen(scriptUrl) == 0) {
        Serial.println("[WARN] No URL configured - run [u] to set it.");
        return;
    }

    // Build URL with all eight data parameters
    String url = String(scriptUrl)
        + "?ms="   + String(millis())
        + "&ch4="  + String(ch4_avg,  2)
        + "&ch4e=" + String(ch4_ema,  2)
        + "&h2s="  + String(h2s_avg,  2)
        + "&h2se=" + String(h2s_ema,  2)
        + "&co="   + String(co_avg,   2)
        + "&coe="  + String(co_ema,   2);

    HTTPClient http;
    http.begin(url);
    http.setFollowRedirects(HTTPC_STRICT_FOLLOW_REDIRECTS); // Apps Script always redirects once

    int code = http.GET();
    if (code == 200) {
        Serial.printf("[Sheets] OK - CH4:%.1f(%.1f) H2S:%.1f(%.1f) CO:%.1f(%.1f)\n",
            ch4_avg, ch4_ema, h2s_avg, h2s_ema, co_avg, co_ema);
    } else {
        Serial.printf("[Sheets] HTTP %d - check your script URL.\n", code);
    }
    http.end();
}

// ---------------------------------------------------------------
// Menu
// ---------------------------------------------------------------

void printMenu() {
    Serial.println("\n--- Google Sheets Logger Menu ---");
    Serial.printf("  WiFi:      %s\n",
        WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString().c_str() : "Not connected");
    Serial.printf("  Status:    %s\n", loggingPaused ? "PAUSED" : "LOGGING");
    Serial.printf("  Interval:  %ds\n", LOG_INTERVAL_MS / 1000);
    Serial.printf("  Supersamp: %d reads/entry\n", SUPERSAMPLE_COUNT);
    Serial.printf("  EMA alpha: %.2f\n", EMA_ALPHA);
    Serial.printf("  URL:       %s\n", strlen(scriptUrl) > 0 ? scriptUrl : "(not set - run [u])");
    Serial.println("[r]  Post a reading now");
    Serial.println("[u]  Update Apps Script URL");
    Serial.println("[w]  Print WiFi status");
    Serial.println("[?]  Show menu");
    Serial.println("[Button]  Pause / Resume logging");
    Serial.println("------------------------------------");
}

// ---------------------------------------------------------------
// Setup
// ---------------------------------------------------------------

void setup() {
    Serial.begin(115200);
    delay(2000);

    analogReadResolution(ADC_BITS);
    pinMode(PIN_CH4,    INPUT);
    pinMode(PIN_H2S,    INPUT);
    pinMode(PIN_CO,     INPUT);
    pinMode(PIN_BUTTON, INPUT_PULLUP);

    // Load saved URL from NVS
    loadUrl();

    // If no URL has ever been set, prompt the user now
    if (strlen(scriptUrl) == 0) {
        Serial.println("No Apps Script URL found in flash.");
        promptForUrl();
    } else {
        Serial.printf("Loaded URL from flash: %s\n", scriptUrl);
    }

    connectWiFi();

    Serial.println("Google Sheets Logger ready.");
    printMenu();
}

// ---------------------------------------------------------------
// Loop
// ---------------------------------------------------------------

void loop() {

    // 1. Reconnect WiFi if dropped
    if (WiFi.status() != WL_CONNECTED && (millis() - lastWifiAttempt >= WIFI_RETRY_DELAY)) {
        connectWiFi();
        lastWifiAttempt = millis();
    }

    // 2. Supersample + EMA + post on interval
    if (!loggingPaused && (millis() - lastLogTime >= LOG_INTERVAL_MS)) {
        float ch4_avg = supersample(PIN_CH4);
        float h2s_avg = supersample(PIN_H2S);
        float co_avg  = supersample(PIN_CO);

        float ch4_ema = updateEma(ema_ch4, ch4_avg);
        float h2s_ema = updateEma(ema_h2s, h2s_avg);
        float co_ema  = updateEma(ema_co,  co_avg);

        postToSheets(ch4_avg, ch4_ema, h2s_avg, h2s_ema, co_avg, co_ema);
        lastLogTime = millis();
    }

    // 3. Serial commands
    if (Serial.available()) {
        char cmd = Serial.read();
        switch (cmd) {
            case 'r': {
                float ch4_avg = supersample(PIN_CH4);
                float h2s_avg = supersample(PIN_H2S);
                float co_avg  = supersample(PIN_CO);
                float ch4_ema = updateEma(ema_ch4, ch4_avg);
                float h2s_ema = updateEma(ema_h2s, h2s_avg);
                float co_ema  = updateEma(ema_co,  co_avg);
                postToSheets(ch4_avg, ch4_ema, h2s_avg, h2s_ema, co_avg, co_ema);
                break;
            }
            case 'u':
                promptForUrl();
                break;
            case 'w':
                Serial.printf("WiFi: %s  RSSI: %d dBm\n",
                    WiFi.status() == WL_CONNECTED
                        ? WiFi.localIP().toString().c_str()
                        : "disconnected",
                    WiFi.RSSI());
                break;
            case '?':
                printMenu();
                break;
        }
    }

    // 4. Button - pause/resume (debounced)
    int reading = digitalRead(PIN_BUTTON);
    if (reading != lastButtonState) lastDebounceTime = millis();
    if ((millis() - lastDebounceTime) > 50) {
        static int buttonState = HIGH;
        if (reading != buttonState) {
            buttonState = reading;
            if (buttonState == LOW) {
                loggingPaused = !loggingPaused;
                Serial.println(loggingPaused ? "Logging PAUSED" : "Logging RESUMED");
            }
        }
    }
    lastButtonState = reading;
}
