"""
This type stub file was generated by pyright.
"""

from . import File
from ..enums import BuildTarget
from ..streams import EndianBinaryReader, EndianBinaryWriter

class SerializedFileHeader:
    metadata_size: int
    file_size: int
    version: int
    data_offset: int
    endian: bytes
    reserved: bytes
    def __init__(self, reader: EndianBinaryReader) -> None: ...

class LocalSerializedObjectIdentifier:
    local_serialized_file_index: int
    local_identifier_in_file: int
    def __init__(
        self, header: SerializedFileHeader, reader: EndianBinaryReader
    ) -> None: ...
    def write(self, header: SerializedFileHeader, writer: EndianBinaryWriter): ...

class FileIdentifier:
    guid: bytes
    type: int
    path: str
    @property
    def name(self): ...
    def __repr__(self): ...
    def __init__(
        self, header: SerializedFileHeader, reader: EndianBinaryReader
    ) -> None: ...
    def write(self, header: SerializedFileHeader, writer: EndianBinaryWriter): ...

class BuildType:
    build_type: str
    def __init__(self, build_type) -> None: ...
    @property
    def IsAlpha(self): ...
    @property
    def IsPatch(self): ...

class SerializedType:
    class_id: int
    is_stripped_type: bool
    script_type_index = ...
    nodes: list = ...
    script_id: bytes
    old_type_hash: bytes
    def __init__(self, reader, serialized_file, is_ref_type: bool) -> None: ...
    def write(self, serialized_file, writer, is_ref_type): ...

class SerializedFile(File.File):
    reader: EndianBinaryReader
    is_changed: bool
    unity_version: str
    version: tuple
    build_type: BuildType
    target_platform: BuildTarget
    types: list
    script_types: list
    externals: list
    _container: dict
    objects: dict
    container_: dict
    _cache: dict
    header: SerializedFileHeader
    @property
    def files(self): ...
    @files.setter
    def files(self, value): ...
    def __init__(self, reader: EndianBinaryReader, parent=..., name=...) -> None: ...
    @property
    def container(self): ...
    def set_version(self, string_version): ...
    def read_type_tree(self): ...
    def read_type_tree_blob(self): ...
    def get_writeable_cab(self, name: str = ...):  # -> None:
        """
        Creates a new cab file in the bundle that contains the given data.
        This is usefull for asset types that use resource files.
        """
        ...
    def save(self, packer: str = ...) -> bytes: ...
    def save_serialized_type(
        self,
        typ: SerializedType,
        header: SerializedFileHeader,
        writer: EndianBinaryWriter,
    ): ...
    def save_type_tree(self, nodes: list, writer: EndianBinaryWriter): ...
    def save_type_tree5(
        self, nodes: list, writer: EndianBinaryWriter, str_data=...
    ): ...

def read_string(string_buffer_reader: EndianBinaryReader, value: int) -> str: ...
