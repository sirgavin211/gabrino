

#ifndef CONFIG_H
#define CONFIG_H



#include <Arduino.h>


#define PWMA 13
#define AIN1 14
#define AIN2 15
#define PWMB 21
#define BIN1 18
#define BIN2 19


const int freq = 5000;
const int res = 8;


#define MIC_SD 25
#define MIC_WS 26
#define MIC_SCK 27

#define SPEAKER_DIN 35
#define SPEAKER_BCLK 32
#define SPEAKER_LRCLK 33

constexpr const char* ssid = "RacingDragon";
constexpr const char* password = "21doatcfhas";

constexpr const char* server_host = "192.168.1.18";
constexpr const uint16_t server_port = 8765;
constexpr int port = 5000;


#endif
