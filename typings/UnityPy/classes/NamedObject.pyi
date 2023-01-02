"""
This type stub file was generated by pyright.
"""

from .EditorExtension import EditorExtension
from ..streams import EndianBinaryWriter

class NamedObject(EditorExtension):
    m_Name: str
    def __init__(self, reader) -> None: ...
    def save(self, writer: EndianBinaryWriter = ...): ...
    @property
    def name(self): ...
    @name.setter
    def name(self, value): ...
    def __repr__(self): ...