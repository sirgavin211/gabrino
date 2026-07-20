

#include "wifi_utils.h"
#include <WiFi.h>
#include "config.h"

void wifi_setup(){
  WiFi.disconnect();
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);


  Serial.print("Connecting");

  while(WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }

  Serial.println();

  Serial.println("WiFi successfully connected.");
}