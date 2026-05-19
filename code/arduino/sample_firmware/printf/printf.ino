#include <stdio.h>

#define FIRMWARE_VERSION 11      // Đại diện cho v2.0
#define FIRMWARE_ID 1000

void setup() {
  Serial.begin(115200);
  Serial.println("firmware printf is setuped");
}

void loop() {
  // put your main code here, to run repeatedly:
  delay(10000);
  Serial.println("firmware printf is looped");
}
