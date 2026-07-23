
#include "network_manager.h"


NetworkManager::NetworkManager(AudioController* audio, MotorController controller, const char* host, uint16_t port){
  this->audio = audio;
  this->controller = controller;
  ws_url = String("ws://") + host + ":" + String(port);
}


void NetworkManager::setup(){
  client.onMessage([this](WebsocketsMessage message){
    onMessageCallback(message);
  });

  client.onEvent([this](WebsocketsEvent event, String data){
    onEventCallback(event, data);
  });

  while (!client.available()){
    client.connect(ws_url);
    delay(50);
  }

  Serial.print("Websocket connected to ");
  Serial.println(ws_url);
}


void NetworkManager::check(){
  Serial.print("Reconnecting...")

  while(!client.available()){
    Serial.print(".");
    client.connect(ws_url);
    delay(50);
  }

  Serial.println();
}

void NetworkManager::onMessageCallback(WebsocketsMessage message){
  audio.onMessageCallback(message);
  controller.onMessageCallback(message);
}


void AudioController::onEventCallback(WebsocketsEvent event, String data) 
{
  if (event == WebsocketsEvent::ConnectionOpened) {
    Serial.println("WebSocket Connected!");
  } 
  else if (event == WebsocketsEvent::ConnectionClosed) {
    Serial.println("WebSocket Disconnected!");
  } 
  else if (event == WebsocketsEvent::GotPing) {
    Serial.println("Got ping from server!");
  } 
  else if (event == WebsocketsEvent::GotPong) {
    Serial.println("Got pong from server!");
  }
}



