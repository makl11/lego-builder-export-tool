from dataclasses import dataclass
from typing import Any, List

from UnityPy.classes import GameObject

from .Brick import *


class GOWithChildren:
    child_objects: List[GameObject]

    def __init__(self, gameobject: GameObject, child_objects: List[GameObject] = []):
        self._gameobject = gameobject
        self._child_objects = child_objects

    @property
    def field(self):  # type: ignore
        return self._gameobject.field  # type: ignore


@dataclass
class CobuildSubModel:
    Id: str
    MaxBuilders: int
    Revision: str

    @staticmethod
    def from_dict(obj: Any) -> "CobuildSubModel":
        _Id = str(obj.get("Id"))
        _MaxBuilders = int(obj.get("MaxBuilders"))
        _Revision = str(obj.get("Revision"))
        return CobuildSubModel(_Id, _MaxBuilders, _Revision)


@dataclass
class InstructionFile:
    Id: str
    FileUrl: str
    CoverUrl: str
    Title: str
    Type: str

    @staticmethod
    def from_dict(obj: Any) -> "InstructionFile":
        _Id = str(obj.get("Id"))
        _FileUrl = str(obj.get("FileUrl"))
        _CoverUrl = str(obj.get("CoverUrl"))
        _Title = str(obj.get("Title"))
        _Type = str(obj.get("Type"))
        return InstructionFile(_Id, _FileUrl, _CoverUrl, _Title, _Type)


@dataclass
class Suitability:
    Description: str
    From: int
    To: int

    @staticmethod
    def from_dict(obj: Any) -> "Suitability":
        _Description = str(obj.get("Description"))
        _From = int(obj.get("From"))
        _To = int(obj.get("To"))
        return Suitability(_Description, _From, _To)


@dataclass
class Path:
    Name: str
    ImageUrl: str

    @staticmethod
    def from_dict(obj: Any) -> "Path":
        _Name = str(obj.get("Name"))
        _ImageUrl = str(obj.get("ImageUrl"))
        return Path(_Name, _ImageUrl)


@dataclass
class BuildingInstruction:
    Name: str
    Id: str
    Url: str
    HasEnrichment: bool
    ImageUrl: str
    LastModifiedDate: str
    Revision: str
    Maturity: str
    Paths: List[Path]

    @staticmethod
    def from_dict(obj: Any) -> "BuildingInstruction":
        _Name = str(obj.get("Name"))
        _Id = str(obj.get("Id"))
        _Url = str(obj.get("Url"))
        _HasEnrichment = bool(obj.get("HasEnrichment"))
        _ImageUrl = str(obj.get("ImageUrl"))
        _LastModifiedDate = str(obj.get("LastModifiedDate"))
        _Revision = str(obj.get("Revision"))
        _Maturity = str(obj.get("Maturity"))
        _Paths = [Path.from_dict(y) for y in obj.get("Paths")]
        return BuildingInstruction(
            _Name,
            _Id,
            _Url,
            _HasEnrichment,
            _ImageUrl,
            _LastModifiedDate,
            _Revision,
            _Maturity,
            _Paths,
        )


@dataclass
class ModelInfo:
    Id: str
    ThemeId: str
    LaunchDate: str
    Title: str
    Description: str
    BoxImageUrl: str
    PrimaryImageGrownupsUrl: str
    ModelImageUrl: str
    IsHistoricalProduct: bool
    HasDbix: bool
    HasCobuild: bool
    HasMissions: bool
    CobuildSubModels: List[CobuildSubModel]
    BrickCount: int
    Suitability: Suitability
    Images: List[str]
    Applications: List[Any]
    InstructionsVersion: str
    InstructionFiles: List[InstructionFile]
    Language: str
    BuildingInstructions: List[BuildingInstruction]

    @staticmethod
    def from_dict(obj: Any, *args: Any) -> "ModelInfo":
        _Id = str(obj.get("Id"))
        _ThemeId = str(obj.get("ThemeId"))
        _LaunchDate = str(obj.get("LaunchDate"))
        _Title = str(obj.get("Title"))
        _Description = str(obj.get("Description"))
        _BoxImageUrl = str(obj.get("BoxImageUrl"))
        _PrimaryImageGrownupsUrl = str(obj.get("PrimaryImageGrownupsUrl"))
        _ModelImageUrl = str(obj.get("ModelImageUrl"))
        _IsHistoricalProduct = bool(obj.get("IsHistoricalProduct"))
        _HasDbix = bool(obj.get("HasDbix"))
        _HasCobuild = bool(obj.get("HasCobuild"))
        _HasMissions = bool(obj.get("HasMissions"))
        _CobuildSubModels = [
            CobuildSubModel.from_dict(y) for y in obj.get("CobuildSubModels")
        ]
        _BrickCount = int(obj.get("BrickCount"))
        _Suitability = Suitability.from_dict(obj.get("Suitability"))
        _Images = [str(y) for y in obj.get("Images")]
        _Applications = [y for y in obj.get("Applications")]
        _InstructionsVersion = str(obj.get("InstructionsVersion"))
        _InstructionFiles = [
            InstructionFile.from_dict(y) for y in obj.get("InstructionFiles")
        ]
        _Language = str(obj.get("Language"))
        _BuildingInstructions = [
            BuildingInstruction.from_dict(y) for y in obj.get("BuildingInstructions")
        ]
        return ModelInfo(
            _Id,
            _ThemeId,
            _LaunchDate,
            _Title,
            _Description,
            _BoxImageUrl,
            _PrimaryImageGrownupsUrl,
            _ModelImageUrl,
            _IsHistoricalProduct,
            _HasDbix,
            _HasCobuild,
            _HasMissions,
            _CobuildSubModels,
            _BrickCount,
            _Suitability,
            _Images,
            _Applications,
            _InstructionsVersion,
            _InstructionFiles,
            _Language,
            _BuildingInstructions,
        )
