"""
This type stub file was generated by pyright.
"""

class Color:
    R: float
    G: float
    B: float
    A: float
    def __init__(
        self, r: float = ..., g: float = ..., b: float = ..., a: float = ...
    ) -> None: ...
    def __eq__(self, other) -> bool: ...
    def __add__(self, other): ...
    def __sub__(self, other): ...
    def __mul__(self, other): ...
    def __div__(self, other): ...
    def __eq__(self, other) -> bool: ...
    def __ne__(self, other) -> bool: ...
    def Vector4(self): ...
