"""
This type stub file was generated by pyright.
"""

from .NamedObject import NamedObject
from ..streams import EndianBinaryReader, EndianBinaryWriter

class Sprite(NamedObject):
    @property
    def image(self): ...
    def __init__(self, reader) -> None: ...
    def save(self, writer: EndianBinaryWriter = ...): ...

class SecondarySpriteTexture:
    def __init__(self, reader) -> None: ...
    def save(self, writer): ...

class SpriteSettings:
    def __init__(self, reader) -> None: ...
    def save(self, writer): ...

class SpriteVertex:
    def __init__(self, reader) -> None: ...
    def save(self, writer, version): ...

class SpriteRenderData:
    def __init__(self, reader) -> None: ...
    def save(self, writer, version): ...

class SpriteBone:
    name: str
    position: tuple
    rotation: tuple
    length: float
    parentId: int
    def __init__(self, reader: EndianBinaryReader) -> None: ...
    def save(self, writer: EndianBinaryWriter): ...