# Data Format

This folder contains raw readings from the three distance sensors at various XY points. The title of the CSV corresponds to a scanning setup as described in section 2.1.4 of the handoff document TODO. There are four columns present in each CSV:

* `x`, `y` - 2D displacement in millimeters from the top left corner of the scan area.
* `intensity` - Raw value from the APDS9960 proximity sensor ADC. Value is a single byte (0-255). Gain, pulse length, and other sensor settings used during the scan can be found in the [sensor code](../plotter_firmware/src/main.cpp).
* `ultra` - Measured distance in centimeters from the MB1213 ultrasonic sensor.
* `lidar` - Measured distance in millimeters from the VL53L0X ToF sensor. Adafruit's `VL53L0X_SENSE_HIGH_ACCURACY` profile was used for measurement: specific setting values can be found under [`Adafruit_VL53L0X::configSensor`](../plotter_firmware/lib/Adafruit_VL53L0X-master/src/Adafruit_VL53L0X.cpp).

All data files measured a 160mm by 160mm area with a 4mm increment. Five measurements were taken at each grid point to minimize error caused by stopping/starting.

For examples of processing this data, see the scripts in [`visualization_scripts`](../visualization_scripts).