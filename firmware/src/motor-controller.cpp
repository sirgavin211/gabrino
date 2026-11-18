

#include "esp32-hal-gpio.h"
#include <motor-controller.h>

void motor_setup() {}

void Motor::setup() {
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  ledcSetup(ch, 5000, 8);
  ledcAttachPin(pwm, ch);
}

void Motor::drive(int speed) {
  ledcWrite(ch, std::abs(speed));

  if (speed > 0) {
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
  } else if (speed < 0) {
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
  } else {
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
  }
}

void Motor::brake() {
  digitalWrite(in2, HIGH);
  digitalWrite(in1, HIGH);
}
