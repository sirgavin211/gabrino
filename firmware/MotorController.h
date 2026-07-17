

#ifndef MOTOR_CONTROLLER_H
#define MOTOR_CONTROLLER_H

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

private:
  int speed;
  int ain1, ain2, pwmA, bin1, bin2, pwmB;

};

#endif