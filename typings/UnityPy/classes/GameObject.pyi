"""
This type stub file was generated by pyright.
"""

from . import (
    Animation,
    Animator,
    MeshFilter,
    MeshRenderer,
    SkinnedMeshRenderer,
    Transform,
)
from .EditorExtension import EditorExtension
from .PPtr import PPtr

class GameObject(EditorExtension):
    m_Components: list
    m_Layer: int
    name: str
    m_Animator: PPtr[Animator] | None
    m_Animation: PPtr[Animation] | None
    m_Transform: PPtr[Transform] | None
    m_MeshRenderer: PPtr[MeshRenderer] | None
    m_SkinnedMeshRenderer: PPtr[SkinnedMeshRenderer] | None
    m_MeshFilter: PPtr[MeshFilter] | None
    def __init__(self, reader) -> None: ...