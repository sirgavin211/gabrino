
#include "MotorController.h"
#include "config.h"
#include <Arduino.h>


MotorController controller(PWMA, AIN1, AIN2, PWMB, BIN1, BIN2, freq, res);


void setup() {
  Serial.begin(115200);

  controller.setSpeed(255);

  delay(50);
}

void loop() {
  if(Serial.available() > 0){

    String input = Serial.readStringUntil('\n');
    input.trim(); // remove trailing \r or whitespace

    if(input == "w"){
      controller.forward();
    }

    if(input == "a"){
      controller.left();
    }

    if(input == "s"){
      controller.reverse();
    }

    if(input == "d"){
      controller.right();
    }

    if(input == "b"){
      controller.brake();
    }

    if(input == "+"){
      controller.increaseSpeed();
    }

    if(input == "-"){
      controller.decreaseSpeed();
    }



  }
}
