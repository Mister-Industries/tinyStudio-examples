/*
 * tinyMP3Player
 *
 * Board:  tinyCore (ESP32-S3)
 * Docs:   https://tinydocs.cc/3_tiny-hats/tinyspeak/example-code/
 * Studio: https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyMP3Player
 *
 * Part of the MR.INDUSTRIES tinyStudio examples collection.
 * Generated from tinyDocs — edit the docs page, not this file.
 */

/*
 * Project: tinySpeak - tinyMP3Player
 * Author: Geoff McIntyre (w/ help from Claude)
 * Revision Date: 2/18/26
 * License: GNU General Public License v3.0
 *
 * Description:
 *   Plays MP3 files from the SD card.
 *
 * Requirements:
 * - Libraries: SD, FS, ESP32-audioI2S by schreibfaul1
 * - Hardware: tinyCore ESP32-S3 + tinySpeak HAT
 *
 * Controls:
 * [p] Play/Pause
 * [n] Next Track
 * [b] Previous Track
 * [+] Volume Up
 * [-] Volume Down
 * [l] List Files
 * [?] Show Menu
 * [Button Single Press] Play/Pause
 * [Button Double Press] Next Track
 */

#include <Arduino.h>
#include <SD.h>
#include <FS.h>
#include "Audio.h"

// --- PINS ---
#define I2S_SPKR_DOUT 8
#define I2S_SPKR_BCLK 9
#define I2S_SPKR_LRC  10
#define PIN_BUTTON    RX

Audio audio;
std::vector<String> mp3Files;
int currentFileIndex = 0;
bool isPlaying = false;
bool isPaused = false;
int volume = 15;

// Debounce Globals
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;
int lastButtonState = HIGH;

// Double-press detection
unsigned long lastPressTime = 0;
const unsigned long doublePressWindow = 300;
bool pendingSinglePress = false;

void printMenu() {
    Serial.println("\\n--- tinyMP3Player Menu ---");
    Serial.println("[p] Play/Pause");
    Serial.println("[n] Next Track");
    Serial.println("[b] Previous Track");
    Serial.println("[+] Volume Up");
    Serial.println("[-] Volume Down");
    Serial.println("[l] List Files");
    Serial.println("[?] Show Menu");
    Serial.println("[Button x1] Play/Pause");
    Serial.println("[Button x2] Next Track");
    Serial.println("--------------------------");
}

void listMP3Files() {
    mp3Files.clear();
    File root = SD.open("/");
    if (!root) {
        Serial.println("Failed to open directory");
        return;
    }
    File file = root.openNextFile();
    while (file) {
        String fileName = file.name();
        if (fileName.endsWith(".mp3")) {
            mp3Files.push_back(fileName);
            Serial.print("Found: "); Serial.println(fileName);
        }
        file = root.openNextFile();
    }
    Serial.printf("Total MP3s: %d\\n", mp3Files.size());
}

void playCurrentTrack() {
    if (mp3Files.empty()) return;
    String path = "/" + mp3Files[currentFileIndex];
    Serial.print("Playing: "); Serial.println(path);
    audio.connecttoFS(SD, path.c_str());
    isPlaying = true;
    isPaused = false;
}

void togglePlayPause() {
    if (mp3Files.empty()) return;

    if (!isPlaying) {
        playCurrentTrack();
    } else if (isPaused) {
        audio.pauseResume();
        isPaused = false;
        Serial.println("Resumed");
    } else {
        audio.pauseResume();
        isPaused = true;
        Serial.println("Paused");
    }
}

void nextTrack() {
    currentFileIndex = (currentFileIndex + 1) % mp3Files.size();
    Serial.printf("Skipping to track %d\\n", currentFileIndex);
    playCurrentTrack();
}

void handleButtonPress() {
    unsigned long now = millis();

    if (pendingSinglePress && (now - lastPressTime) <= doublePressWindow) {
        pendingSinglePress = false;
        Serial.println("Double press — Next Track");
        nextTrack();
    } else {
        pendingSinglePress = true;
        lastPressTime = now;
    }
}

void setup() {
    Serial.begin(115200);
    delay(2000);

    pinMode(PIN_BUTTON, INPUT_PULLUP);

    if (!SD.begin()) {
        Serial.println("SD Mount Failed!");
    } else {
        Serial.println("SD Mounted.");
        listMP3Files();
    }

    audio.setPinout(I2S_SPKR_BCLK, I2S_SPKR_LRC, I2S_SPKR_DOUT);
    audio.setVolume(volume);

    printMenu();
}

void loop() {
    audio.loop();

    if (pendingSinglePress && (millis() - lastPressTime) > doublePressWindow) {
        pendingSinglePress = false;
        Serial.println("Single press — Play/Pause");
        togglePlayPause();
    }

    if (Serial.available()) {
        char cmd = Serial.read();
        switch (cmd) {
            case 'p': togglePlayPause(); break;
            case 'n': nextTrack(); break;
            case 'b':
                currentFileIndex = (currentFileIndex - 1 + mp3Files.size()) % mp3Files.size();
                playCurrentTrack();
                break;
            case '+':
                volume = constrain(volume + 1, 0, 21);
                audio.setVolume(volume);
                Serial.printf("Volume: %d\\n", volume);
                break;
            case '-':
                volume = constrain(volume - 1, 0, 21);
                audio.setVolume(volume);
                Serial.printf("Volume: %d\\n", volume);
                break;
            case 'l': listMP3Files(); break;
            case '?': printMenu(); break;
        }
    }

    int reading = digitalRead(PIN_BUTTON);
    if (reading != lastButtonState) {
        lastDebounceTime = millis();
    }
    if ((millis() - lastDebounceTime) > debounceDelay) {
        static int buttonState = HIGH;
        if (reading != buttonState) {
            buttonState = reading;
            if (buttonState == LOW) {
                handleButtonPress();
            }
        }
    }
    lastButtonState = reading;
}

void audio_eof_mp3(const char *info) {
    Serial.print("EOF: "); Serial.println(info);
    currentFileIndex = (currentFileIndex + 1) % mp3Files.size();
    playCurrentTrack();
}
