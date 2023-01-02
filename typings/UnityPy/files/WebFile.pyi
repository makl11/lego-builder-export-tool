"""
This type stub file was generated by pyright.
"""

from . import File
from ..streams import EndianBinaryReader

class WebFile(File.File):
    """A package which can hold other WebFiles, Bundles and SerialiedFiles.
    It may be compressed via gzip or brotli.

    files -- list of all files in the WebFile
    """

    def __init__(self, reader: EndianBinaryReader, parent: File, name=...) -> None:
        """Constructor Method"""
        ...
    def save(
        self, files: dict = ..., packer: str = ..., signature: str = ...
    ) -> bytes: ...
