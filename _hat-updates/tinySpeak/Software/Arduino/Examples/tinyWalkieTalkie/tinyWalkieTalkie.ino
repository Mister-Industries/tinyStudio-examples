/*
 * tinyWalkieTalkie
 *
 * Board:  tinyCore (ESP32-S3)
 * Docs:   https://tinydocs.cc/3_tiny-hats/tinyspeak/example-code/
 * Studio: https://app.tinystudio.cc/Mister-Industries/tinySpeak/Software/Arduino/Examples/tinyWalkieTalkie
 *
 * Part of the MR.INDUSTRIES tinyStudio examples collection.
 * Generated from tinyDocs — edit the docs page, not this file.
 */

/*
 * Project: tinySpeak - tinyWalkieTalkie
 * Author: Geoff McIntyre (w/ help from Claude)
 * Revision Date: 2/18/26
 * License: GNU General Public License v3.0
 *
 * Description:
 * Push-to-Talk Intercom using ESP-NOW.
 * - Low-latency audio streaming between units (No Router/Internet needed).
 * - Broadcasts to all nearby tinySpeak devices on the same channel.
 *
 * Requirements:
 * - Libraries: WiFi, esp_now (Built-in)
 * - Hardware: 2+ x tinyCore ESP32-S3 + tinySpeak HAT
 * - Note: No SD card or internet required.
 *
 * Controls:
 * [Hold RX Button 150ms] Start Talking (Transmit)
 * [Release RX Button]    Stop Talking after 200ms (Receive)
 * [t]  Toggle Talk via Serial
 * [c]  Cycle WiFi Channel (1-11)
 * [?]  Show Menu
 */

#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include "driver/i2s_std.h"

// --- PINS ---
#define I2S_SPKR_DOUT  8
#define I2S_SPKR_BCLK  9
#define I2S_SPKR_LRC   10
#define I2S_MIC_WS     11
#define I2S_MIC_SD     12
#define I2S_MIC_SCK    13
#define PIN_BUTTON     RX

// --- AUDIO CONFIG ---
// 8kHz keeps ESP-NOW packets under the 250-byte limit.
// 120 samples x 2 bytes = 240 bytes per packet.
#define SAMPLE_RATE     8000
#define PACKET_SAMPLES  120
#define PACKET_SIZE     (PACKET_SAMPLES * 2)
#define MIC_SHIFT       16
#define MIC_GAIN        4.0f
#define RECEIVER_TIMEOUT_MS  80
#define BUTTON_HOLD_MS    150
#define BUTTON_RELEASE_MS 200

// --- GLOBALS ---
int  wifiChannel  = 1;
bool isTalking    = false;

i2s_chan_handle_t tx_handle = NULL;
i2s_chan_handle_t rx_handle = NULL;

int32_t raw_samples[PACKET_SAMPLES];
int16_t tx_buffer[PACKET_SAMPLES];

uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

volatile unsigned long lastPacketTime    = 0;
volatile bool          isReceivingAudio  = false;

unsigned long buttonPressedAt  = 0;
unsigned long buttonReleasedAt = 0;
bool buttonArmed = false;

// ---------------------------------------------------------------
// I2S Setup
// ---------------------------------------------------------------

void setupI2S() {
    // Speaker (I2S_NUM_0, TX)
    i2s_chan_config_t spk_chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_0, I2S_ROLE_MASTER);
    i2s_new_channel(&spk_chan_cfg, &tx_handle, NULL);

    i2s_std_config_t spk_cfg = {
        .clk_cfg  = I2S_STD_CLK_DEFAULT_CONFIG(SAMPLE_RATE),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED,
            .bclk = (gpio_num_t)I2S_SPKR_BCLK,
            .ws   = (gpio_num_t)I2S_SPKR_LRC,
            .dout = (gpio_num_t)I2S_SPKR_DOUT,
            .din  = I2S_GPIO_UNUSED,
            .invert_flags = { .mclk_inv = false, .bclk_inv = false, .ws_inv = false },
        },
    };
    i2s_channel_init_std_mode(tx_handle, &spk_cfg);
    i2s_channel_enable(tx_handle);

    // Microphone (I2S_NUM_1, RX)
    i2s_chan_config_t mic_chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_1, I2S_ROLE_MASTER);
    i2s_new_channel(&mic_chan_cfg, NULL, &rx_handle);

    i2s_std_config_t mic_cfg = {
        .clk_cfg  = I2S_STD_CLK_DEFAULT_CONFIG(SAMPLE_RATE),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_32BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED,
            .bclk = (gpio_num_t)I2S_MIC_SCK,
            .ws   = (gpio_num_t)I2S_MIC_WS,
            .dout = I2S_GPIO_UNUSED,
            .din  = (gpio_num_t)I2S_MIC_SD,
            .invert_flags = { .mclk_inv = false, .bclk_inv = false, .ws_inv = false },
        },
    };
    i2s_channel_init_std_mode(rx_handle, &mic_cfg);
    i2s_channel_enable(rx_handle);
}

// Hard-reset clears the DMA ring buffer — writing silence alone isn't enough.
void resetSpeaker() {
    i2s_channel_disable(tx_handle);
    i2s_channel_enable(tx_handle);
}

// ---------------------------------------------------------------
// ESP-NOW
// ---------------------------------------------------------------

void OnDataRecv(const esp_now_recv_info_t *recv_info, const uint8_t *incomingData, int len) {
    if (isTalking) return;
    isReceivingAudio = true;
    lastPacketTime   = millis();
    size_t bytes_written;
    i2s_channel_write(tx_handle, incomingData, len, &bytes_written, pdMS_TO_TICKS(20));
}

void setupESPNOW() {
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();

    if (esp_now_init() != ESP_OK) {
        Serial.println("[ERROR] ESP-NOW init failed.");
        return;
    }

    esp_now_register_recv_cb(OnDataRecv);

    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, broadcastAddress, 6);
    peerInfo.channel = wifiChannel;
    peerInfo.encrypt = false;

    if (esp_now_add_peer(&peerInfo) != ESP_OK) {
        Serial.println("[ERROR] Failed to add broadcast peer.");
        return;
    }

    Serial.printf("ESP-NOW ready on channel %d\\n", wifiChannel);
}

void changeChannel(int newChan) {
    wifiChannel = constrain(newChan, 1, 11);
    esp_now_deinit();
    WiFi.mode(WIFI_STA);
    esp_wifi_set_promiscuous(true);
    esp_wifi_set_channel(wifiChannel, WIFI_SECOND_CHAN_NONE);
    esp_wifi_set_promiscuous(false);
    setupESPNOW();
    Serial.printf("Switched to channel %d\\n", wifiChannel);
}

// ---------------------------------------------------------------
// Talk State
// ---------------------------------------------------------------

void startTalking() { isTalking = true;  Serial.println("Transmitting..."); }
void stopTalking()  { isTalking = false; Serial.println("Listening..."); }

// ---------------------------------------------------------------
// Menu
// ---------------------------------------------------------------

void printMenu() {
    Serial.println("\\n--- tinyWalkieTalkie Menu ---");
    Serial.println("[Hold RX 150ms] Start Talking");
    Serial.println("[Release RX]    Stop Talking (after 200ms)");
    Serial.println("[t]  Toggle Talk via Serial");
    Serial.println("[c]  Cycle Channel (1-11)");
    Serial.println("[?]  Show Menu");
    Serial.printf( "Current Channel: %d\\n", wifiChannel);
    Serial.println("-----------------------------");
}

// ---------------------------------------------------------------
// Setup
// ---------------------------------------------------------------

void setup() {
    Serial.begin(115200);
    delay(2000);
    pinMode(PIN_BUTTON, INPUT_PULLUP);
    setupI2S();
    setupESPNOW();
    printMenu();
}

// ---------------------------------------------------------------
// Loop
// ---------------------------------------------------------------

void loop() {
    // 1. Serial Commands
    if (Serial.available()) {
        String input = Serial.readStringUntil('\\n');
        input.trim();
        if (input.length() == 0) return;

        if (input[0] == '?') { printMenu(); return; }
        if (input[0] == 't') {
            if (!isTalking) startTalking(); else stopTalking();
            return;
        }
        if (input[0] == 'c') {
            changeChannel((wifiChannel >= 11) ? 1 : wifiChannel + 1);
            return;
        }
    }

    // 2. Button — two-stage debounce.
    //    START: hold LOW for BUTTON_HOLD_MS before transmitting.
    //    STOP:  release HIGH for BUTTON_RELEASE_MS before stopping.
    int reading = digitalRead(PIN_BUTTON);

    if (reading == LOW) {
        buttonReleasedAt = 0;
        if (buttonPressedAt == 0) buttonPressedAt = millis();
        if (!isTalking && !buttonArmed && (millis() - buttonPressedAt >= BUTTON_HOLD_MS)) {
            buttonArmed = true;
            startTalking();
        }
    } else {
        buttonPressedAt = 0;
        buttonArmed = false;
        if (isTalking) {
            if (buttonReleasedAt == 0) buttonReleasedAt = millis();
            if (millis() - buttonReleasedAt >= BUTTON_RELEASE_MS) {
                buttonReleasedAt = 0;
                stopTalking();
            }
        } else {
            buttonReleasedAt = 0;
        }
    }

    // 3. Speaker DMA — hard reset on stream end; pump silence when idle.
    if (!isTalking) {
        if (isReceivingAudio && (millis() - lastPacketTime) > RECEIVER_TIMEOUT_MS) {
            isReceivingAudio = false;
            resetSpeaker();
        }
        if (!isReceivingAudio) {
            static uint8_t silence[PACKET_SIZE] = {0};
            size_t bytes_written;
            i2s_channel_write(tx_handle, silence, sizeof(silence), &bytes_written, 0);
        }
    }

    // 4. Transmission loop
    if (isTalking) {
        size_t bytes_read = 0;
        if (i2s_channel_read(rx_handle, raw_samples, sizeof(raw_samples), &bytes_read, 0) == ESP_OK && bytes_read > 0) {
            int stereo_frames = bytes_read / 8;
            for (int i = 0; i < stereo_frames; i++) {
                float sample = (raw_samples[2 * i] >> MIC_SHIFT) * MIC_GAIN;
                if      (sample >  32767.0f) sample =  32767.0f;
                else if (sample < -32768.0f) sample = -32768.0f;
                tx_buffer[i] = (int16_t)sample;
            }
            esp_now_send(broadcastAddress, (uint8_t*)tx_buffer, stereo_frames * 2);
        }
    }
}
