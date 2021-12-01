import time
import json
from typing import Generator, NamedTuple, Optional
from pandas.core.frame import DataFrame

import serial
from mpl_toolkits import mplot3d as Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
import pandas as pd

from penplotter import Point, PenPlotter


CNC_PORT = 'COM6'
ARDUINO_PORT = 'COM4'
CNC_BAUD = ARDUINO_BAUD = 115200

ARDUINO_TAKE_READING = b'm'
ARDUINO_CHECK_OK = b'r'
ARDUINO_FAIL = b'fail'

class SerialDebugProxy(serial.Serial):
    PREFIX = ''

    def write(self, data: bytes) -> int:
        print(f'->{self.PREFIX}: {data.decode("ascii").strip()}')
        return super().write(data)
    
    def read_until(self, expected: bytes):
        out = super().read_until(expected=expected)
        print(f'<-{self.PREFIX} {out.decode("ascii").strip()}')
        return out

    def readline(self):
        out = super().readline()
        print(f'<-{self.PREFIX} {out.decode("ascii").strip()}')
        return out

class CNCDebugProxy(SerialDebugProxy):
    PREFIX = 'cnc'

class ArduinoDebugProxy(SerialDebugProxy):
    PREFIX = 'arduino'

class SensorReading(NamedTuple):
    ultra: int
    intensity: int
    lidar: Optional[int] = None

class DataPoint(NamedTuple):
    x: float
    y: float
    intensity: int
    ultra: int
    lidar: Optional[int]

    @staticmethod
    def factory(p: Point, r: SensorReading) -> 'DataPoint':
        return DataPoint(p.x, p.y, r.intensity, r.ultra, r.lidar)

def point_grid_zigzag(gridsize: int, gridinc: int) -> Generator[Point, None, None]:
    for i, x in enumerate(range(0, gridsize + gridinc, gridinc)):
        itery = range(0, gridsize + gridinc, gridinc)
        if i % 2 != 0:
            itery = reversed(itery)
        for y in itery:
            yield Point(x, y)

def take_reading(ser: serial.Serial) -> SensorReading:
    ser.write(ARDUINO_TAKE_READING)
    reading = ser.readline()
    if ARDUINO_FAIL in reading:
        raise RuntimeError(f'Got unexpected output: {reading.decode("ascii")}')
    decoded = json.loads(reading)
    return SensorReading(**decoded)

def wait_or_fail(ser: serial.Serial, check: bytes):
    line = ser.read_until(check)
    if check not in line:
        raise TimeoutError(f'Error when waiting for string "{check}"')

if __name__ == '__main__':
    with CNCDebugProxy(CNC_PORT, CNC_BAUD, timeout=100) as cncser, \
        ArduinoDebugProxy(ARDUINO_PORT, ARDUINO_BAUD, timeout=2) as arduinoser:
        
        plotter = PenPlotter(cncser)
        plotter.reset()
        
        try:
            wait_or_fail(arduinoser, b'Ready!\r\n')
        except TimeoutError:
            arduinoser.write(ARDUINO_CHECK_OK)
            wait_or_fail(arduinoser, b'ok\r\n')

        arduinoser.flushInput()

        print('Devices setup successfully')

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_zlim(0, 1024)
        plt.show(block=False)
        plt.draw()

        graph, = ax.plot([0], [0], [0], '.')

        lidar_points = pd.DataFrame(columns=DataPoint._fields)

        plotter.move_and_stop(Point(-1, 0))
        time.sleep(1)

        for point in point_grid_zigzag(160, 4):
            plotter.move_and_stop(point)

            points = []
            for _ in range(5):
                measure = take_reading(arduinoser)
                points.append(DataPoint.factory(point, measure))
            lidar_points = pd.concat((lidar_points, pd.DataFrame.from_records(points, columns=DataPoint._fields)), ignore_index=True)

            lidar_points.to_csv('out.csv', index=False)
            z = lidar_points['lidar'].fillna(0).array
            graph.set_data_3d(lidar_points['x'].array, lidar_points['y'].array, z)
            fig.canvas.draw()
            plt.pause(0.01)
        