from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Type

class CNC(ABC):
    __subclasses = dict()
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        CNC.__subclasses[cls.__name__] = cls

    @classmethod
    def from_name(cls, name:str)-> Type[CNC]:
        return cls.__subclasses[name]

    @abstractmethod
    def open(self):
        pass
    
    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def write(self, data:str, timeout:float=None):
        pass
    @abstractmethod
    def read(self, timeout:float=None)->str:
        pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    