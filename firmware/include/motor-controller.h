#pragma once
#include <Arduino.h>

struct motor {
  int in1, in2, pwm, ch;

  void setup();
  void drive(int speed);
  void brake();
};

void motor_setup();
