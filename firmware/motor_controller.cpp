#include "WString.h"


#include "motor_controller.h"
#include <Arduino.h>

MotorController::MotorController(int PWMA, int AIN1, int AIN2, int PWMB, int BIN1, int BIN2, int freq, int res){
  
  ain1 = AIN1; pwmA = PWMA; ain2 = AIN2; pwmB = PWMB; bin1 = BIN1; bin2 = BIN2;

  pinMode(ain1, OUTPUT);
  pinMode(ain2, OUTPUT);
  pinMode(bin1, OUTPUT);
  pinMode(bin2, OUTPUT);

  ledcAttachChannel(pwmA, freq, res, 0);
  ledcAttachChannel(pwmB, freq, res, 0);

  Serial.println(String("Motor Controller running on pins -> ") +
                "PWMA:" + pwmA + " AIN1:" + ain1 + " AIN2:" + ain2 +
                " PWMB:" + pwmB + " BIN1:" + bin1 + " BIN2:" + bin2);

}

void MotorController::forward(){
  digitalWrite(ain1, HIGH);
  digitalWrite(ain2, LOW);

  digitalWrite(bin1, HIGH);
  digitalWrite(bin2, LOW);
}

void MotorController::reverse(){
  digitalWrite(ain1, LOW);
  digitalWrite(ain2, HIGH);

  digitalWrite(bin1, LOW);
  digitalWrite(bin2, HIGH);
}

void MotorController::left(){
  digitalWrite(ain1, LOW);
  digitalWrite(ain2, HIGH);

  digitalWrite(bin1, HIGH);
  digitalWrite(bin2, LOW);
}

void MotorController::right(){
  digitalWrite(ain1, HIGH);
  digitalWrite(ain2, LOW);

  digitalWrite(bin1, LOW);
  digitalWrite(bin2, HIGH);
}

void MotorController::setSpeed(int speed){
  this->speed = speed;
  ledcWrite(pwmA, speed);
  ledcWrite(pwmB, speed);
}

void MotorController::decreaseSpeed(){
  int new_speed = speed - 255/10;

  if(new_speed < 0){
    new_speed = 0;
  }

  setSpeed(new_speed);
}
void MotorController::increaseSpeed(){
  int new_speed = speed + 255/10;

  if(new_speed > 255){
    new_speed = 255;
  }

  setSpeed(new_speed);
}


void MotorController::brake(){
  digitalWrite(ain1, LOW);
  digitalWrite(ain2, LOW);

  digitalWrite(bin1, LOW);
  digitalWrite(bin2, LOW);
}
