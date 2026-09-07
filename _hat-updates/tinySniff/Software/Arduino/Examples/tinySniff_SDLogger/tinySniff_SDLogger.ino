/*
 * SD Card Logger
 *
 * Board:  tinyCore (ESP32-S3)
 * Docs:   https://tinydocs.cc/3_tiny-hats/tinysniff/example-code/
 * Studio: https://app.tinystudio.cc/Mister-Industries/tinySniff/Software/Arduino/Examples/tinySniff_SDLogger
 *
 * Part of the MR.INDUSTRIES tinyStudio examples collection.
 * Generated from tinyDocs — edit the docs page, not this file.
 */

/*
 * Project: tinySniff - SD Card Logger
 * Author: Geoff McIntyre (w/ help from Claude)
 * Revision Date: 3/17/26
 * License: GNU General Public License v3.0
 *
 * Description:
 *   Logs all three tinySniff MEMS gas sensors to a timestamped CSV
 *   file on the SD card. A new file (LOG_0001.CSV, LOG_0002.CSV, …)
 *   is created on each boot so previous sessions are never overwritten.
 *   Import the CSV into Excel, Google Sheets, or plot with Python.
 *
 *   Each logged measurement is the average of SUPERSAMPLE_COUNT raw ADC
 *   readings taken in rapid succession. This dramatically reduces ADC
 *   noise by averaging out random error - effectively giving you more
 *   effective bits of resolution for free.
 *
 *   A separate EMA (Exponential Moving Average) filtered column is also
 *   logged alongside the supersampled average. The EMA smooths slower
 *   trends across samples over time and is useful for spotting gradual
 *   gas buildup while ignoring momentary spikes.
 *
 *   CSV columns:
 *     Millis_ms | CH4_avg | CH4_ema | H2S_avg | H2S_ema | CO_avg | CO_ema
 *
 *   Sensors:
 *     H2S  (Hydrogen Sulfide)          - A0 - GM-602B
 *     CO   (Carbon Monoxide)           - A1 - GM-702B
 *     CH4  (Methane / Combustible Gas) - A2 - GM-402B
 *
 * Requirements:
 *   - Libraries: SD, FS
 *   - Hardware: tinyCore ESP32-S3 + tinySniff HAT (SD card inserted)
 *
 * Controls:
 *   [s]  Force flush buffer to SD card now
 *   [p]  Print last 10 log entries to Serial
 *   [n]  Close current file and start a new one
 *   [?]  Show menu
 *   [Button]  Pause / Resume logging
 */

#include <Arduino.h>
#include <SD.h>
#include <FS.h>

// --- PINS ---
#define PIN_H2S     A0
#define PIN_CO      A1
#define PIN_CH4     A2
#define PIN_BUTTON  RX

// --- ADC CONFIG ---
#define ADC_BITS  12

// --- SUPERSAMPLING CONFIG ---
// Each logged value is the mean of this many rapid ADC reads.
// 100 samples takes ~1ms on ESP32-S3 - imperceptible in a 1s log interval.
#define SUPERSAMPLE_COUNT  100

// --- EMA FILTER CONFIG ---
// Alpha controls how quickly the EMA responds to new readings.
// Lower = smoother / slower response. Higher = faster / noisier.
//   0.05 = very smooth, good for detecting slow gas buildup
//   0.20 = moderate, tracks changes in a few seconds
//   0.50 = fast, follows readings closely
#define EMA_ALPHA  0.1f

// --- LOGGING CONFIG ---
#define LOG_INTERVAL_MS  1000   // One supersampled entry per second
#define FLUSH_EVERY_N    10     // Flush to SD every N entries
#define MAX_LOG_FILES    9999

// --- GLOBALS ---
File logFile;
String logFileName;
bool loggingPaused = false;
unsigned long entryCount   = 0;
unsigned long flushCounter = 0;
unsigned long lastLogTime  = 0;

// EMA state - initialized to -1 so we can seed on the first reading
float ema_ch4 = -1.0f;
float ema_h2s = -1.0f;
float ema_co  = -1.0f;

// Debounce
unsigned long lastDebounceTime = 0;
int lastButtonState = HIGH;

// ---------------------------------------------------------------
// Supersampling - averages SUPERSAMPLE_COUNT rapid ADC reads
// ---------------------------------------------------------------

float supersample(int pin) {
    long sum = 0;
    for (int i = 0; i < SUPERSAMPLE_COUNT; i++) {
        sum += analogRead(pin);
    }
    return (float)sum / SUPERSAMPLE_COUNT;
}

// ---------------------------------------------------------------
// EMA filter - seeds on first call, then applies weighted average
// ---------------------------------------------------------------

float updateEma(float &ema, float newValue) {
    if (ema < 0.0f) {
        ema = newValue; // Seed with first real reading
    } else {
        ema = EMA_ALPHA * newValue + (1.0f - EMA_ALPHA) * ema;
    }
    return ema;
}

// ---------------------------------------------------------------
// File Management
// ---------------------------------------------------------------

String nextLogFileName() {
    for (int i = 1; i <= MAX_LOG_FILES; i++) {
        char name[20];
        snprintf(name, sizeof(name), "/LOG_%04d.CSV", i);
        if (!SD.exists(name)) return String(name);
    }
    return "/LOG_OVERFLOW.CSV";
}

bool openLogFile(const String& fileName) {
    logFile = SD.open(fileName, FILE_WRITE);
    if (!logFile) {
        Serial.printf("[ERROR] Could not open %s\n", fileName.c_str());
        return false;
    }
    // CSV header
    logFile.println("Millis_ms,CH4_avg,CH4_ema,H2S_avg,H2S_ema,CO_avg,CO_ema");
    logFile.flush();
    Serial.printf("Logging to: %s\n", fileName.c_str());
    return true;
}

// ---------------------------------------------------------------
// Menu
// ---------------------------------------------------------------

void printMenu() {
    Serial.println("\n--- SD Card Logger Menu ---");
    Serial.printf("  File:       %s\n", logFileName.c_str());
    Serial.printf("  Entries:    %lu\n", entryCount);
    Serial.printf("  Status:     %s\n", loggingPaused ? "PAUSED" : "LOGGING");
    Serial.printf("  Supersamp:  %d reads/entry\n", SUPERSAMPLE_COUNT);
    Serial.printf("  EMA alpha:  %.2f\n", EMA_ALPHA);
    Serial.println("[s]  Flush buffer to card now");
    Serial.println("[p]  Print last 10 entries");
    Serial.println("[n]  Start a new log file");
    Serial.println("[?]  Show menu");
    Serial.println("[Button]  Pause / Resume logging");
    Serial.println("--------------------------------");
}

// ---------------------------------------------------------------
// Print last N entries from the active log file
// ---------------------------------------------------------------

void printLastEntries(int n) {
    if (logFile) logFile.flush();
    File f = SD.open(logFileName, FILE_READ);
    if (!f) { Serial.println("[ERROR] Could not read file."); return; }

    std::vector<String> lines;
    while (f.available()) lines.push_back(f.readStringUntil('\n'));
    f.close();

    Serial.printf("\n--- Last %d entries from %s ---\n", n, logFileName.c_str());
    int start = max(0, (int)lines.size() - n);
    for (int i = start; i < (int)lines.size(); i++) Serial.println(lines[i]);
    Serial.println("---");
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

    if (!SD.begin()) {
        Serial.println("[ERROR] SD mount failed. Insert a card and reset.");
        while (1) delay(500);
    }
    Serial.println("SD mounted.");

    logFileName = nextLogFileName();
    if (!openLogFile(logFileName)) while (1) delay(500);

    Serial.println("SD Card Logger ready.");
    printMenu();
}

// ---------------------------------------------------------------
// Loop
// ---------------------------------------------------------------

void loop() {

    // 1. Log a supersampled entry at the configured interval
    if (!loggingPaused && (millis() - lastLogTime >= LOG_INTERVAL_MS)) {

        // Take SUPERSAMPLE_COUNT reads per channel and average them
        float ch4_avg = supersample(PIN_CH4);
        float h2s_avg = supersample(PIN_H2S);
        float co_avg  = supersample(PIN_CO);

        // Update EMA with the freshly supersampled averages
        float ch4_ema = updateEma(ema_ch4, ch4_avg);
        float h2s_ema = updateEma(ema_h2s, h2s_avg);
        float co_ema  = updateEma(ema_co,  co_avg);

        // Write CSV row
        logFile.printf("%lu,%.2f,%.2f,%.2f,%.2f,%.2f,%.2f\n",
            millis(),
            ch4_avg, ch4_ema,
            h2s_avg, h2s_ema,
            co_avg,  co_ema);

        entryCount++;
        flushCounter++;
        lastLogTime = millis();

        Serial.printf("[%lu] CH4  avg:%.1f ema:%.1f | H2S  avg:%.1f ema:%.1f | CO  avg:%.1f ema:%.1f\n",
            millis(),
            ch4_avg, ch4_ema,
            h2s_avg, h2s_ema,
            co_avg,  co_ema);

        if (flushCounter >= FLUSH_EVERY_N) {
            logFile.flush();
            flushCounter = 0;
            Serial.println("  [flushed]");
        }
    }

    // 2. Serial commands
    if (Serial.available()) {
        char cmd = Serial.read();
        switch (cmd) {
            case 's':
                logFile.flush();
                Serial.println("Flushed.");
                break;
            case 'p':
                printLastEntries(10);
                break;
            case 'n':
                logFile.close();
                entryCount   = 0;
                flushCounter = 0;
                ema_ch4 = ema_h2s = ema_co = -1.0f; // Reset EMA state for new file
                logFileName  = nextLogFileName();
                openLogFile(logFileName);
                break;
            case '?':
                printMenu();
                break;
        }
    }

    // 3. Button - pause/resume (debounced)
    int reading = digitalRead(PIN_BUTTON);
    if (reading != lastButtonState) lastDebounceTime = millis();
    if ((millis() - lastDebounceTime) > 50) {
        static int buttonState = HIGH;
        if (reading != buttonState) {
            buttonState = reading;
            if (buttonState == LOW) {
                loggingPaused = !loggingPaused;
                if (!loggingPaused) logFile.flush();
                Serial.println(loggingPaused ? "Logging PAUSED" : "Logging RESUMED");
            }
        }
    }
    lastButtonState = reading;
}
