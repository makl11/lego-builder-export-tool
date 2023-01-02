"""
This type stub file was generated by pyright.
"""

from typing import List
from . import Component, PPtr
from ..math import Vector3, Quaternion

class Transform(Component):
    m_LocalRotation: Quaternion
    m_LocalPosition: Vector3
    m_LocalScale: Vector3
    m_Children: List[PPtr[Transform]]
    m_Father: PPtr[Transform]
    def __init__(self, reader) -> None: ...