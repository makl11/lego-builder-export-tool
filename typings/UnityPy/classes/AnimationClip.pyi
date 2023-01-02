"""
This type stub file was generated by pyright.
"""

from enum import IntEnum
from typing import List
from .NamedObject import NamedObject

def uint(num): ...

class Keyframe:
    def __init__(self, reader, readerFunc) -> None: ...

class AnimationCurve:
    def __init__(self, reader, readerFunc) -> None: ...

class QuaternionCurve:
    def __init__(self, reader) -> None: ...

class PackedFloatVector:
    def __init__(self, reader) -> None: ...
    def save(self, writer): ...
    def UnpackFloats(
        self,
        itemCountInChunk: int,
        chunkStride: int,
        start: int = ...,
        numChunks: int = ...,
    ) -> List[float]: ...

class PackedIntVector:
    def __init__(self, reader) -> None: ...
    def save(self, writer): ...
    def UnpackInts(self): ...

class PackedQuatVector:
    def __init__(self, reader) -> None: ...
    def UnpackQuats(self): ...

class CompressedAnimationCurve:
    def __init__(self, reader) -> None: ...

class Vector3Curve:
    def __init__(self, reader) -> None: ...

class FloatCurve:
    def __init__(self, reader) -> None: ...

class PPtrKeyframe:
    def __init__(self, reader) -> None: ...

class PPtrCurve:
    def __init__(self, reader) -> None: ...

class AABB:
    def __init__(self, reader) -> None: ...
    def save(self, writer): ...

class xform:
    def __init__(self, reader) -> None: ...

class HandPose:
    def __init__(self, reader) -> None: ...

class HumanGoal:
    def __init__(self, reader) -> None: ...

class HumanPose:
    def __init__(self, reader) -> None: ...

class StreamedCurveKey:
    def __init__(self, reader) -> None: ...
    def CalculateNextInSlope(self, dx: float, rhs):  # -> float:
        """
        :param dx: float
        :param rhs: StreamedCurvedKey
        :return:
        """
        ...

class StreamedFrame:
    def __init__(self, reader) -> None: ...

class StreamedClip:
    def __init__(self, reader) -> None: ...
    def ReadData(self): ...

class DenseClip:
    def __init__(self, reader) -> None: ...

class ConstantClip:
    def __init__(self, reader) -> None: ...

class ValueConstant:
    def __init__(self, reader) -> None: ...

class ValueArrayConstant:
    def __init__(self, reader) -> None: ...

class Clip:
    def __init__(self, reader) -> None: ...

class ValueDelta:
    def __init__(self, reader) -> None: ...

class ClipMuscleConstant:
    def __init__(self, reader) -> None: ...

class GenericBinding:
    def __init__(self, reader) -> None: ...

class AnimationClipBindingConstant:
    def __init__(self, reader) -> None: ...
    def FindBinding(self, index): ...

class AnimationType(IntEnum):
    kLegacy = ...
    kGeneric = ...
    kHumanoid = ...

class AnimationClip(NamedObject):
    def __init__(self, reader) -> None: ...