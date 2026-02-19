const int ldrPin = A0;
const int potPin = A1;
const int temPin = A2;

const int ledPin = 8;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  pinMode(ledPin, OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  // set the brightness of pin 9:
  int ldrValue = analogRead(ldrPin);
  int potValue = analogRead(potPin);
  int tempValue = analogRead(tempPin);

  // transmitting sensor data as CSV
  Serial.println(ldrValue);
  Serial.println(",");
  Serial.println(potValue);
  Serial.println(",");
  Serial.println(tempValue);

  if (Serial.available() > 0) {
    char command = Serial.read();

    if (command == 'H') {
      digitalWrite(ledPin, HIGH);
    }
    else if (command == 'L') {
      digitalWrite(ledPin, LOW);
    }
  }
  
  delay(50);
}
