import os
from dataclasses import astuple, dataclass
from enum import IntEnum, auto
from typing import Dict, List, Tuple

from pygltflib import FLOAT as ComponentTypeFloat
from pygltflib import GLTF2
from pygltflib import SCALAR as AccessorTypeScalar
from pygltflib import UNSIGNED_INT as ComponentTypeUInt
from pygltflib import VEC2 as AccessorTypeVec2
from pygltflib import VEC3 as AccessorTypeVec3
from pygltflib import VEC4 as AccessorTypeVec4
from pygltflib import Accessor, Asset, Attributes, Buffer
from pygltflib import Mesh as GLTFMesh
from pygltflib import Node
from pygltflib import NormalMaterialTexture as NormalTextureInfo
from pygltflib import (
    OcclusionTextureInfo,
    PbrMetallicRoughness,
    Primitive,
    Scene,
    TextureInfo,
)

from typings import GOWithChildren
from UnityPy.classes import (
    GameObject,
    Material,
    Mesh,
    MeshFilter,
    MeshRenderer,
    SkinnedMeshRenderer,
    Texture,
    Texture2D,
)
from UnityPy.classes.Mesh import SubMesh
from UnityPy.classes.Object import NodeHelper
from UnityPy.enums import GfxPrimitiveType
from UnityPy.math import Color, Vector2, Vector3, Vector4

from .util import get_transform


class TextureMapType(IntEnum):
    Main = 0
    Bump = auto()
    SpecGloss = auto()
    Emission = auto()
    MetallicGloss = auto()
    Light = auto()
    Occlusion = auto()


class UnityGLTFExporter:
    @dataclass
    class ImageInfo:
        texture: Texture2D
        textureMapType: TextureMapType

    _rootGameObject: GameObject
    _root: GLTF2
    _bufferId: int
    _buffer: Buffer
    _imageInfos: List[ImageInfo]
    _textures: List[Texture]
    _materials: List[Material]
    _shouldUseInternalBufferForImages: bool

    _metalGlossChannelSwapMaterial: Material
    _normalChannelMaterial: Material

    MagicGLTF = 0x46546C67
    Version = 2
    MagicJson = 0x4E4F534A
    MagicBin = 0x004E4942
    GLTFHeaderSize = 12
    SectionHeaderSize = 8

    _primOwner: Dict[Tuple[Mesh, Material], int]
    _meshToPrims: Dict[Mesh, List[Primitive]]

    def __init__(self, gameObject: GameObject):
        # TODO : self._metalGlossChannelSwapMaterial
        # TODO : self._normalChannelMaterial
        self._rootGameObject = gameObject
        self._root = GLTF2(asset=Asset(version="2.0"))
        self._imageInfos = list()
        self._materials = list()
        self._textures = list()
        self._buffer = Buffer()
        self._root.buffers.append(self._buffer)
        self._bufferId = len(self._root.buffers) - 1

    def SaveGLTFandBin(self, path: str, fileName: str):
        self._shouldUseInternalBufferForImages = False
        self._root.scene = self.ExportScene(self._rootGameObject)
        # TODO: Buffer stuff
        self._root.save_json(os.path.join(path, fileName, ".json"))  # type: ignore
        self.ExportImages(path)

    def ExportImages(self, outputPath: str):
        for imgInfo in self._imageInfos:
            match (imgInfo.textureMapType):
                case TextureMapType.MetallicGloss:
                    self.ExportMetallicGlossTexture(imgInfo.texture, outputPath)
                    break
                case TextureMapType.Bump:
                    self.ExportNormalTexture(imgInfo.texture, outputPath)
                    break
                case _:
                    self.ExportTexture(imgInfo.texture, outputPath)
                    break

    def ExportMetallicGlossTexture(self, texture: Texture2D, outpath: str) -> None:
        raise NotImplementedError()

    def ExportNormalTexture(self, texture: Texture2D, outpath: str) -> None:
        raise NotImplementedError()

    def ExportTexture(self, texture: Texture2D, outpath: str) -> None:
        raise NotImplementedError()

    def ConstructImageFilenamePath(self, texture: Texture2D, outpath: str) -> str:
        raise NotImplementedError()

    def ExportScene(self, gameobject: GameObject):
        scene = Scene(name=gameobject.name)
        scene.nodes = list()
        scene.nodes.append(self.ExportNode(gameobject))
        self._root.scenes.append(scene)
        return len(self._root.scenes) - 1

    def ExportNode(self, gameobject: GameObject):
        node = Node(name=gameobject.name)
        transform = get_transform(gameobject)
        node.translation = list(astuple(transform.m_LocalPosition))
        node.scale = list(astuple(transform.m_LocalScale))
        node.rotation = list(astuple(transform.m_LocalRotation))

        self._root.nodes.append(node)
        prims, nonPrims = self.FilterPrimitives(gameobject)

        if len(prims) > 0:
            node.mesh = self.ExportMesh(gameobject.name, prims)

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
                    self._primOwner[(mesh, material)] = node.mesh
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
                    self._primOwner[(mesh, material)] = node.mesh
        if len(nonPrims) > 0:
            node.children = list()
            [node.children.append(self.ExportNode(np)) for np in nonPrims]

        return len(self._root.nodes) - 1

    def ContainsValidRenderer(self, gameobj: GameObject):
        return (
            gameobj.m_MeshFilter is not None and gameobj.m_MeshRenderer is not None
        ) or gameobj.m_SkinnedMeshRenderer is not None

    def FilterPrimitives(self, gameobject: GameObject):
        primitives: List[GameObject] = list()
        nonPrimitives: List[GameObject] = list()

        if self.ContainsValidRenderer(gameobject):
            primitives.append(gameobject)

        child: GameObject
        for child in GOWithChildren(gameobject).child_objects:
            if self.isPrimitive(child):
                primitives.append(child)
            else:
                nonPrimitives.append(child)

        return primitives, nonPrimitives

    def isPrimitive(self, gameobj: GameObject):
        transform = get_transform(gameobj)
        noChildren = len(transform.m_Children) == 0
        noTranslation = transform.m_LocalPosition == Vector3.Zero()
        r = transform.m_LocalRotation
        noRotation = r.X == 0 and r.Y == 0 and r.Z == 0 and r.W == 1
        noScaling = transform.m_LocalScale == Vector3.One()

        return (
            noChildren
            and noTranslation
            and noRotation
            and noScaling
            and self.ContainsValidRenderer(gameobj)
        )

    def ExportMesh(self, name: str, primitives: List[GameObject]):
        # TODO: check cache for existing mesh
        mesh = GLTFMesh(name=name)
        mesh.primitives = sum([self.ExportPrimitive(p, mesh) for p in primitives], [])
        self._root.meshes.append(mesh)
        return len(self._root.meshes) - 1

    def ExportPrimitive(self, prim: GameObject, mesh: GLTFMesh) -> List[Primitive]:
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

        if self._meshToPrims[meshobj] and len(self._meshToPrims[meshobj]) == len(
            meshobj.m_SubMeshes
        ):
            for i in range(len(meshobj.m_SubMeshes)):
                newPrim = self._meshToPrims[meshobj][i]
                newPrim.material = self.ExportMaterial(materials[i])
                prims[i] = newPrim
            return prims

        aPosition = self.ExportAccessor_vec3(meshobj.m_Vertices)
        aNormal = self.ExportAccessor_vec3(meshobj.m_Normals)
        aTangent = self.ExportAccessor_vec4(meshobj.m_Tangents)
        aTexcoord0 = self.ExportAccessor_vec2(meshobj.m_UV0)
        aTexcoord1 = self.ExportAccessor_vec2(meshobj.m_UV2)
        aColor0 = self.ExportAccessor_color(meshobj.m_Colors)

        lastMaterialId: int | None = None

        for i, submesh in enumerate(meshobj.m_SubMeshes):
            p = Primitive()
            topology = submesh.topology
            indices = self.Mesh_GetIndices(meshobj, submesh)
            if topology == GfxPrimitiveType.kPrimitiveTriangles:
                self.FlipTriangleFaces(indices)
            p.mode = self.GetDrawMode(topology)
            p.indices = self.ExportAccessor_int(indices, True)

            p.attributes = Attributes(
                aPosition, aNormal, aTangent, aTexcoord0, aTexcoord1, aColor0
            )

            if i < len(materialsObj):
                p.material = self.ExportMaterial(materials[i])
                lastMaterialId = p.material
            elif lastMaterialId != None:
                p.material = lastMaterialId
            else:
                assert False and "This should be unreachable"

            if smr:
                # Only needed for SkinnedMeshRenderer
                self.ExportBlendShapes(smr, meshobj, p, mesh)

            prims[i] = p

        self._meshToPrims[meshobj] = prims

        return prims

    def ExportMaterial(self, material: Material) -> int:
        raise NotImplementedError()

    def ExportBlendShapes(
        self,
        smr: SkinnedMeshRenderer,
        meshObj: Mesh,
        primitive: Primitive,
        mesh: GLTFMesh,
    ):
        raise NotImplementedError()

    # TODO: Implememt all these methods
    def IsPBRMetallicRoughness(self, material: Material) -> bool:
        raise NotImplementedError()

    def IsCommonConstant(self, material: Material) -> bool:
        raise NotImplementedError()

    def ExportTextureTransform(
        self, info: TextureInfo, mat: Material, texName: str
    ) -> None:
        raise NotImplementedError()

    def ExportNormalTextureInfo(
        self, texture: Texture, textureMapType: TextureMapType, material: Material
    ) -> NormalTextureInfo:
        raise NotImplementedError()

    def ExportOcclusionTextureInfo(
        self, texture: Texture, textureMapType: TextureMapType, material: Material
    ) -> OcclusionTextureInfo:
        raise NotImplementedError()

    def ExportPBRMetallicRoughness(self, material: Material) -> PbrMetallicRoughness:
        raise NotImplementedError()

    def ExportCommonConstant(self, materialObj: Material) -> MaterialCommonConstant:
        raise NotImplementedError()

    def ExportTextureInfo(
        self, texture: Texture, textureMapType: TextureMapType
    ) -> TextureInfo:
        raise NotImplementedError()

    def ExportTexture(self, textureObj: Texture, textureMapType: TextureMapType) -> int:
        raise NotImplementedError()

    def ExportImage(self, texture: Texture, texturMapType: TextureMapType) -> int:
        raise NotImplementedError()

    def ExportImageInternalBuffer(
        self, texture: Texture, texturMapType: TextureMapType
    ) -> int:
        raise NotImplementedError()

    def ExportSampler(self, texture: Texture) -> int:
        raise NotImplementedError()

    def ExportAccessor_int(self, values: List[int], isIndices: bool = False) -> int:
        count = len(values)
        if count is 0:
            raise RuntimeError("Accessors can not have a count of 0.")
        accessor = Accessor(count=count, type=AccessorTypeScalar)

        min: float = values[0]
        max: float = values[0]

        for cur in values:
            if cur < min:
                min = cur
            if cur > max:
                max = cur

        accessor.min = list({min})
        accessor.max = list({max})

        # TODO: Buffer stuff
        accessor.componentType = ComponentTypeUInt  # PLACEHOLDER

        self._root.accessors.append(accessor)

        return len(self._root.accessors) - 1

    def AppendToBufferMultiplyOf4(self, byteOffset: int, byteLength: int) -> int:
        raise NotImplementedError()

    def ExportAccessor_vec2(self, values: List[Vector2]) -> int:
        count = len(values)
        if count is 0:
            raise RuntimeError("Accessors can not have a count of 0.")
        accessor = Accessor(
            componentType=ComponentTypeFloat, count=count, type=AccessorTypeVec2
        )

        minX: float = values[0].X
        minY: float = values[0].Y
        maxX: float = values[0].X
        maxY: float = values[0].Y

        for cur in values:
            if cur.X < minX:
                minX = cur.X
            if cur.Y < minY:
                minY = cur.Y
            if cur.X > maxX:
                maxX = cur.X
            if cur.Y > maxY:
                maxY = cur.Y

        accessor.min = list({minX, minY})
        accessor.max = list({maxX, maxY})

        # TODO: Buffer stuff

        self._root.accessors.append(accessor)

        return len(self._root.accessors) - 1

    def ExportAccessor_vec3(self, values: List[Vector3]) -> int:
        count = len(values)
        if count is 0:
            raise RuntimeError("Accessors can not have a count of 0.")
        accessor = Accessor(
            componentType=ComponentTypeFloat, count=count, type=AccessorTypeVec3
        )

        minX: float = values[0].X
        minY: float = values[0].Y
        minZ: float = values[0].Z
        maxX: float = values[0].X
        maxY: float = values[0].Y
        maxZ: float = values[0].Z

        for cur in values:
            if cur.X < minX:
                minX = cur.X
            if cur.Y < minY:
                minY = cur.Y
            if cur.Z < minZ:
                minZ = cur.Z
            if cur.X > maxX:
                maxX = cur.X
            if cur.Y > maxY:
                maxY = cur.Y
            if cur.Z > maxZ:
                maxZ = cur.Z

        accessor.min = list({minX, minY, minZ})
        accessor.max = list({maxX, maxY, maxZ})

        # TODO: Buffer stuff

        self._root.accessors.append(accessor)

        return len(self._root.accessors) - 1

    def ExportAccessor_vec4(self, values: List[Vector4]) -> int:
        count = len(values)
        if count is 0:
            raise RuntimeError("Accessors can not have a count of 0.")
        accessor = Accessor(
            componentType=ComponentTypeFloat, count=count, type=AccessorTypeVec4
        )

        minX: float = values[0].X
        minY: float = values[0].Y
        minZ: float = values[0].Z
        minW: float = values[0].W
        maxX: float = values[0].X
        maxY: float = values[0].Y
        maxZ: float = values[0].Z
        maxW: float = values[0].W

        for cur in values:
            if cur.X < minX:
                minX = cur.X
            if cur.Y < minY:
                minY = cur.Y
            if cur.Z < minZ:
                minZ = cur.Z
            if cur.W < minW:
                minW = cur.W
            if cur.X > maxX:
                maxX = cur.X
            if cur.Y > maxY:
                maxY = cur.Y
            if cur.Z > maxZ:
                maxZ = cur.Z
            if cur.W > maxW:
                maxW = cur.W

        accessor.min = list({minX, minY, minZ, minW})
        accessor.max = list({maxX, maxY, maxZ, maxW})

        # TODO: Buffer stuff

        self._root.accessors.append(accessor)

        return len(self._root.accessors) - 1

    def ExportAccessor_color(self, values: List[Color]) -> int:
        count = len(values)
        if count is 0:
            raise RuntimeError("Accessors can not have a count of 0.")
        accessor = Accessor(
            componentType=ComponentTypeFloat, count=count, type=AccessorTypeVec4
        )

        minR: float = values[0].R
        minG: float = values[0].G
        minB: float = values[0].B
        minA: float = values[0].A
        maxR: float = values[0].R
        maxG: float = values[0].G
        maxB: float = values[0].B
        maxA: float = values[0].A

        for cur in values:
            if cur.R < minR:
                minR = cur.R
            if cur.G < minG:
                minG = cur.G
            if cur.B < minB:
                minB = cur.B
            if cur.A < minA:
                minA = cur.A
            if cur.R > maxR:
                maxR = cur.R
            if cur.G > maxG:
                maxG = cur.G
            if cur.B > maxB:
                maxB = cur.B
            if cur.A > maxA:
                maxA = cur.A

        accessor.min = list({minR, minG, minB, minA})
        accessor.max = list({maxR, maxG, maxB, maxA})

        # TODO: Buffer stuff

        self._root.accessors.append(accessor)

        return len(self._root.accessors) - 1

    def ExportBufferView(self, byteOffset: int, byteLength: int) -> int:
        raise NotImplementedError()

    def GetMaterialId(self, root: GLTF2, materialObj: Material) -> int:
        raise NotImplementedError()

    def GetTextureId(self, root: GLTF2, textureObj: Texture) -> int:
        raise NotImplementedError()

    def GetImageId(self, root: GLTF2, imageObj: Texture) -> int:
        raise NotImplementedError()

    def GetSamplerId(self, root: GLTF2, textureObj: Texture) -> int:
        raise NotImplementedError()

    def GetDrawMode(self, topology: GfxPrimitiveType) -> int:

        match (topology):
            case GfxPrimitiveType.kPrimitivePoints:
                return self.DrawMode.Points
            case GfxPrimitiveType.kPrimitiveLines:
                return self.DrawMode.Lines
            case GfxPrimitiveType.kPrimitiveLineStrip:
                return self.DrawMode.LineStrip
            case GfxPrimitiveType.kPrimitiveTriangles:
                return self.DrawMode.Triangles
            case _:
                raise RuntimeError(
                    "glTF does not support Unity mesh topology: ", topology
                )

    ### CUSTOM PART ###
    class DrawMode(IntEnum):
        Points = 0
        Lines = auto()
        LineStrip = auto()
        Triangles = auto()

    def Mesh_GetIndices(  # TODO: Verify this is correct
        self, mesh: Mesh, subMesh: SubMesh, applyBaseVertex: bool = True
    ) -> List[int]:
        firstIndex = subMesh.firstByte // (2 if mesh.m_Use16BitIndices else 4)
        indices = mesh.m_Indices[firstIndex : subMesh.indexCount]
        return [i + subMesh.baseVertex for i in indices] if applyBaseVertex else indices

    def FlipTriangleFaces(self, indices: List[int]):
        for i in range(len(indices)):
            temp = indices[i]
            indices[i] = indices[i + 2]
            indices[i + 2] = temp
