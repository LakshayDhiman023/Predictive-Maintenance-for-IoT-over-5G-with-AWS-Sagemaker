/*
  Simulating CPU Sensor Readings with Arduino & Tinkercad
  ---------------------------------------------------------
  - Temperature Sensor: LM35 connected to A0.
  - Voltage Sensor: Simulated with a potentiometer on A1.
  - Current Sensor: Simulated with a potentiometer on A2.
  - CPU Usage Monitor: Simulated with a potentiometer on A3.
  - Fan Speed Sensor: Simulated with a potentiometer on A4.
*/

void setup() {
  Serial.begin(9600);    // initialize serial communication at 9600 baud
}

void loop() {
  // Read analog values from sensors
  int tempRaw      = analogRead(A0);  // LM35 temperature sensor
  int voltageRaw   = analogRead(A1);  // simulated voltage sensor
  int currentRaw   = analogRead(A2);  // simulated current sensor
  int cpuUsageRaw  = analogRead(A3);  // simulated CPU usage monitor
  int fanSpeedRaw  = analogRead(A4);  // simulated fan speed sensor

  // Convert raw values to simulated physical units:

  // LM35 outputs 10mV per °C, so:
  float temperature = (tempRaw * (5.0 / 1023.0)) * 100.0;  // temperature in °C

  // For the other sensors, we assume a basic conversion:
  // The potentiometer gives a voltage between 0 and 5V.
  // You can adjust these factors as needed for your simulation:

  float voltage   = voltageRaw * (5.0 / 1023.0);         // Voltage in Volts
  float current   = currentRaw * (5.0 / 1023.0);           // Current in Amps (simulation scale)
  float cpuUsage  = cpuUsageRaw * (5.0 / 1023.0) * 20;       // CPU usage in % (scale factor to get 0-100%)
  float fanSpeed  = fanSpeedRaw * (5.0 / 1023.0) * 1000;     // Fan speed in RPM (simulation scale)

  // Print out sensor readings to Serial Monitor
  Serial.print("Temperature (°C): ");
  Serial.print(temperature);
  Serial.print(" | Voltage (V): ");
  Serial.print(voltage);
  Serial.print(" | Current (A): ");
  Serial.print(current);
  Serial.print(" | CPU Usage (%): ");
  Serial.print(cpuUsage);
  Serial.print(" | Fan Speed (RPM): ");
  Serial.println(fanSpeed);

  delay(1000); // delay 1 second between reads for clarity
}
