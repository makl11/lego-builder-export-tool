"""
This type stub file was generated by pyright.
"""

def get_resource_data(*args):
    """
    Input:
    Option 1:
        0 - path - file path
        1 - assets_file - SerializedFile
        2 - offset -
        3 - size -
    Option 2:
        0 - reader - EndianBinaryReader
        1 - offset -
        2 - size -

    -> -2 = offset, -1 = size
    """
    ...

def search_resource(res_path, assets_file): ...
def search_resource_file(path, name): ...
