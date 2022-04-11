from copy import copy
from typing import Tuple
from mongoose.cnc import CNC, FileCNC
from mongoose.grbl import GrblError, GrblAlarm
import math


class MongooseError(Exception):
    pass


class Mongoose:
    def __init__(self, cnc: CNC, safe_z: float = 5, atomic: bool = True) -> None:
        self._cnc = cnc
        self._grbl_settings = None
        self._grbl_status = dict()
        self.safe_z = safe_z

        # initial state
        self._atomic = atomic
        self._increment_mode = None

    def send_command(self, cmd: str, with_newline: bool = True) -> str:
        # Realtime commands (like `?` for status report) can be
        # sent without newline character. But for FileCNC, newline
        # is required.
        self._cnc.write(cmd + "\n" if with_newline or isinstance(self._cnc, FileCNC) else cmd)
        return self._cnc.read()

    @property
    def grbl_settings(self) -> dict:
        return copy(self._grbl_settings)

    def _get_grbl_settings(self) -> dict:
        response = self.send_command("$$")
        settings_words = response.split("\r\n\n")
        grbl_settings = dict()

        for w in settings_words:
            if w and w[0] == "$":
                key, value = w.split("=")
                if "." in value:
                    grbl_settings[key] = float(value)
                else:
                    grbl_settings[key] = int(value)

        return grbl_settings

    @grbl_settings.setter
    def grbl_settings(self, new_settings: dict):
        for key, value in new_settings:
            if key not in self._get_grbl_settings:
                raise KeyError("Bad grbl setting key")

            self.send_command(f"{key}={value}")
            self._grbl_settings[key] = value

    def home(self):
        self.send_command("$H")

    def _unlock(self):
        self.send_command("$X")

    @property
    def atomic(self) -> bool:
        return self._atomic

    @atomic.setter
    def atomic(self, enabled: bool):
        self._atomic = enabled

    @property
    def increment_mode(self) -> bool:
        return self._increment_mode

    @increment_mode.setter
    def increment_mode(self, enabled: bool):
        if self._increment_mode != enabled:
            self.send_command("G91" if enabled else "G90")
            self._increment_mode = enabled

    def wait_for_finish(self):
        # TODO: implement wait for finish
        pass

    def _linear_motion(self, cmd: str, x: float, y: float, z: float, feed: float, atomic: bool):
        cmd_args = [("X", x), ("Y", y), ("Z", z), ("F", feed)]
        cmd_str = cmd + " " + \
            " ".join((f"{prefix}{value:.3f}" for prefix,
                     value in cmd_args if value is not None))

        self.send_command(cmd_str)

        atomic = self.atomic if atomic is None else atomic
        if atomic:
            self.wait_for_finish()

    def move_to(self, x: float = None, y: float = None, z: float = None, atomic: bool = None):
        # TODO: soft limits checking
        self.increment_mode = False
        self._linear_motion("G0", x, y, z, None, atomic)

    def move(self,  x: float = None, y: float = None, z: float = None, atomic: bool = None):
        # TODO: soft limits checking
        self.increment_mode = True
        self._linear_motion("G0", x, y, z, None, atomic)

    def mill_to(self, x: float = None, y: float = None, z: float = None, feed: float = 300, atomic: bool = None):
        # TODO: soft limits checking
        self.increment_mode = False
        self._linear_motion("G1", x, y, z, feed, atomic)

    def mill(self,  x: float = None, y: float = None, z: float = None, feed: float = 300, atomic: bool = None):
        # TODO: soft limits checking
        self.increment_mode = True
        self._linear_motion("G1", x, y, z, feed, atomic)

    def _update_status(self):
        # Updates machine position and work coordinate offset
        # <Idle|MPos:0.000,0.000,0.000|FS:0,0|WCO:0.000,0.000,0.000>
        status = self.send_command("?", False)
        status_words = status.split("|")

        for w in status_words:
            # WCO is only sent in the status report if it has changed since last
            # status report. (It's also sent intermittently regardless of change.)
            if w and w[:3] == "WCO":
                _, positions = w.split(":")
                x, y, z_chunk = positions.split(",")
                if ">" in z_chunk:
                    z, _ = z_chunk.split(">", maxsplit=1)
                else:
                    z = z_chunk
                self._grbl_status["work_coordinate_offset"] = (float(x), float(y), float(z))
            
            # MPos is always sent in the status report.
            if w and w[:4] == "MPos":
                _, positions = w.split(":")
                x, y, z_chunk = positions.split(",")
                if ">" in z_chunk:
                    z, _ = z_chunk.split(">", maxsplit=1)
                else:
                    z = z_chunk
                self._grbl_status["machine_position"] = (float(x), float(y), float(z))


    def set_work_coordinate_offset(self):
        # Sets work coordinates to (0, 0, 0) at current position
        # TODO: create option to set work coordinates based on input values?
        self.send_command("G10 L20 P0 X0 Y0 Z0")
        self._update_status()

    def get_work_coordinate_offset(self) -> Tuple[float, float, float]:
        self._update_status()
        return self._grbl_status["work_coordinate_offset"]

    def machine_position(self) -> Tuple[float, float, float]:        
        self._update_status()
        return self._grbl_status["machine_position"]

    def work_position(self) -> Tuple[float, float, float]:
        self._update_status()
        coordinates = zip(self._grbl_status["machine_position"], self._grbl_status["work_coordinate_offset"])
        return tuple([mpos - wco for mpos, wco in coordinates])

    def work_volume(self) -> Tuple[float, float, float]:
        if "$130" in self._grbl_settings:
            return (self._grbl_settings["$130"], self._grbl_settings["$131"], self._grbl_settings["$132"])
        
        # added this exception in to make it possible to use a FileCNC, since FileCNC doesn't have settings
        return (200.0, 200.0, 200.0)

    def square(self, x: float, y: float, z: float, side_length: float, feed: float = 300):
        self.move_to(z=self.safe_z)
        self.move_to(x=x, y=y)
        self.mill_to(z=z, feed=feed)
        self.mill(x=side_length, feed=feed)
        self.mill(y=side_length, feed=feed)
        self.mill(x=-side_length, feed=feed)
        self.mill(y=-side_length, feed=feed)

    def circle(self, x: float, y: float, z: float, radius: float, feed: float = 300, atomic: bool= None):
        x,y,z  = x + radius, y, z
        i,j,k = -radius,0,None
        cmd_args = [("X", x), ("Y", y), ("Z", z), ("I", i), ("J", j), ("K", k), ("F", feed)]
        cmd = "G2"
        cmd_str = cmd + " " + \
            " ".join((f"{prefix}{value:.3f}" for prefix,
                     value in cmd_args if value is not None))

        self.move_to(z=self.safe_z)
        self.move_to(x=x, y=y)
        self.mill_to(z=z, feed=feed)
        
        self.send_command(cmd_str)

        atomic = self.atomic if atomic is None else atomic
        if atomic:
            self.wait_for_finish()

    def polygon(self, sides: int, x: float, y: float, z: float, radius: float, feed: float, atomic: bool = None):
        self.move_to(z=self.safe_z)
        self.move_to(x + radius, y)
        self.mill_to(z=z, feed=feed)
        
        for i in range(1, sides):
            next_x = x + radius * math.cos(2 * math.pi * i / sides)
            next_y = y + radius * math.sin(2 * math.pi * i / sides)
            self.mill_to(next_x, next_y, feed=feed)
        
        self.mill_to(x + radius, y, feed=feed)


    def open(self):
        self._cnc.open()
        self._grbl_settings = self._get_grbl_settings()
        self.increment_mode = False

    def close(self):
        self.move_to(z=self.safe_z)
        self._cnc.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()
