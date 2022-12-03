import xml.etree.ElementTree as ET
from json import load as parseJson
from pprint import PrettyPrinter
from urllib.request import urlopen

from UnityPy import load as loadUnityFile

pp = PrettyPrinter(indent=4)
BASE_URL = "https://dbix.services.lego.com/api/v1"


def get_model_info(model_id, locale="en-US"):
    url = f"https://buildinginstructions.services.lego.com/Products/{model_id}?culture={locale}&market={locale.split('-')[1]}"
    build_instructions = parseJson(
        urlopen(f"{BASE_URL}/buildinginstructions?ProductNumber={model_id}")
    )["BuildingInstructions"]
    model_info = parseJson(urlopen(url))
    model_info["BuildingInstructions"] = build_instructions
    return model_info


def load_build_instructions_xml(build_instructions):
    return ET.parse(urlopen(build_instructions["Url"]))


def make_find_and_load_brick(build_instructions_xml):
    def find_and_load_brick(refId):
        brick = build_instructions_xml.find(f".//Brick[@refID='{refId}']")
        id, revision = brick.get("designID").split(";")
        asset_url = f"{BASE_URL}/bricks/{id}?Revision={revision}&Platform=android"
        return id, revision, urlopen(asset_url)

    return find_and_load_brick


if __name__ == "__main__":
    model_info = get_model_info(75335, "de-de")
    instructions = load_build_instructions_xml(model_info["BuildingInstructions"][0])
    steps = instructions.findall(".//Step")

    find_and_load_brick = make_find_and_load_brick(instructions)

    for step in steps:
        for brick in step.findall(".//In[@brickRef]"):
            id, revision, file = find_and_load_brick(brick.get("brickRef"))

            env = loadUnityFile(file.read())

            main_GameObject = [
                o.read()
                for o in env.objects
                if o.type.name == "GameObject" and o.read().name == id
            ][0]

            pp.pprint(main_GameObject)

            ### break after first iteration until code for processing a step and its bricks is done
            break
        break
