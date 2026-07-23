

#ifndef NETWORK_MANAGER_H
#define NETWORK_MANAGER_H


#include <ArduinoWebsockets.h>
#include <Arduino.h>
#include <ArduinoJson.h>

#include <audio_controller.h>
#include <motor_controller.h>


using namespace websockets;

class NetworkManager{

public:
  NetworkManager(AudioController* audio, MotorController* controller);
  void setup();
  void check();

private:
  WebsocketsClient client;
  AudioController* audio;
  MotorController* controller;
  void onMessageCallback(WebsocketsMessage message);
  void onEventCallback(WebsocketsEvent event, String data);
  String ws_url;

};

#endif