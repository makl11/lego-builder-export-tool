"""
This type stub file was generated by pyright.
"""

from enum import IntEnum
from .NamedObject import NamedObject

class Shader(NamedObject):
    def export(self): ...
    def __init__(self, reader) -> None: ...

class StructParameter:
    def __init__(self, reader) -> None: ...

class SamplerParameter:
    def __init__(self, reader) -> None: ...

class SerializedTextureProperty:
    def __init__(self, reader) -> None: ...

class SerializedProperty:
    def __init__(self, reader) -> None: ...

class SerializedProperties:
    def __init__(self, reader) -> None: ...

class SerializedShaderFloatValue:
    def __init__(self, reader) -> None: ...

class SerializedShaderRTBlendState:
    def __init__(self, reader) -> None: ...

class SerializedStencilOp:
    def __init__(self, reader) -> None: ...

class SerializedShaderVectorValue:
    def __init__(self, reader) -> None: ...

class FogMode(IntEnum):
    kFogUnknown = ...
    kFogDisabled = ...
    kFogLinear = ...
    kFogExp = ...
    kFogExp2 = ...

class SerializedShaderState:
    def __init__(self, reader) -> None: ...

class ShaderBindChannel:
    def __init__(self, reader) -> None: ...

class ParserBindChannels:
    def __init__(self, reader) -> None: ...

class VectorParameter:
    def __init__(self, reader) -> None: ...

class MatrixParameter:
    def __init__(self, reader) -> None: ...

class TextureParameter:
    def __init__(self, reader) -> None: ...

class BufferBinding:
    def __init__(self, reader) -> None: ...

class ConstantBuffer:
    def __init__(self, reader) -> None: ...

class UAVParameter:
    def __init__(self, reader) -> None: ...

class SerializedProgramParameters:
    def __init__(self, reader) -> None: ...

class SerializedSubProgram:
    def __init__(self, reader) -> None: ...

class SerializedProgram:
    def __init__(self, reader) -> None: ...

class SerializedPass:
    def __init__(self, reader) -> None: ...

class SerializedTagMap:
    def __init__(self, reader) -> None: ...

class SerializedSubShader:
    def __init__(self, reader) -> None: ...

class SerializedShaderDependency:
    def __init__(self, reader) -> None: ...

class SerializedCustomEditorForRenderPipeline:
    def __init__(self, reader) -> None: ...

class SerializedShader:
    def __init__(self, reader) -> None: ...