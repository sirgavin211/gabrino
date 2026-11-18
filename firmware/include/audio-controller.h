#pragma once

#include <driver/i2s.h>

extern const i2s_config_t config;
extern const i2s_pin_config_t pin_config;

struct Sample {
  int32_t buf[512];
  size_t bytes_read;
};

struct Microphone {
  void setup();
  Sample read();
};
