#include "audio-controller.h"
#include "motor-controller.h"
#include "network-controller.h"
#include "robot-config.h"
#include <Arduino.h>

motor left_motor{left_motor_1, left_motor_2, pwma_pin, 0};
motor right_motor{right_motor_1, right_motor_2, pwmb_pin, 1};
Microphone mic;
Network network(ssid, password, host, port);

void setup() {
  left_motor.setup();
  right_motor.setup();
  mic.setup();
}

void loop() {
  Sample s = mic.read();
  Serial.printf("Bytes Read: %d \n", s.bytes_read);

  for (int32_t byte : s.buf) {
    Serial.printf("%d, ", byte);
  }

  delay(5000);
}
