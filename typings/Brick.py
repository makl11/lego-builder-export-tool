from dataclasses import dataclass, field
from urllib.request import urlopen
from io import IOBase

from lego_colors import Lego_Colors

BASE_URL = "https://dbix.services.lego.com/api/v1"
PLATFORM = "android"


@dataclass
class Brick:
    id: str
    revision: str
    color_id: str
    color: str = field(init=False)
    asset_url: str = field(init=False)
    asset_file: IOBase = field(init=False)

    def __post_init__(self):
        self.asset_url = (
            f"{BASE_URL}/bricks/{self.id}?Revision={self.revision}&Platform={PLATFORM}"
        )
        self.asset_file = urlopen(self.asset_url)
        self.color = Lego_Colors[self.color_id]
