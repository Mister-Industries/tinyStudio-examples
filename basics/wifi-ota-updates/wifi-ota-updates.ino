/*
 * OTA (Over-the-Air) Updates
 *
 * Board:  tinyCore (ESP32-S3)
 * Docs:   https://tinydocs.cc/2_tiny-core/basics/wifi/
 * Studio: https://app.tinystudio.cc/Mister-Industries/tinyStudio-examples/basics/wifi-ota-updates
 *
 * Part of the MR.INDUSTRIES tinyStudio examples collection.
 * Generated from tinyDocs — edit the docs page, not this file.
 */

#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <ElegantOTA.h>

AsyncWebServer server(80);

void setup() {
    // WiFi setup...

    // Enable OTA updates — browse to http://<board-ip>/update
    ElegantOTA.begin(&server);

    server.begin();
}

void loop() {
    ElegantOTA.loop();
}
