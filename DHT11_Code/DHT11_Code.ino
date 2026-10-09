#include <DHT.h>
#define DHTPIN 2    // Pin connected to DHT11 data pin
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
void setup() {
  Serial.begin(9600);
  dht.begin();
}
void loop() {
  float h = dht.readHumidity(); // Percentage
  float t = dht.readTemperature(); // Celsius

  if (isnan(h) || isnan(t)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
  Serial.print("Temp:");
  Serial.print(t);
  Serial.print(",Humidity:");
  Serial.println(h);
  delay(500);
}
