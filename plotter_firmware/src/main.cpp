#include <stdnoreturn.h>
#include <Arduino.h>
#include <Adafruit_APDS9960_SoftWire.h>
#include "wiring_private.h"
#include "FeatherTrace.h"
#include "Adafruit_VL53L0X.h"
#include "SlowSoftI2CMaster.h"
#include "SlowSoftWire.h"

constexpr uint8_t MATBOTIX_WRITE_ADDR = 224;
constexpr uint8_t MATBOTIX_TAKE_READING = 81;
constexpr uint8_t MATBOTIX_READ_ADDR = 225;

FEATHERTRACE_BIND_ALL()

SlowSoftWire lidar_i2c(A0, A1, false);
Adafruit_VL53L0X lidar;
SlowSoftWire apds_i2c(11, 10, false);
Adafruit_APDS9960 intensity;
SlowSoftI2CMaster ultra_i2c(9, 6, true);

void fail(const char* const msg) {
    Serial.println(msg);
    FeatherTrace::Fault(FeatherTrace::FAULT_USER);
}

void setup() {
    // put your setup code here, to run once:
    Serial.begin(115200);
    while(!Serial);
    if (FeatherTrace::DidFault())
      FeatherTrace::PrintFault(Serial);
    Serial.flush();
    // set the watchdog timer to 8 seconds
    FeatherTrace::StartWDT(FeatherTrace::WDTTimeout::WDT_8S);

    Serial.println("Init");
    if (!lidar.begin(VL53L0X_I2C_ADDR, true, &lidar_i2c, Adafruit_VL53L0X::VL53L0X_SENSE_HIGH_ACCURACY))
        fail("Lidar init");

    if (!intensity.begin(200, APDS9960_AGAIN_1X, 0x39, &apds_i2c))
        fail("Intensity init");
    intensity.setProxGain(APDS9960_PGAIN_4X);
    intensity.setLED(APDS9960_LEDDRIVE_100MA, APDS9960_LEDBOOST_100PCNT);
    intensity.setProxPulse(APDS9960_PPULSELEN_16US, 8);
    intensity.enableProximity(true);

    if (!ultra_i2c.i2c_init())
        fail("ultra i2c init");
    if (!ultra_i2c.i2c_start(MATBOTIX_WRITE_ADDR))
        fail("ultra not connected");
    ultra_i2c.i2c_stop();

    MARK;
    Serial.println("Ready!");
    Serial.flush();
}

void take_reading() {
    if (!ultra_i2c.i2c_start(MATBOTIX_WRITE_ADDR))
        fail("ultra not connected");
    ultra_i2c.i2c_write(MATBOTIX_TAKE_READING);
    ultra_i2c.i2c_stop();

    VL53L0X_RangingMeasurementData_t measure;
    lidar.rangingTest(&measure, false);

    bool lidar_valid = false;
    uint16_t lidar_dist = 0;
    if (measure.RangeStatus != 4) {
        lidar_valid = true;
        lidar_dist = measure.RangeMilliMeter;
    }
    else
        lidar_valid = false;

    uint16_t prox_dist = intensity.readProximity();

    if (!ultra_i2c.i2c_start_wait(MATBOTIX_READ_ADDR))
        fail("ultra not connected read");
    uint8_t high = ultra_i2c.i2c_read(false);
    uint8_t low = ultra_i2c.i2c_read(false);
    ultra_i2c.i2c_stop();
    uint16_t ultra_dist = ((uint16_t)high << 8) | (uint16_t)low;

    char buf[1024];
    if (lidar_valid)
        snprintf(buf, sizeof(buf), R"({"lidar": %hu, "intensity": %hu, "ultra": %hu})", lidar_dist, prox_dist, ultra_dist);
    else
        snprintf(buf, sizeof(buf), R"({"intensity": %hu, "ultra": %hu})", prox_dist, ultra_dist);
    Serial.println(buf);
}

void loop() {
    MARK;
    while (!Serial.available())
        MARK;

    const char read = Serial.read();
    switch (read) {
        case 'm':
            take_reading();
            break;
        case 'r':
            Serial.println("ok");
            break;
        default: ;
    }
}