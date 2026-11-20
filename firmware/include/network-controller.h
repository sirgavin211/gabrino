#pragma once

#include "WebSockets.h"
#include "audio-controller.h"
#include <HTTPClient.h>
#include <WebSocketsClient.h>
#include <WiFi.h>
#include <WiFiMulti.h>
#include <cstddef>
#include <cstdint>
#include <sys/types.h>

class Network {
public:
  Network(const char *ssid, const char *password, const char *host,
          uint16_t port);
  void connect();
  void send_audio(Sample sample);
  Sample get_audio();

private:
  const char *ssid;
  const char *password;
  const char *host;
  uint16_t port;
  WiFiMulti WiFiMulti;
  std::vector<Sample> data_queue;
  void websocket_callback(WStype_t type, uint8_t *payload, size_t length);
  WebSocketsClient webSocket;
};
