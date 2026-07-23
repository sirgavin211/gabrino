

#ifndef MOTOR_CONTROLLER_H
#define MOTOR_CONTROLLER_H

#include <ArduinoWebsocket.h>
#include <Arduino.h>

using namespace websocket;

class MotorController{

public:
  MotorController(int PWMA, int AIN1, int AIN2, int PWMB, int BIN1, int BIN2, int freq, int res);
  void forward();
  void reverse();

  void brake();

  void left();
  void right();

  void setSpeed(int speed);
  void increaseSpeed();
  void decreaseSpeed();

  void onMessageCallback(WebsocketsMessage message);

private:
  int speed;
  int ain1, ain2, pwmA, bin1, bin2, pwmB;

};

#endif