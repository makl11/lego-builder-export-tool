from dataclasses import astuple
from typing import Dict, List, Tuple

from pygltflib import GLTF2, Attributes
from pygltflib import Mesh as GLTFMesh
from pygltflib import Node, Primitive, Scene

from typings import GOWithChildren
from .util import get_trans

from UnityPy.classes import (
    GameObject,
    Material,
    Mesh,
    MeshFilter,
    MeshRenderer,
    SkinnedMeshRenderer,
    Transform,
)
from UnityPy.classes.Object import NodeHelper
from UnityPy.enums import GfxPrimitiveType
from UnityPy.math import Color, Vector2, Vector3, Vector4

_root = GLTF2()
_primOwner: Dict[Tuple[Mesh, Material], int]
_meshToPrims: Dict[Mesh, List[Primitive]]


def FilterPrimitives(gameobject: GameObject):
    def ContainsValidRenderer(gameobj: GameObject):
        return (
            gameobj.m_MeshFilter is not None and gameobj.m_MeshRenderer is not None
        ) or gameobj.m_SkinnedMeshRenderer is not None

    def isPrimitive(gameobj: GameObject):
        trans = get_trans(gameobj)
        noChildren = len(trans.m_Children) == 0
        noTranslation = trans.m_LocalPosition == Vector3.Zero()
        r = trans.m_LocalRotation
        noRotation = r.X == 0 and r.Y == 0 and r.Z == 0 and r.W == 1
        noScaling = trans.m_LocalScale == Vector3.One()

        return (
            noChildren
            and noTranslation
            and noRotation
            and noScaling
            and ContainsValidRenderer(gameobj)
        )

    primitives: List[GameObject] = list()
    nonPrimitives: List[GameObject] = list()

    if ContainsValidRenderer(gameobject):
        primitives.append(gameobject)

    child: GameObject
    for child in GOWithChildren(gameobject).child_objects:
        if isPrimitive(child):
            primitives.append(child)
        else:
            nonPrimitives.append(child)

    return primitives, nonPrimitives


def ExportScene(gameobject: GameObject):
    scene = Scene(name=gameobject.name)
    scene.nodes = list()
    scene.nodes.append(ExportNode(gameobject))
    _root.scenes.append(scene)
    return len(_root.scenes) - 1


def Node_SetUnityTransform(node: Node, unity_transform: Transform):
    node.translation = list(astuple(unity_transform.m_LocalPosition))
    node.scale = list(astuple(unity_transform.m_LocalScale))
    node.rotation = list(astuple(unity_transform.m_LocalRotation))


def ExportNode(gameobject: GameObject):
    node = Node(name=gameobject.name)
    Node_SetUnityTransform(node, get_trans(gameobject))
    _root.nodes.append(node)
    prims, nonPrims = FilterPrimitives(gameobject)

    if len(prims) > 0:
        node.mesh = ExportMesh(gameobject.name, prims)

        for p in prims:
            if p.m_SkinnedMeshRenderer is not None:
                smr = p.m_SkinnedMeshRenderer.get_obj().read()
                if not isinstance(smr, SkinnedMeshRenderer):
                    raise RuntimeError("smr is not a SkinnedMeshRenderer")
                mesh = smr.m_Mesh.get_obj().read()
                if not isinstance(mesh, Mesh):
                    raise RuntimeError("mesh is not a Mesh")
                material = smr.m_Materials[0].get_obj().read()
                if not isinstance(material, Material):
                    raise RuntimeError("material is not a Material")
                _primOwner[(mesh, material)] = node.mesh
            elif p.m_MeshFilter and p.m_MeshRenderer:
                meshFilter = p.m_MeshFilter.get_obj().read()
                if not isinstance(meshFilter, MeshFilter):
                    raise RuntimeError("meshFilter is not a MeshFilter")
                mesh = meshFilter.m_Mesh.get_obj().read()
                if not isinstance(mesh, Mesh):
                    raise RuntimeError("mesh is not a Mesh")
                meshRenderer = p.m_MeshRenderer.get_obj().read()
                if not isinstance(meshRenderer, MeshRenderer):
                    raise RuntimeError("meshRenderer is not a MeshRenderer")
                material = meshRenderer.m_Materials[0].get_obj().read()
                if not isinstance(material, Material):
                    raise RuntimeError("material is not a Material")
                _primOwner[(mesh, material)] = node.mesh
    if len(nonPrims) > 0:
        node.children = list()
        [node.children.append(ExportNode(np)) for np in nonPrims]

    return len(_root.nodes) - 1


def ExportMesh(name: str, primitives: List[GameObject]):
    # TODO: check cache for existing mesh
    mesh = GLTFMesh(name=name)
    mesh.primitives = sum([ExportPrimitive(p, mesh) for p in primitives], [])
    _root.meshes.append(mesh)
    return len(_root.meshes) - 1


def ExportPrimitive(prim: GameObject, mesh: GLTFMesh) -> List[Primitive]:
    meshobj: Mesh | NodeHelper | None
    materialsObj: List[Material | NodeHelper | None] = list()
    smr: SkinnedMeshRenderer | None = None
    if prim.m_SkinnedMeshRenderer:
        _smr = prim.m_SkinnedMeshRenderer.get_obj().read()
        if not isinstance(_smr, SkinnedMeshRenderer):
            raise RuntimeError("smr is not a SkinnedMeshRenderer")
        smr = _smr
        meshobj = smr.m_Mesh.get_obj().read()
        materialsObj.extend([m.get_obj().read() for m in smr.m_Materials])
    elif prim.m_MeshFilter and prim.m_MeshRenderer:
        meshFilter = prim.m_MeshFilter.get_obj().read()
        if not isinstance(meshFilter, MeshFilter):
            raise RuntimeError("meshFilter is not a MeshFilter")
        meshobj = meshFilter.m_Mesh.get_obj().read()
        meshRenderer = prim.m_MeshRenderer.get_obj().read()
        if not isinstance(meshRenderer, MeshRenderer):
            raise RuntimeError("meshRenderer is not a MeshRenderer")
        materialsObj.extend([m.get_obj().read() for m in meshRenderer.m_Materials])
    else:
        raise RuntimeError("Primitive does not contain a mesh")

    if not isinstance(meshobj, Mesh):
        raise RuntimeError("mesh is not a Mesh")

    materials = [m for m in materialsObj if isinstance(m, Material)]

    prims: List[Primitive] = list()

    if _meshToPrims[meshobj] and len(_meshToPrims[meshobj]) == len(meshobj.m_SubMeshes):
        for i in range(len(meshobj.m_SubMeshes)):
            newPrim = _meshToPrims[meshobj][i]
            newPrim.material = ExportMaterial(materials[i])
            prims[i] = newPrim
        return prims

    aPosition = ExportAccessor_vec3(meshobj.m_Vertices)
    aNormal = ExportAccessor_vec3(meshobj.m_Normals)
    aTangent = ExportAccessor_vec4(meshobj.m_Tangents)
    aTexcoord0 = ExportAccessor_vec2(meshobj.m_UV0)
    aTexcoord1 = ExportAccessor_vec2(meshobj.m_UV2)
    aColor0 = ExportAccessor_color(meshobj.m_Colors)

    lastMaterialId: int | None = None

    for i in range(len(meshobj.m_SubMeshes)):
        submesh = meshobj.m_SubMeshes[i]
        p = Primitive()
        topology = submesh.topology
        indices = list((0, 0, 0, 0))  # TODO: find out how to get indices from UnityPy SubMesh
        if topology == GfxPrimitiveType.kPrimitiveTriangles:
            pass  # TODO: flip triangles
        p.mode = GetDrawMode(topology)
        p.indices = ExportAccessor_int(indices, True)

        p.attributes = Attributes(
            aPosition, aNormal, aTangent, aTexcoord0, aTexcoord1, aColor0
        )

        if i < len(materialsObj):
            p.material = ExportMaterial(materials[i])
            lastMaterialId = p.material
        elif lastMaterialId != None:
            p.material = lastMaterialId
        else:
            assert False and "This should be unreachable"

        if smr:
            # Only needed for SkinnedMeshRenderer
            ExportBlendShapes(smr, meshobj, p, mesh)

        prims[i] = p

    _meshToPrims[meshobj] = prims

    return prims


def ExportMaterial(material: Material) -> int:
    raise NotImplementedError()


# ExportAccessor(int[] arr, bool isIndices = false)
def ExportAccessor_int(values: List[int], isIndices: bool = False) -> int:
    raise NotImplementedError()


# ExportAccessor(Vector2[] arr)
def ExportAccessor_vec2(values: List[Vector2]) -> int:
    raise NotImplementedError()


# ExportAccessor(Vector3[] arr)
def ExportAccessor_vec3(values: List[Vector3]) -> int:
    raise NotImplementedError()


# ExportAccessor(Vector4[] arr)
def ExportAccessor_vec4(values: List[Vector4]) -> int:
    raise NotImplementedError()


# ExportAccessor(Color[] arr)
def ExportAccessor_color(values: List[Color]) -> int:
    raise NotImplementedError()


def GetDrawMode(topology: GfxPrimitiveType) -> int:
    match (topology):
        case GfxPrimitiveType.kPrimitivePoints:
            return 0  # DrawMode.Points;
        case GfxPrimitiveType.kPrimitiveLines:
            return 1  # DrawMode.Lines;
        case GfxPrimitiveType.kPrimitiveLineStrip:
            return 3  # DrawMode.LineStrip;
        case GfxPrimitiveType.kPrimitiveTriangles:
            return 4  # DrawMode.Triangles;
        case _:
            raise RuntimeError("glTF does not support Unity mesh topology: ", topology)


def ExportBlendShapes(
    smr: SkinnedMeshRenderer, meshObj: Mesh, primitive: Primitive, mesh: GLTFMesh
):
    raise NotImplementedError()
