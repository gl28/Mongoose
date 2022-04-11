
from serial import Serial

from mongoose.mongoose import MongooseError

from .base_cnc import CNC
import re

class Genmitsu3018CNC(CNC):
    def __init__(self, port: str) -> None:
        self._port = port
        self._timeout = 2

    @property
    def port(self):
        return self._port

    def open(self):
        self._ser = Serial(self._port, baudrate=115200, timeout=self._timeout, exclusive=True)
        self._ser.reset_input_buffer()
        self._ser.reset_output_buffer()
        self._ser.write(bytearray([24, 88, 10]))
        self.read()
        return self

    def close(self):
        if self._ser:
            self._ser.close()

    def write(self, data: str) -> int:
        bytes_written = self._ser.write(data.encode())
        return bytes_written

    def read(self) -> str:
        done_regex = re.compile(r"(ok)|(error\: \d+)|(alarm\: \d+)|(^Grbl.*)")
        lines = list()
        endline = "\r\n".encode()

        while True:
            new_line = self._ser.read_until(endline).decode()
            if not new_line:
                break

            lines.append(new_line)
            m = done_regex.match(new_line)
            if m:
                ok, error, alarm, start_up = m.groups()
                if ok or start_up:
                    break
                if error:
                    raise MongooseError(f"Command failed with error: {error}")
                if alarm:
                    raise MongooseError(f"Command failed with alarm: {error}")
        
        return "\n".join(lines)