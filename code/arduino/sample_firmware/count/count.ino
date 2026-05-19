#include <stdio.h>

int count = 0;

void setup() {
  Serial.begin(115200);
  Serial.println("firmware count is setuped");
}

void loop() {
  Serial.printf("count = %d", count);
  count++;

  if (count == 10000) {
    Serial.println("firmware count is reach 10000, return 0");
    count = 0;
  }
}
