#include "network-controller.h"
#include "HardwareSerial.h"
#include "WebSockets.h"
#include "WiFiType.h"
#include <cstdint>

Network::Network(const char *ssid, const char *password, const char *host,
                 uint16_t port) {
  this->ssid = ssid;
  this->password = password;
  this->host = host;
  this->port = port;
}

void Network::connect() {
  WiFiMulti.addAP(ssid, password);

  Serial.printf("Connecting to %s", ssid);

  while (WiFiMulti.run() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  webSocket.begin(host, port, "/");
  webSocket.onEvent([this](WStype_t type, uint8_t *payload, size_t length) {
    websocket_callback(type, payload, length);
  });
  webSocket.setReconnectInterval(5000);

  Serial.println();
}

void Network::websocket_callback(WStype_t type, uint8_t *payload,
                                 size_t length) {
  switch (type) {
  case WStype_CONNECTED:
    Serial.println("Websocket connected");
    break;
  case WStype_DISCONNECTED:
    Serial.println("Websocket disconnected");
    break;
  case WStype_BIN:

    break;
  default:
    break;
  }
}
