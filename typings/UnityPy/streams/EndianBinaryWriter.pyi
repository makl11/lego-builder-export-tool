"""
This type stub file was generated by pyright.
"""

import io
from ..math import Color, Matrix4x4, Quaternion, Rectangle, Vector2, Vector3, Vector4

class EndianBinaryWriter:
    endian: str
    Length: int
    Position: int
    stream: io.BufferedReader
    def __init__(self, input_=..., endian=...) -> None: ...
    @property
    def bytes(self): ...
    @property
    def Length(self) -> int: ...
    def dispose(self): ...
    def write(self, *args): ...
    def write_byte(self, value: int): ...
    def write_u_byte(self, value: int): ...
    def write_bytes(self, value: bytes): ...
    def write_short(self, value: int): ...
    def write_int(self, value: int): ...
    def write_long(self, value: int): ...
    def write_u_short(self, value: int): ...
    def write_u_int(self, value: int): ...
    def write_u_long(self, value: int): ...
    def write_float(self, value: float): ...
    def write_double(self, value: float): ...
    def write_boolean(self, value: bool): ...
    def write_string_to_null(self, value: str): ...
    def write_aligned_string(self, value: str): ...
    def align_stream(self, alignment=...): ...
    def write_quaternion(self, value: Quaternion): ...
    def write_vector2(self, value: Vector2): ...
    def write_vector3(self, value: Vector3): ...
    def write_vector4(self, value: Vector4): ...
    def write_rectangle_f(self, value: Rectangle): ...
    def write_color4(self, value: Color): ...
    def write_matrix(self, value: Matrix4x4): ...
    def write_array(self, command, value: list, write_length: bool = ...): ...
    def write_byte_array(self, value: bytes): ...
    def write_boolean_array(self, value: list): ...
    def write_u_short_array(self, value: list): ...
    def write_int_array(self, value: list, write_length: bool = ...): ...
    def write_u_int_array(self, value: list, write_length: bool = ...): ...
    def write_float_array(self, value: list, write_length: bool = ...): ...
    def write_string_array(self, value: list): ...
    def write_vector2_array(self, value: list): ...
    def write_vector4_array(self, value: list): ...
    def write_matrix_array(self, value: list): ...