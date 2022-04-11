from pathlib import Path

from .base_cnc import CNC

class FileCNC(CNC):
    def __init__(self, filepath:Path) -> None:
        self._path = filepath

    @property
    def path(self):
        return self._path

    def open(self):
        self._fp = open(self.path, "w")
        return self

    def close(self):
        self._fp.close()

    def write(self, data: str, timeout: float = None):
        self._fp.write(data)

    def read(self, timeout: float = None) -> str:
        # This previously raised NotImplementedError, but I changed
        # it to return an empty string, since every write call in the 
        # Mongoose class requires a read call, and therefore any write
        # to a FileCNC using Mongoose raised an error.
        return ""
