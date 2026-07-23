#ifndef AUDIO_CONTROLLER_H
#define AUDIO_CONTROLLER_H

#include <ArduinoWebsockets.h>
#include <Arduino.h>
#include <ArduinoJson.h>
#include <driver/i2s_std.h>

using namespace websockets;

#define MAX_AUDIO_BUFFER 64000 
#define SAMPLE_RATE 16000
#define SAMPLE_BITS I2S_DATA_BIT_WIDTH_16BIT
#define BUFFER_SIZE   1024


enum SystemState{
  IDLE,
  PLAYING
};


class AudioController{
public:
  AudioController(int ws, int sck, int sd, int bclk, int lrc, int din, const char* host, uint16_t port, bool debug);
  void setup();
  void send();
  void play();
  void loop();
  void onMessageCallback(WebsocketsMessage message);
  
private:
  int ws, sck, sd;
  int bclk, lrc, din;
  const char* host;
  uint16_t port;
  bool recording;
  WebsocketsClient client;
  String ws_url;
  bool debug;
  SystemState currentState;

  void setupMicI2S();
  void setupSpeakerI2S();

  i2s_chan_handle_t rx_handle = NULL;
  i2s_chan_handle_t tx_handle = NULL;

  uint8_t audioData[MAX_AUDIO_BUFFER];
  uint32_t audioDataSize = 0;
};

#endif