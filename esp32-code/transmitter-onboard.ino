#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <Adafruit_MPU6050.h>
#include <HardwareSerial.h>

Adafruit_BME280 bme;      // interno - temperatura, humedad y presion
Adafruit_MPU6050 mpu;     // reemplaza BMP280 - acelerómetro y giroscopio
HardwareSerial LoRaSerial(2);

#define M0 4
#define M1 5

void setup() {
  Serial.begin(115200);
  LoRaSerial.begin(9600, SERIAL_8N1, 16, 17); 

  // CONFIGURACION OPCIONAL PARA BAJAR POTENCIA A LORA. //
  
  pinMode(M0, OUTPUT);
  pinMode(M1, OUTPUT);

  digitalWrite(M0, LOW);
  digitalWrite(M1, LOW);
  delay(100);

  Wire.begin(21, 22); 
  delay(100);         

  bool bmeOK = bme.begin(0x76);
  bool mpuOK = mpu.begin();

  if (bmeOK) Serial.println("BME280 OK");
  else        Serial.println("BME280 ERROR");

  if (mpuOK) {
    Serial.println("MPU6050 OK");

    // Configuración de rangos
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  } else {
    Serial.println("MPU6050 ERROR");
  }

  Serial.println("Transmisor listo");
}

void loop() {

  // --- BME280 ---
  float tempInt = bme.readTemperature();
  float humInt  = bme.readHumidity();
  float presInt = bme.readPressure() / 100; // Pa -> hPa

  // --- MPU6050 ---
  sensors_event_t accel, gyro, temp;
  mpu.getEvent(&accel, &gyro, &temp);

  float ax = accel.acceleration.x;  // m/s²
  float ay = accel.acceleration.y;
  float az = accel.acceleration.z;

  float gx = gyro.gyro.x;           // rad/s
  float gy = gyro.gyro.y;
  float gz = gyro.gyro.z;

  // --- Formato de envío ---
  // tempInt, humInt, ax, ay, az, gx, gy, gz, mpuTemp
  String data = String(tempInt, 2) + "," +
                String(humInt,  2) + "," +
                String(presInt,  2) + "," +
                String(ax, 3)      + "," +
                String(ay, 3)      + "," +
                String(az, 3)      + "," +
                String(gx, 3)      + "," +
                String(gy, 3)      + "," +
                String(gz, 3)      + ",";

  LoRaSerial.println(data);
  Serial.println("Enviado: " + data);

  delay(1000);
}