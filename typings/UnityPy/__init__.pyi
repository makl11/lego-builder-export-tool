"""
This type stub file was generated by pyright.
"""

from .environment import Environment
from .helpers.ArchiveStorageManager import set_assetbundle_decrypt_key

__version__: int = ...

def load(*args) -> Environment: ...

AssetsManager = Environment