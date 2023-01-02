"""
This type stub file was generated by pyright.
"""

from typing import Tuple
from . import File
from ..enums import ArchiveFlags, ArchiveFlagsOld
from ..helpers import ArchiveStorageManager
from ..streams import EndianBinaryReader, EndianBinaryWriter

BlockInfo = ...
DirectoryInfoFS = ...
reVersion = ...

class BundleFile(File.File):
    format: int
    is_changed: bool
    signature: str
    version_engine: str
    version_player: str
    dataflags: Tuple[ArchiveFlags, ArchiveFlagsOld]
    decryptor: ArchiveStorageManager.ArchiveStorageDecryptor = ...
    def __init__(
        self, reader: EndianBinaryReader, parent: File, name: str = ...
    ) -> None: ...
    def read_web_raw(self, reader: EndianBinaryReader): ...
    def read_fs(self, reader: EndianBinaryReader): ...
    def save(self, packer=...):  # -> bytes:
        """
        Rewrites the BundleFile and returns it as bytes object.

        packer:
            can be either one of the following strings
            or tuple consisting of (block_info_flag, data_flag)
            allowed strings:
                none - no compression, default, safest bet
                lz4 - lz4 compression
                original - uses the original flags
        """
        ...
    def save_fs(
        self, writer: EndianBinaryWriter, data_flag: int, block_info_flag: int
    ): ...
    def decompress_data(
        self,
        compressed_data: bytes,
        uncompressed_size: int,
        flags: int,
        index: int = ...,
    ) -> bytes:
        """
        Parameters
        ----------
        compressed_data : bytes
            The compressed data.
        uncompressed_size : int
            The uncompressed size of the data.
        flags : int
            The flags of the data.

        Returns
        -------
        bytes
            The decompressed data."""
        ...
    def get_version_tuple(self) -> Tuple[int, int, int]:
        """Returns the version as a tuple."""
        ...