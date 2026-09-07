/*
 * Text Notifications
 *
 * Board:  tinyCore (ESP32-S3)
 * Docs:   https://tinydocs.cc/3_tiny-hats/tinysniff/example-code/
 * Studio: https://app.tinystudio.cc/Mister-Industries/tinySniff/Software/Arduino/Examples/tinySniff_Alarm
 *
 * Part of the MR.INDUSTRIES tinyStudio examples collection.
 * Generated from tinyDocs — edit the docs page, not this file.
 */

/*
 * Project: tinySniff - Text Notifications
 * Author: Geoff McIntyre (w/ help from Claude)
 * Revision Date: 3/17/26
 * License: GNU General Public License v3.0
 *
 * Description:
 *   Monitors all three tinySniff gas sensors against configurable thresholds
 *   and sends an email alert when any channel exceeds its limit.
 *   Each threshold check uses a supersampled reading (average of
 *   SUPERSAMPLE_COUNT samples) so a single noisy ADC spike won't false-trigger.
 *
 *   Email is sent via SMTP using the ESP-Mail-Client library by Mobizt.
 *   Gmail works out of the box - see setup instructions below.
 *
 *   Gmail Setup (one-time):
 *   1. Enable 2-Step Verification on your Google account if not already on.
 *   2. Go to myaccount.google.com > Security > App Passwords.
 *   3. Create an app password (name it anything, e.g. "tinySniff").
 *   4. Copy the 16-character password - this goes into SMTP_PASSWORD below.
 *      (Your real Google password is NOT used here.)
 *   5. Fill in SMTP_SENDER_EMAIL and ALERT_RECIPIENT_EMAIL below.
 *
 *   Other SMTP providers (Outlook, SendGrid, Mailjet) work too -
 *   just change SMTP_HOST and SMTP_PORT accordingly.
 *
 *   Sensors:
 *     H2S  (Hydrogen Sulfide)          - A0 - GM-602B
 *     CO   (Carbon Monoxide)           - A1 - GM-702B
 *     CH4  (Methane / Combustible Gas) - A2 - GM-402B
 *
 * Requirements:
 *   - Libraries: WiFi, ESP Mail Client (by Mobizt - install via Library Manager)
 *   - Hardware: tinyCore ESP32-S3 + tinySniff HAT + WiFi network
 *
 * Controls:
 *   [t]  Print current thresholds
 *   [s]  Print current sensor readings
 *   [a]  Toggle alarm armed / disarmed
 *   [e]  Send a test email
 *   [w]  Print WiFi status
 *   [?]  Show menu
 *   [Button]  Arm / Disarm alarm
 */

#include <Arduino.h>
#include <WiFi.h>
#include <ESP_Mail_Client.h>

// --- WIFI CREDENTIALS ---
#define WIFI_SSID  "your_ssid_here"
#define WIFI_PASS  "your_password_here"

// --- EMAIL CONFIG ---
// Gmail: use an App Password, NOT your real password (see setup above).
#define SMTP_HOST           "smtp.gmail.com"
#define SMTP_PORT           465                         // SSL - use 587 for TLS
#define SMTP_SENDER_EMAIL   "your.address@gmail.com"
#define SMTP_PASSWORD       "xxxx xxxx xxxx xxxx"       // 16-char Gmail App Password
#define ALERT_RECIPIENT_EMAIL  "recipient@example.com"  // Where alerts are sent

// --- PINS ---
#define PIN_H2S     A0
#define PIN_CO      A1
#define PIN_CH4     A2
#define PIN_BUTTON  RX

// --- ADC CONFIG ---
#define ADC_BITS  12

// --- SUPERSAMPLING CONFIG ---
// Threshold checks average this many reads - eliminates false triggers from
// single noisy ADC samples without adding meaningful latency (~1ms for 100).
#define SUPERSAMPLE_COUNT  100

// --- ALARM THRESHOLDS (raw ADC, 0-4095) ---
// Tune these after observing your clean-air baseline in the Serial Monitor.
// Supersampled readings are more stable than raw reads, so thresholds can
// be set tighter without nuisance trips.
#define THRESHOLD_CH4   1200   // GM-402B - Methane / Combustible Gas
#define THRESHOLD_H2S   1200   // GM-602B - Hydrogen Sulfide
#define THRESHOLD_CO    1200   // GM-702B - Carbon Monoxide

// --- ALARM CONFIG ---
#define SAMPLE_INTERVAL_MS   2000   // Check sensors every 2 seconds
#define ALERT_COOLDOWN_MS   60000   // Minimum ms between repeat alerts per channel (60s)
#define WIFI_RETRY_DELAY     5000

// --- GLOBALS ---
SMTPSession smtp;

bool alarmArmed = true;

unsigned long lastAlertTime_CH4 = 0;
unsigned long lastAlertTime_H2S = 0;
unsigned long lastAlertTime_CO  = 0;

unsigned long lastSampleTime  = 0;
unsigned long lastWifiAttempt = 0;

// Debounce
unsigned long lastDebounceTime = 0;
int lastButtonState = HIGH;

// ---------------------------------------------------------------
// Supersampling
// ---------------------------------------------------------------

float supersample(int pin) {
    long sum = 0;
    for (int i = 0; i < SUPERSAMPLE_COUNT; i++) sum += analogRead(pin);
    return (float)sum / SUPERSAMPLE_COUNT;
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
// Email
// ---------------------------------------------------------------

// SMTP status callback - routes library debug output to Serial
void smtpCallback(SMTP_Status status) {
    Serial.println(status.info());
}

void sendAlertEmail(const char* gasName, float reading, int threshold) {
    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("[WARN] Not connected - email not sent.");
        return;
    }

    Serial.printf("[Email] Sending alert for %s...\n", gasName);

    // Configure SMTP session
    Session_Config config;
    config.server.host_name = SMTP_HOST;
    config.server.port      = SMTP_PORT;
    config.login.email      = SMTP_SENDER_EMAIL;
    config.login.password   = SMTP_PASSWORD;
    config.login.user_domain = "";  // Leave empty for Gmail

    // Build message
    SMTP_Message message;
    message.sender.name  = "tinySniff";
    message.sender.email = SMTP_SENDER_EMAIL;
    message.subject      = "tinySniff Gas Alert";
    message.addRecipient("Alert Recipient", ALERT_RECIPIENT_EMAIL);

    char body[256];
    snprintf(body, sizeof(body),
        "tinySniff Gas Alert\n\n"
        "Sensor:    %s\n"
        "Reading:   %.1f (supersampled avg of %d reads)\n"
        "Threshold: %d\n\n"
        "Device is monitoring. Next alert for this channel\n"
        "will not be sent for %d seconds.",
        gasName, reading, SUPERSAMPLE_COUNT, threshold, ALERT_COOLDOWN_MS / 1000);

    message.text.content = body;
    message.text.charSet = "utf-8";

    smtp.debug(0); // Set to 1 for verbose SMTP debug output
    smtp.callback(smtpCallback);

    if (!smtp.connect(&config)) {
        Serial.printf("[Email] Connection failed: %s\n", smtp.errorReason().c_str());
        return;
    }
    if (!MailClient.sendMail(&smtp, &message)) {
        Serial.printf("[Email] Send failed: %s\n", smtp.errorReason().c_str());
    } else {
        Serial.printf("[Email] Alert sent: %s reading=%.1f\n", gasName, reading);
    }
    smtp.closeSession();
}

// ---------------------------------------------------------------
// Alarm Check
// ---------------------------------------------------------------

void checkAlarms() {
    float ch4 = supersample(PIN_CH4);
    float h2s = supersample(PIN_H2S);
    float co  = supersample(PIN_CO);
    unsigned long now = millis();

    Serial.printf("[Monitor] CH4:%.1f  H2S:%.1f  CO:%.1f  (armed: %s)\n",
        ch4, h2s, co, alarmArmed ? "YES" : "NO");

    if (!alarmArmed) return;

    if (ch4 > THRESHOLD_CH4 && (now - lastAlertTime_CH4 >= ALERT_COOLDOWN_MS)) {
        Serial.println("[ALARM] CH4 threshold exceeded!");
        sendAlertEmail("CH4 (Methane / Combustible Gas)", ch4, THRESHOLD_CH4);
        lastAlertTime_CH4 = now;
    }
    if (h2s > THRESHOLD_H2S && (now - lastAlertTime_H2S >= ALERT_COOLDOWN_MS)) {
        Serial.println("[ALARM] H2S threshold exceeded!");
        sendAlertEmail("H2S (Hydrogen Sulfide)", h2s, THRESHOLD_H2S);
        lastAlertTime_H2S = now;
    }
    if (co > THRESHOLD_CO && (now - lastAlertTime_CO >= ALERT_COOLDOWN_MS)) {
        Serial.println("[ALARM] CO threshold exceeded!");
        sendAlertEmail("CO (Carbon Monoxide)", co, THRESHOLD_CO);
        lastAlertTime_CO = now;
    }
}

// ---------------------------------------------------------------
// Menu
// ---------------------------------------------------------------

void printThresholds() {
    Serial.println("\n--- Active Thresholds ---");
    Serial.printf("  CH4 (Methane):           %d / 4095\n", THRESHOLD_CH4);
    Serial.printf("  H2S (Hydrogen Sulfide):  %d / 4095\n", THRESHOLD_H2S);
    Serial.printf("  CO  (Carbon Monoxide):   %d / 4095\n", THRESHOLD_CO);
    Serial.printf("  Supersample count:       %d reads/check\n", SUPERSAMPLE_COUNT);
    Serial.println("  Edit #define THRESHOLD_xxx to adjust.");
    Serial.println("-------------------------");
}

void printMenu() {
    Serial.println("\n--- Text Notifications Menu ---");
    Serial.printf("  WiFi:     %s\n",
        WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString().c_str() : "Not connected");
    Serial.printf("  Alarm:    %s\n", alarmArmed ? "ARMED" : "DISARMED");
    Serial.printf("  Alerting: %s\n", ALERT_RECIPIENT_EMAIL);
    Serial.println("[t]  Print thresholds");
    Serial.println("[s]  Print current sensor readings");
    Serial.println("[a]  Toggle alarm armed / disarmed");
    Serial.println("[e]  Send a test email");
    Serial.println("[w]  Print WiFi status");
    Serial.println("[?]  Show menu");
    Serial.println("[Button]  Arm / Disarm");
    Serial.println("----------------------------");
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

    connectWiFi();

    Serial.println("Text Notifications ready.");
    printMenu();
    printThresholds();
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

    // 2. Sample and check alarms
    if (millis() - lastSampleTime >= SAMPLE_INTERVAL_MS) {
        checkAlarms();
        lastSampleTime = millis();
    }

    // 3. Serial commands
    if (Serial.available()) {
        char cmd = Serial.read();
        switch (cmd) {
            case 't':
                printThresholds();
                break;
            case 's':
                Serial.printf("CH4:%.1f  H2S:%.1f  CO:%.1f\n",
                    supersample(PIN_CH4), supersample(PIN_H2S), supersample(PIN_CO));
                break;
            case 'a':
                alarmArmed = !alarmArmed;
                Serial.printf("Alarm %s\n", alarmArmed ? "ARMED" : "DISARMED");
                break;
            case 'e':
                Serial.println("Sending test email...");
                sendAlertEmail("TEST (ignore this)", 0.0f, 0);
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

    // 4. Button - arm/disarm (debounced)
    int reading = digitalRead(PIN_BUTTON);
    if (reading != lastButtonState) lastDebounceTime = millis();
    if ((millis() - lastDebounceTime) > 50) {
        static int buttonState = HIGH;
        if (reading != buttonState) {
            buttonState = reading;
            if (buttonState == LOW) {
                alarmArmed = !alarmArmed;
                Serial.printf("Alarm %s\n", alarmArmed ? "ARMED" : "DISARMED");
            }
        }
    }
    lastButtonState = reading;
}
