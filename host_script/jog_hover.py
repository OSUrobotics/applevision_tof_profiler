import serial
import time
import itertools
from typing import Generator, NamedTuple

PORT = 'COM3'
BAUD = 115200

ENDLINE = b'\r\n'
OK = b'ok\r\n'
ERROR = b'error:'

JOG_CANCEL = bytes(0x85)

class SerialDebugProxy(serial.Serial):
    def write(self, data: bytes) -> int:
        print(f'->cnc: {data.decode("ascii").strip()}')
        return super().write(data)
    
    def read_until(self, expected: bytes):
        out = super().read_until(expected=expected)
        print(f'<-cnc {out.decode("ascii").strip()}')
        return out


class Point(NamedTuple):
    x: float
    y: float

class CommError(Exception):
    pass

class GrblError(CommError):
    code: int

class InvalidStateError(CommError):
    pass

def write_with_error(ser: serial.Serial, command: bytes) -> None:
    if not ser.is_open:
        raise RuntimeError(f'Serial port closed: {ser}')

    ser.write(command)

    response = ser.read_until(expected=ENDLINE)
    if response != OK:
        if ERROR in response:
            error_code = int(response.decode('ascii').strip().split(':')[1])
            raise GrblError(error_code)

        raise InvalidStateError(f'Got invalid grbl response "{response}" to command "{command}"')


def move_and_stop(ser: serial.Serial, pos: Point, speed: int = 1000):
    command = f'G0X{pos.x}Y{pos.y}F{speed}'.encode('ascii') + ENDLINE
    wait_command = b'G4P0.01' + ENDLINE

    write_with_error(ser, command)
    write_with_error(ser, JOG_CANCEL)
    write_with_error(ser, wait_command)
    write_with_error(ser, wait_command)


def point_grid_zigzag(gridsize: int) -> Generator[Point, None, None]:
    for x in range(0, 100, 5):
        itery = range(0, 100, 5)
        if x % 2 != 0:
            itery = reversed(itery)
        for y in itery:
            yield Point(x, y)


if __name__ == '__main__':
    with SerialDebugProxy(PORT, BAUD, timeout=100) as ser:
        ser.write(ENDLINE * 2)
        time.sleep(2)
        ser.flushInput()

        for x in range(0, 100, 5):
            itery = range(0, 100, 5)
            if x % 2 != 0:
                itery = reversed(itery)
            for y in itery:
                move_and_stop(ser, Point(x, y))
        # read GRBL version
        # set coordinates to 0
        # for 