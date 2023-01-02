import math
import os
import sys
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List, Tuple

from pygltflib import ARRAY_BUFFER
from pygltflib import BYTE as ComponentTypeByte
from pygltflib import CLAMP_TO_EDGE, ELEMENT_ARRAY_BUFFER
from pygltflib import FLOAT as ComponentTypeFloat
from pygltflib import GLTF2, MIRRORED_REPEAT, REPEAT
from pygltflib import SCALAR as AccessorTypeScalar
from pygltflib import SHORT as ComponentTypeShort
from pygltflib import UNSIGNED_BYTE as ComponentTypeUnsignedByte
from pygltflib import UNSIGNED_INT as ComponentTypeUnsignedInt
from pygltflib import UNSIGNED_SHORT as ComponentTypeUnsignedShort
from pygltflib import VEC2 as AccessorTypeVec2
from pygltflib import VEC3 as AccessorTypeVec3
from pygltflib import VEC4 as AccessorTypeVec4
from pygltflib import Accessor, Asset, Attributes, Buffer, BufferView
from pygltflib import Mesh as GLTFMesh
from pygltflib import Node
from pygltflib import NormalMaterialTexture as NormalTextureInfo
from pygltflib import (
    OcclusionTextureInfo,
    PbrMetallicRoughness,
    Primitive,
    Sampler,
    Scene,
    TextureInfo,
)

from UnityPy.classes import (
    GameObject,
    Material,
    Mesh,
    MeshFilter,
    MeshRenderer,
    SkinnedMeshRenderer,
    Texture,
    Texture2D,
    Transform,
)
from UnityPy.classes.Mesh import SubMesh
from UnityPy.classes.Object import NodeHelper
from UnityPy.enums import GfxPrimitiveType
from UnityPy.math import Color, Quaternion, Vector2, Vector3, Vector4
from UnityPy.streams import EndianBinaryWriter

from .util import get_transform


class BUFFERVIEW_TARGETS(IntEnum):
    ARRAY_BUFFER = ARRAY_BUFFER
    ELEMENT_ARRAY_BUFFER = ELEMENT_ARRAY_BUFFER


class WRAPPING_MODES(IntEnum):
    CLAMP_TO_EDGE = CLAMP_TO_EDGE
    MIRRORED_REPEAT = MIRRORED_REPEAT
    REPEAT = REPEAT


class TextureMapType(IntEnum):
    Main = 0
    Bump = 1
    SpecGloss = 2
    Emission = 3
    MetallicGloss = 4
    Light = 5
    Occlusion = 6


class UnityGLTFExporter:
    @dataclass
    class ImageInfo:
        texture: Texture2D
        textureMapType: TextureMapType

    _rootGameObject: GameObject
    _root: GLTF2
    _bufferId: int
    _buffer: Buffer
    _bufferWriter: EndianBinaryWriter
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

    PrimKey = Tuple[Mesh, Material]
    _primOwner: Dict[PrimKey, int] = {}
    _meshToPrims: Dict[Mesh, List[Primitive]] = {}

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

    @staticmethod
    def AlignToBoundary(
        writer: EndianBinaryWriter, pad: bytes = b" ", boundary: int = 4
    ):
        currentLength = writer.Length
        newLength = UnityGLTFExporter.CalculateAlignment(currentLength, boundary)
        writer.write_bytes(pad * (newLength - currentLength))

    @staticmethod
    def CalculateAlignment(currentSize: int, byteAlignment: int) -> int:
        return (
            math.floor((currentSize + byteAlignment - 1) / byteAlignment)
            * byteAlignment
        )

    def SaveGLTFandBin(self, path: str, fileName: str):
        self._shouldUseInternalBufferForImages = False
        self._bufferWriter = EndianBinaryWriter(endian="<")
        self._root.scene = self.ExportScene(self._rootGameObject)
        self.AlignToBoundary(self._bufferWriter, b"00")
        self._buffer.byteLength = self.CalculateAlignment(self._bufferWriter.Length, 4)
        self._root.set_binary_blob(self._bufferWriter.bytes)
        self._root.save(os.path.join(path, fileName + ".gltf"), self._root.asset)
        self.ExportImages(path)

    def ExportImages(self, outputPath: str):
        for imgInfo in self._imageInfos:
            match (imgInfo.textureMapType):
                case TextureMapType.MetallicGloss:
                    self.ExportMetallicGlossTexture(imgInfo.texture, outputPath)
                case TextureMapType.Bump:
                    self.ExportNormalTexture(imgInfo.texture, outputPath)
                case _:
                    self.Export_Texture(imgInfo.texture, outputPath)

    def ExportMetallicGlossTexture(self, texture: Texture2D, outpath: str) -> None:
        raise NotImplementedError()

    def ExportNormalTexture(self, texture: Texture2D, outpath: str) -> None:
        raise NotImplementedError()

    def Export_Texture(self, texture: Texture2D, outpath: str) -> None:
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
        node = self.SetUnityTransform(node, get_transform(gameobject))

        self._root.nodes.append(node)
        nodeId = len(self._root.nodes) - 1
        prims, nonPrims = UnityGLTFExporter.FilterPrimitives(gameobject)

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
            node.children = [self.ExportNode(np) for np in nonPrims]

        return nodeId

    @staticmethod
    def ContainsValidRenderer(gameobj: GameObject):
        return (
            gameobj.m_MeshFilter is not None and gameobj.m_MeshRenderer is not None
        ) or gameobj.m_SkinnedMeshRenderer is not None

    @staticmethod
    def FilterPrimitives(gameobject: GameObject):
        primitives: List[GameObject] = list()
        nonPrimitives: List[GameObject] = list()

        if UnityGLTFExporter.ContainsValidRenderer(gameobject):
            primitives.append(gameobject)

        transform = get_transform(gameobject)
        child_objects = [
            c.get_obj().read().m_GameObject.get_obj().read()
            for c in transform.m_Children
        ]

        child: GameObject
        for child in child_objects:
            if UnityGLTFExporter.isPrimitive(child):
                primitives.append(child)
            else:
                nonPrimitives.append(child)

        return primitives, nonPrimitives

    @staticmethod
    def isPrimitive(gameobj: GameObject):
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
            and UnityGLTFExporter.ContainsValidRenderer(gameobj)
        )

    def ExportMesh(self, name: str, primitives: List[GameObject]):
        key: UnityGLTFExporter.PrimKey
        existingMeshId: int | None = None
        for prim in primitives:
            smr = prim.m_SkinnedMeshRenderer
            filter = prim.m_MeshFilter
            renderer = prim.m_MeshRenderer
            if smr:
                smr = smr.get_obj().read()
                assert isinstance(smr, SkinnedMeshRenderer)
                mesh = smr.m_Mesh.get_obj().read()
                assert isinstance(mesh, Mesh)
                material = smr.m_Materials[0].get_obj().read()
                assert isinstance(material, Material)
                key = (mesh, material)
            elif filter and renderer:
                filter = filter.get_obj().read()
                assert isinstance(filter, MeshFilter)
                mesh = filter.m_Mesh.get_obj().read()
                assert isinstance(mesh, Mesh)
                renderer = renderer.get_obj().read()
                assert isinstance(renderer, MeshRenderer)
                material = renderer.m_Materials[0].get_obj().read()
                assert isinstance(material, Material)
                key = (mesh, material)
            else:
                raise RuntimeError("Unreachable")
            tempMeshId = self._primOwner.get(key)
            if tempMeshId and (existingMeshId is None or tempMeshId == existingMeshId):
                existingMeshId = tempMeshId
            else:
                existingMeshId = None
                break
        if existingMeshId:
            return existingMeshId

        mesh = GLTFMesh(name=name)
        # sum is used to flatten the list by abbusing list()'s __add__ method
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

        primVariations = self._meshToPrims.get(meshobj)
        if primVariations and len(primVariations) == len(meshobj.m_SubMeshes):
            for i in range(len(meshobj.m_SubMeshes)):
                newPrim = self._meshToPrims[meshobj][i]
                newPrim.material = self.ExportMaterial(materials[i])
                prims[i] = newPrim
            return prims

        aPosition = self.ExportAccessor_vec3(
            self.ConvertVector3CoordinateSpaceAndCopy(
                [
                    Vector3(*meshobj.m_Vertices[i : i + 3])
                    for i in range(0, len(meshobj.m_Vertices), 3)
                ],
                Vector3(-1, 1, 1),
            )
        )

        aNormal, aTangent, aTexcoord0, aTexcoord1, aColor0 = [None for _ in range(5)]

        if meshobj.m_Normals and len(meshobj.m_Normals):
            aNormal = self.ExportAccessor_vec3(
                self.ConvertVector3CoordinateSpaceAndCopy(
                    [
                        Vector3(*meshobj.m_Normals[i : i + 3])
                        for i in range(0, len(meshobj.m_Normals), 3)
                    ],
                    Vector3(-1, 1, 1),
                )
            )

        if meshobj.m_Tangents and len(meshobj.m_Tangents):
            aTangent = self.ExportAccessor_vec4(
                self.ConvertVector4CoordinateSpaceAndCopy(
                    [
                        Vector4(*meshobj.m_Tangents[i : i + 4])
                        for i in range(0, len(meshobj.m_Tangents), 4)
                    ],
                    Vector4(-1, 1, 1, -1),
                )
            )

        if meshobj.m_UV0 and len(meshobj.m_UV0):
            aTexcoord0 = self.ExportAccessor_vec2(
                self.FlipTexCoordArrayVAndCopy(
                    [
                        Vector2(*meshobj.m_UV0[i : i + 2])
                        for i in range(0, len(meshobj.m_UV0), 2)
                    ]
                )
            )

        if meshobj.m_UV2 and len(meshobj.m_UV2):
            aTexcoord1 = self.ExportAccessor_vec2(
                self.FlipTexCoordArrayVAndCopy(
                    [
                        Vector2(*meshobj.m_UV2[i : i + 2])
                        for i in range(0, len(meshobj.m_UV2), 2)
                    ]
                )
            )

        if meshobj.m_Colors and len(meshobj.m_Colors):
            aColor0 = self.ExportAccessor_color(
                [
                    Color(*meshobj.m_Colors[i : i + 4])
                    for i in range(0, len(meshobj.m_Colors), 4)
                ]
            )

        lastMaterialId: int | None = None

        for i, submesh in enumerate(meshobj.m_SubMeshes):
            p = Primitive()
            topology = submesh.topology
            indices = self.Mesh_GetIndices(meshobj, submesh)
            if topology == GfxPrimitiveType.kPrimitiveTriangles:
                self.FlipTriangleFaces(indices)
            p.mode = self.GetDrawMode(topology)
            p.indices = self.ExportAccessor_int(indices, True)

            p.attributes = Attributes(POSITION=aPosition)
            if aNormal:
                p.attributes.NORMAL = aNormal
            if aTangent:
                p.attributes.TANGENT = aTangent
            if aTexcoord0:
                p.attributes.TEXCOORD_0 = aTexcoord0
            if aTexcoord1:
                p.attributes.TEXCOORD_1 = aTexcoord1
            if aColor0:
                p.attributes.COLOR_0 = aColor0

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

            prims.insert(i, p)

        self._meshToPrims[meshobj] = prims

        return prims

    def ExportMaterial(self, material: Material) -> int:
        pass
        # raise NotImplementedError()

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

    def ExportCommonConstant(
        self, materialObj: Material
    ) -> Any:  # -> MaterialCommonConstant:
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

    def ExportSampler(self, texture: Texture2D) -> int:
        samplerId = self.GetSamplerId(texture)
        if samplerId:
            return samplerId
        sampler = Sampler()

        match (texture.m_TextureSettings.m_WrapMode):
            case self.TextureWrapMode.Clamp:
                sampler.wrapS = self.WrapMode.Clamp
                sampler.wrapT = self.WrapMode.Clamp
            case self.TextureWrapMode.Repeat:
                sampler.wrapS = self.WrapMode.Repeat
                sampler.wrapT = self.WrapMode.Repeat
            case self.TextureWrapMode.Mirror:
                sampler.wrapS = self.WrapMode.Mirror
                sampler.wrapT = self.WrapMode.Mirror
            case _:
                sampler.wrapS = self.WrapMode.Repeat
                sampler.wrapT = self.WrapMode.Repeat

        match (texture.m_TextureSettings.m_FilterMode):
            case self.FilterMode.Point:
                sampler.minFilter = self.MinFilterMode.NearestMipmapNearest
                sampler.magFilter = self.MagFilterMode.Nearest
            case self.FilterMode.Bilinear:
                sampler.minFilter = self.MinFilterMode.LinearMipmapNearest
                sampler.magFilter = self.MagFilterMode.Linear
            case self.FilterMode.Trilinear:
                sampler.minFilter = self.MinFilterMode.LinearMipmapLinear
                sampler.magFilter = self.MagFilterMode.Linear
            case _:
                print(
                    "Unsupported Texture.filterMode: ",
                    texture.m_TextureSettings.m_FilterMode,
                    file=sys.stderr,
                )
                sampler.minFilter = self.MinFilterMode.LinearMipmapLinear
                sampler.magFilter = self.MagFilterMode.Linear

    def ExportAccessor_int(self, values: List[int], isIndices: bool = False) -> int:
        count = len(values)
        if count == 0:
            raise RuntimeError("Accessors can not have a count of 0.")
        accessor = Accessor(count=count, type=AccessorTypeScalar)

        min: float = values[0]
        max: float = values[0]

        for cur in values:
            if cur < min:
                min = cur
            if cur > max:
                max = cur

        accessor.min = list([min])
        accessor.max = list([max])

        self.AlignToBoundary(self._bufferWriter, b"00")
        byteOffset = self.CalculateAlignment(self._bufferWriter.Position, 4)

        if max <= 255 and min >= 0:
            accessor.componentType = ComponentTypeUnsignedByte
            [self._bufferWriter.write_u_byte(val) for val in values]
        elif max <= 127 and min >= -128 and not isIndices:
            accessor.componentType = ComponentTypeByte
            [self._bufferWriter.write_byte(val) for val in values]
        elif max <= 32767 and min >= -32768 and not isIndices:
            accessor.componentType = ComponentTypeShort
            [self._bufferWriter.write_short(val) for val in values]
        elif max <= 65535 and min >= 0:
            accessor.componentType = ComponentTypeUnsignedShort
            [self._bufferWriter.write_u_short(val) for val in values]
        elif min >= 0:
            accessor.componentType = ComponentTypeUnsignedInt
            [self._bufferWriter.write_u_int(val) for val in values]
        else:
            accessor.componentType = ComponentTypeFloat
            [self._bufferWriter.write_float(val) for val in values]

        byteLength = self.CalculateAlignment(
            self._bufferWriter.Position - byteOffset, 4
        )

        target = (
            BUFFERVIEW_TARGETS.ELEMENT_ARRAY_BUFFER
            if isIndices
            else BUFFERVIEW_TARGETS.ARRAY_BUFFER
        )
        accessor.bufferView = self.ExportBufferView(byteOffset, byteLength, target)

        self._root.accessors.append(accessor)

        return len(self._root.accessors) - 1

    def AppendToBufferMultiplyOf4(self, byteOffset: int, byteLength: int) -> int:
        moduloOffset = byteLength % 4
        if moduloOffset > 0:
            self._bufferWriter.write_bytes(b"00" * (4 - moduloOffset))
            byteLength = self._bufferWriter.Position - byteOffset
        return byteLength

    def ExportAccessor_vec2(self, values: List[Vector2]) -> int:
        count = len(values)
        if count == 0:
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

        accessor.min = list([minX, minY])
        accessor.max = list([maxX, maxY])

        self.AlignToBoundary(self._bufferWriter, b"00")
        byteOffset = self.CalculateAlignment(self._bufferWriter.Position, 4)
        for vec in values:
            self._bufferWriter.write_float(vec.X)
            self._bufferWriter.write_float(vec.Y)
        byteLength = self.CalculateAlignment(
            self._bufferWriter.Position - byteOffset, 4
        )

        accessor.bufferView = self.ExportBufferView(byteOffset, byteLength)

        self._root.accessors.append(accessor)

        return len(self._root.accessors) - 1

    def ExportAccessor_vec3(self, values: List[Vector3]) -> int:
        count = len(values)
        if count == 0:
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

        accessor.min = list([minX, minY, minZ])
        accessor.max = list([maxX, maxY, maxZ])

        self.AlignToBoundary(self._bufferWriter, b"00")
        byteOffset = self.CalculateAlignment(self._bufferWriter.Position, 4)
        for vec in values:
            self._bufferWriter.write_float(vec.X)
            self._bufferWriter.write_float(vec.Y)
            self._bufferWriter.write_float(vec.Z)
        byteLength = self.CalculateAlignment(
            self._bufferWriter.Position - byteOffset, 4
        )

        accessor.bufferView = self.ExportBufferView(byteOffset, byteLength)

        self._root.accessors.append(accessor)

        return len(self._root.accessors) - 1

    def ExportAccessor_vec4(self, values: List[Vector4]) -> int:
        count = len(values)
        if count == 0:
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

        accessor.min = list([minX, minY, minZ, minW])
        accessor.max = list([maxX, maxY, maxZ, maxW])

        self.AlignToBoundary(self._bufferWriter, b"00")
        byteOffset = self.CalculateAlignment(self._bufferWriter.Position, 4)
        for vec in values:
            self._bufferWriter.write_float(vec.X)
            self._bufferWriter.write_float(vec.Y)
            self._bufferWriter.write_float(vec.Z)
            self._bufferWriter.write_float(vec.W)
        byteLength = self.CalculateAlignment(
            self._bufferWriter.Position - byteOffset, 4
        )

        accessor.bufferView = self.ExportBufferView(byteOffset, byteLength)

        self._root.accessors.append(accessor)

        return len(self._root.accessors) - 1

    def ExportAccessor_color(self, values: List[Color]) -> int:
        count = len(values)
        if count == 0:
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

        accessor.min = list([minR, minG, minB, minA])
        accessor.max = list([maxR, maxG, maxB, maxA])

        self.AlignToBoundary(self._bufferWriter, b"00")
        byteOffset = self.CalculateAlignment(self._bufferWriter.Position, 4)
        for vec in values:
            self._bufferWriter.write_float(vec.R)
            self._bufferWriter.write_float(vec.G)
            self._bufferWriter.write_float(vec.B)
            self._bufferWriter.write_float(vec.A)
        byteLength = self.CalculateAlignment(
            self._bufferWriter.Position - byteOffset, 4
        )

        accessor.bufferView = self.ExportBufferView(byteOffset, byteLength)

        self._root.accessors.append(accessor)

        return len(self._root.accessors) - 1

    def ExportBufferView(
        self,
        byteOffset: int,
        byteLength: int,
        target: BUFFERVIEW_TARGETS = BUFFERVIEW_TARGETS.ARRAY_BUFFER,
    ) -> int:
        bufferView = BufferView(
            buffer=self._bufferId,
            byteOffset=byteOffset,
            byteLength=byteLength,
            target=target,
        )
        self._root.bufferViews.append(bufferView)
        return len(self._root.bufferViews) - 1

    def GetMaterialId(self, materialObj: Material) -> int | None:
        for i, material in enumerate(self._materials):
            if material == materialObj:
                return i
        return None

    def GetTextureId(self, textureObj: Texture) -> int | None:
        for i, texture in enumerate(self._textures):
            if texture == textureObj:
                return i
        return None

    def GetImageId(self, imageObj: Texture) -> int | None:
        for i, imgInfo in enumerate(self._imageInfos):
            if imgInfo.texture == imageObj:
                return i
        return None

    def GetSamplerId(self, textureObj: Texture2D) -> int | None:
        for i, sampler in enumerate(self._root.samplers):
            filterIsNearest = (
                sampler.minFilter == self.MinFilterMode.Nearest
                or sampler.minFilter == self.MinFilterMode.NearestMipmapNearest
                or sampler.minFilter == self.MinFilterMode.NearestMipmapLinear
            )

            filterIsLinear = (
                sampler.minFilter == self.MinFilterMode.Linear
                or sampler.minFilter == self.MinFilterMode.LinearMipmapNearest
            )

            filterMatched = (
                textureObj.m_TextureSettings.m_FilterMode == self.FilterMode.Point
                and filterIsNearest
                or textureObj.m_TextureSettings.m_FilterMode == self.FilterMode.Bilinear
                and filterIsLinear
                or textureObj.m_TextureSettings.m_FilterMode
                == self.FilterMode.Trilinear
                and sampler.minFilter == self.MinFilterMode.LinearMipmapLinear
            )

            wrapMatched = (
                textureObj.m_TextureSettings.m_WrapMode == self.TextureWrapMode.Clamp
                and sampler.wrapS == WRAPPING_MODES.CLAMP_TO_EDGE
                or textureObj.m_TextureSettings.m_WrapMode
                == self.TextureWrapMode.Repeat
                and sampler.wrapS == WRAPPING_MODES.REPEAT
                or textureObj.m_TextureSettings.m_WrapMode
                == self.TextureWrapMode.Mirror
                and sampler.wrapS == WRAPPING_MODES.MIRRORED_REPEAT
            )

            if filterMatched and wrapMatched:
                return i
        return None

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
    @staticmethod
    def SetUnityTransform(node: Node, transform: Transform):
        pos = UnityGLTFExporter.UnityToGltfVector3Convert(transform.m_LocalPosition)
        scale = transform.m_LocalScale
        rot = UnityGLTFExporter.UnityToGltfQuaternionConvert(transform.m_LocalRotation)
        if pos != Vector3.Zero():
            node.translation = list((pos.X, pos.Y, pos.Z))
        if scale != Vector3.One():
            node.scale = list((scale.X, scale.Y, scale.Z))
        if rot.X != 0 and rot.Y != 0 and rot.Z != 0 and rot.W != 1:
            node.rotation = list((rot.X, rot.Y, rot.Z, rot.W))
        return node

    @staticmethod
    def ConvertVector3CoordinateSpaceAndCopy(
        vector3s: List[Vector3], coordinateSpaceCoordinateScale: Vector3
    ):
        return [
            Vector3(
                vector.X * coordinateSpaceCoordinateScale.X,
                vector.Y * coordinateSpaceCoordinateScale.Y,
                vector.Z * coordinateSpaceCoordinateScale.Z,
            )
            for vector in vector3s
        ]

    @staticmethod
    def ConvertVector4CoordinateSpaceAndCopy(
        vector4s: List[Vector4 | Quaternion], coordinateSpaceCoordinateScale: Vector4
    ):
        return [
            Vector4(
                vector.X * coordinateSpaceCoordinateScale.X,
                vector.Y * coordinateSpaceCoordinateScale.Y,
                vector.Z * coordinateSpaceCoordinateScale.Z,
                vector.W * coordinateSpaceCoordinateScale.W,
            )
            for vector in vector4s
        ]

    @staticmethod
    def FlipTexCoordArrayVAndCopy(vector2s: List[Vector2]):
        return [Vector2(vector.X, 1.0 - vector.Y) for vector in vector2s]

    @staticmethod
    def UnityToGltfVector3Convert(vector3: Vector3):
        return Vector3(vector3.X * -1.0, vector3.Y * 1.0, vector3.Z * 1.0)

    @staticmethod
    def UnityToGltfVector4Convert(vector4: Vector4):
        return Vector4(
            vector4.X * -1,
        )

    @staticmethod
    def UnityToGltfQuaternionConvert(quaternion: Quaternion):
        return Quaternion(
            quaternion.X * 1.0, quaternion.Y * -1.0, quaternion.Z * -1.0, quaternion.W
        )

    class DrawMode(IntEnum):
        Points = 0
        Lines = 1
        LineStrip = 3
        Triangles = 4

    def Mesh_GetIndices(
        self, mesh: Mesh, subMesh: SubMesh, applyBaseVertex: bool = True
    ) -> List[int]:
        firstIndex = subMesh.firstByte // (2 if mesh.m_Use16BitIndices else 4)
        indices = mesh.m_Indices[firstIndex : subMesh.indexCount]
        return [i + subMesh.baseVertex for i in indices] if applyBaseVertex else indices

    def FlipTriangleFaces(self, indices: List[int]):
        for i in range(0, len(indices), 3):
            temp = indices[i]
            indices[i] = indices[i + 2]
            indices[i + 2] = temp

    class MinFilterMode(IntEnum):
        NONE = 0
        Nearest = 9728
        Linear = 9729
        NearestMipmapNearest = 9984
        LinearMipmapNearest = 9985
        NearestMipmapLinear = 9986
        LinearMipmapLinear = 9987

    class MagFilterMode(IntEnum):
        NONE = 0
        Nearest = 9728
        Linear = 9729

    class FilterMode(IntEnum):
        Point = 0
        Bilinear = 1
        Trilinear = 2

    class TextureWrapMode(IntEnum):
        Repeat = 0
        Clamp = 1
        Mirror = 2
        MirrorOnce = 3

    class WrapMode(IntEnum):
        Repeat = 0
        Clamp = 1
        Mirror = 2
        MirrorOnce = 3
