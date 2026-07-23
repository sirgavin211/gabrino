
#include "motor_controller.h"
#include "audio_controller.h"
// #include "gabrino_mouth.h"

#include "config.h"
#include <Arduino.h>
#include "wifi_utils.h"

MotorController controller(PWMA, AIN1, AIN2, PWMB, BIN1, BIN2, freq, res);
AudioController audio(MIC_WS, MIC_SCK, MIC_SD, SPEAKER_BCLK, SPEAKER_LRCLK, SPEAKER_DIN, server_host, server_port, false);



void setup() {
  Serial.begin(115200);

  wifi_setup();
  audio.setup();
  // mouth.setup();
  controller.setSpeed(255);
  controller.brake();

  Serial.println("Gabrino V7 (robot lil bro)");

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

    if(input == "play"){
      audio.play();
    }

  }

  audio.loop();
  // audio.send();


}

