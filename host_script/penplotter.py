import serial
import time
from typing import NamedTuple

ENDLINE = b'\r\n'
OK = b'ok\r\n'
ERROR = b'error:'

JOG_CANCEL = bytes(0x85)


class Point(NamedTuple):
    x: float
    y: float

class CommError(Exception):
    pass

class GrblError(CommError):
    def __init__(self, code: int, *args: object) -> None:
        self.code = code
        super().__init__(*args)

class InvalidStateError(CommError):
    pass

class PenPlotter():
    def __init__(self, ser: serial.Serial) -> None:
        self.ser = ser

    def reset(self):
        self.ser.write(ENDLINE * 2)
        time.sleep(2)
        self.ser.flushInput()

    def write_with_error(self, command: bytes) -> None:
        if not self.ser.is_open:
            raise RuntimeError(f'Serial port closed: {self.ser}')

        self.ser.write(command)

        response = self.ser.read_until(expected=ENDLINE)
        if response != OK:
            if ERROR in response:
                error_code = int(response.decode('ascii').strip().split(':')[1])
                raise GrblError(error_code)

            raise InvalidStateError(f'Got invalid grbl response "{response}" to command "{command}"')


    def move_and_stop(self, pos: Point, speed: int = 1000):
        command = f'$J=G90X{pos.x}Y{pos.y}F{speed}'.encode('ascii') + ENDLINE
        wait_command = b'G4P0.01' + ENDLINE

        self.write_with_error(command)
        time.sleep(0.2)
        self.ser.write(JOG_CANCEL)
        while True:
            try:
                time.sleep(0.2)
                self.ser.flushInput()
                self.write_with_error(wait_command)
            except GrblError as err:
                if err.code != 9:
                    raise err
            else:
                break
