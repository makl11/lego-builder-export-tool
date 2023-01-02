"""
This type stub file was generated by pyright.
"""

from .Vector3 import Vector3

class Matrix4x4:
    M: list
    def __init__(self, values) -> None: ...
    def __getitem__(self, index): ...
    def __setitem__(self, index, value): ...
    def __eq__(self, other) -> bool: ...
    def __mul__(lhs, rhs): ...
    @staticmethod
    def Scale(vector: Vector3): ...
    @property
    def M00(self): ...
    @M00.setter
    def M00(self, value): ...
    @property
    def M10(self): ...
    @M10.setter
    def M10(self, value): ...
    @property
    def M20(self): ...
    @M20.setter
    def M20(self, value): ...
    @property
    def M30(self): ...
    @M30.setter
    def M30(self, value): ...
    @property
    def M01(self): ...
    @M01.setter
    def M01(self, value): ...
    @property
    def M11(self): ...
    @M11.setter
    def M11(self, value): ...
    @property
    def M21(self): ...
    @M21.setter
    def M21(self, value): ...
    @property
    def M31(self): ...
    @M31.setter
    def M31(self, value): ...
    @property
    def M02(self): ...
    @M02.setter
    def M02(self, value): ...
    @property
    def M12(self): ...
    @M12.setter
    def M12(self, value): ...
    @property
    def M22(self): ...
    @M22.setter
    def M22(self, value): ...
    @property
    def M32(self): ...
    @M32.setter
    def M32(self, value): ...
    @property
    def M03(self): ...
    @M03.setter
    def M03(self, value): ...
    @property
    def M13(self): ...
    @M13.setter
    def M13(self, value): ...
    @property
    def M23(self): ...
    @M23.setter
    def M23(self, value): ...
    @property
    def M33(self): ...
    @M33.setter
    def M33(self, value): ...
