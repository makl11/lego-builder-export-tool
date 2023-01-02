"""
This type stub file was generated by pyright.
"""

from .Texture import Texture
from ..enums import TextureFormat
from ..streams import EndianBinaryWriter

class Texture2D(Texture):
    m_Width: int
    m_Height: int
    @property
    def image(self): ...
    @image.setter
    def image(self, img): ...
    @property
    def image_data(self): ...
    def reset_streamdata(self): ...
    @image_data.setter
    def image_data(self, data: bytes): ...
    def set_image(
        self,
        img,
        target_format: TextureFormat = ...,
        in_cab: bool = ...,
        mipmap_count: int = ...,
    ): ...
    def __init__(self, reader) -> None: ...
    def save(self, writer: EndianBinaryWriter = ...): ...

class StreamingInfo:
    offset: int
    size: int
    path: str
    def __init__(self, reader, version) -> None: ...
    def save(self, writer, version): ...

class GLTextureSettings:
    m_FilterMode: int
    m_WrapMode: int
    def __init__(self, reader, version) -> None: ...
    def save(self, writer, version): ...
