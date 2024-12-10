class Rocker {
  protected:
    int GND, VCC, VAX, VAY, SW;
    char buffer[50];
  public:
    Rocker(int VAX, int VAY, int SW, int GND = -999, int VCC = -999) {
      this->GND = GND;
      this->VCC = VCC;
      this->VAX = VAX;
      this->VAY = VAY;
      this->SW = SW;
      if (GND != -999) {
        pinMode(GND, OUTPUT);
        digitalWrite(GND, 0);
      };
      if (VCC != -999) {
        pinMode(VCC, OUTPUT);
        digitalWrite(VCC, 1);
      };
      pinMode(VAX, INPUT);
      pinMode(VAY, INPUT);
      pinMode(SW, INPUT);
    };
    void send(void) {
      int x = analogRead(this->VAX);
      int y = analogRead(this->VAY);
      int sw = analogRead(this->SW);
      sprintf(buffer, "Start;Rocker: %d, %d, %d;End;", x, y, sw);
      Serial.println(buffer);
    };
};

class Button {
  protected:
    int GND, VCC, SW;
    char buffer[20];
  public:
    Button(int SW, int Vcc = -999, int GND = -999) {
      this->GND = GND;
      this->VCC = VCC;
      this->SW = SW;
      if (GND != -999) {
        pinMode(GND, OUTPUT);
        digitalWrite(GND, 0);
      };
      if (VCC != -999) {
        pinMode(VCC, OUTPUT);
        digitalWrite(VCC, 1);
      };
      pinMode(SW, INPUT);
    };
    void send(void) {
      int sw = analogRead(this->SW);
      sprintf(buffer, "Start;Button: %d;End;", sw);
      Serial.println(buffer);
    };
};

Rocker rocker(A1, A2, A3);
// Button button(6, 7, 5);
void setup() {
  Serial.begin(57600);
  pinMode(5, INPUT);
};

void loop() {
  rocker.send();
  delay(10);
};
