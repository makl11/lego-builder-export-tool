import xml.etree.ElementTree as ET
from json import load as parseJson
from pprint import PrettyPrinter
from urllib.request import urlopen

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


if __name__ == "__main__":
    model_info = get_model_info(75335, "de-de")
    instructions = load_build_instructions_xml(model_info["BuildingInstructions"][0])
    steps = instructions.findall(".//Step")

    pp.pprint(model_info)

