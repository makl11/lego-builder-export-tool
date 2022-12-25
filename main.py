import xml.etree.ElementTree as ET
from json import load as parseJson
from pprint import PrettyPrinter
from urllib.request import urlopen

from UnityPy import load as loadUnityFile  # type: ignore because I'd have to create my own Stub

from typings import Brick, BuildingInstruction, ModelInfo

pp = PrettyPrinter(indent=4)
BASE_URL = "https://dbix.services.lego.com/api/v1"


def hex_to_rgb0to1(hex: str):
    r = int(hex[0:2], 16) / 255
    g = int(hex[2:4], 16) / 255
    b = int(hex[4:6], 16) / 255
    return r, g, b


def get_model_info(model_id: str | int, locale: str = "en-US"):
    url = f"https://buildinginstructions.services.lego.com/Products/{model_id}?culture={locale}&market={locale.split('-')[1]}"
    build_instructions = parseJson(
        urlopen(f"{BASE_URL}/buildinginstructions?ProductNumber={model_id}")
    ).pop("BuildingInstructions")
    model_info: ModelInfo = parseJson(
        urlopen(url),
        object_hook=lambda o: ModelInfo.from_dict(
            {**o, "BuildingInstructions": build_instructions}
        )
        if "ThemeId" in o
        else o,
    )
    return model_info


def load_build_instructions_xml(build_instruction: BuildingInstruction):
    return ET.parse(urlopen(build_instruction.Url))


def make_find_and_load_brick(build_instructions_xml: ET.ElementTree):
    def find_and_load_brick(refId: str | int) -> Brick:
        brick = build_instructions_xml.find(f".//Brick[@refID='{refId}']/Part")
        if not brick:
            raise RuntimeError(f"Brick with refId {refId} not found")
        id, revision = brick.attrib["designID"].split(";")
        color_id, _ = brick.attrib["materials"].split(":")  # idk what _ is yet

        return Brick(id, revision, color_id)

    return find_and_load_brick


def resolve_game_object_structure(main_gameobject: Any):
    """This function modifies the gameobject directly. No need to use the return value of this function, but you could."""
    transform = main_gameobject.m_Transform.get_obj().read()
    if len(transform.m_Children) == 0:
        return main_gameobject
    children = [
        resolve_game_object_structure(c.get_obj().read().m_GameObject.get_obj().read())
        for c in transform.m_Children
    ]
    main_gameobject.child_objects = children
    return main_gameobject


if __name__ == "__main__":
    model_info = get_model_info(75335, "de-de")
    instructions = load_build_instructions_xml(model_info.BuildingInstructions[0])
    steps = instructions.findall(".//Step")

    find_and_load_brick = make_find_and_load_brick(instructions)

    for step in steps:
        for brick in step.findall(".//In[@brickRef]"):
            brick = find_and_load_brick(brick.attrib["brickRef"])

            env = loadUnityFile(brick.asset_file.read())

            game_objects = [
                o.read() for o in env.objects if o.type.name == "GameObject"
            ]

            main = [go for go in game_objects if go.name == brick.id][0]  # type: ignore

            resolve_game_object_structure(main)

            pp.pprint(main)

            ### break after first iteration until code for processing a step and its bricks is done
            break
        break
