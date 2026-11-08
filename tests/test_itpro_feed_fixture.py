from pathlib import Path
from xml.etree import ElementTree


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "itpro_software_engineering.xml"


def test_software_engineering_fixture_identifies_category() -> None:
    root = ElementTree.parse(FIXTURE_PATH).getroot()

    assert root.findtext("./channel/title") == "ITPro.lk - Software Engineering Jobs"
    assert root.findtext("./channel/item/link") == (
        "https://itpro.lk/job/15717/"
        "software-engineer-intern-january-2027-intake-at-nippon-it-and-educational-solution-nites/"
    )
