"""
This type stub file was generated by pyright.
"""

from .EditorExtension import EditorExtension
from ..streams import EndianBinaryReader, EndianBinaryWriter

class Component(EditorExtension):
    def __init__(self, reader: EndianBinaryReader) -> None: ...
    def save(self, writer: EndianBinaryWriter = ...): ...
