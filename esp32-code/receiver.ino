#include <HardwareSerial.h>

HardwareSerial LoRaSerial(2);

#define M0 4
#define M1 5

String buffer = "";

float P0 = 1013.25;

bool altInicialTomado = false;
float altInicial = 0.0;

float altFinal;

void setup() {
  Serial.begin(115200);
  LoRaSerial.begin(9600, SERIAL_8N1, 16, 17); // Rx, TX

  pinMode(M0, OUTPUT);
  pinMode(M1, OUTPUT);

  digitalWrite(M0, LOW);
  digitalWrite(M1, LOW);
  delay(100);

  Serial.println("Receptor listo...");
}

void loop() {
  while (LoRaSerial.available()) {
    char c = LoRaSerial.read();
    if (c == '\n') {
      Serial.print("[RAW] >>");
      Serial.print(buffer);
      Serial.println("<<");
      procesarDatos(buffer);
      buffer = "";
    } else {
      buffer += c;
    }
  }
}

void procesarDatos(String data) {
  float tempInt, humInt, presInt;
  float ax, ay, az;
  float gx, gy, gz;
  float mpuTemp;

  int parsed = sscanf(data.c_str(), "%f,%f,%f,%f,%f,%f,%f,%f,%f",
                    &tempInt, &humInt, &presInt,
                    &ax, &ay, &az,
                    &gx, &gy, &gz);

  float alt = 44330 * (1 - pow(presInt / P0, 0.1903));


  if (parsed != 9) {
    Serial.println("[Error]");
    return;
  }

  // Altitud absoluta con fórmula barométrica estándar
  float P0 = 1013.25;
  float altAbs = 44330.0 * (1.0 - pow(presInt / P0, 0.1903));

  // Tomar referencia en el primer paquete válido
  if (!altInicialTomado) {
    altInicial = altAbs;
    altInicialTomado = true;
  }

  // Altitud relativa al punto de lanzamiento
  float altFinal = altAbs - altInicial;

  String finalData = String(tempInt, 2) + "," +
                String(humInt,  2) + "," +
                String(presInt,  2) + "," +
                String(altFinal,  2) + "," +
                String(ax, 3)      + "," +
                String(ay, 3)      + "," +
                String(az, 3)      + "," +
                String(gx, 3)      + "," +
                String(gy, 3)      + "," +
                String(gz, 3);

  Serial.println(finalData);
}