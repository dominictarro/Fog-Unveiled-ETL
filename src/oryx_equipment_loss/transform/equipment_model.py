"""
Case parser for a listing of an Oryx equipment model.
"""
from __future__ import annotations
import logging
import re
import traceback
from typing import TYPE_CHECKING, Generator, Optional

from src.oryx_equipment_loss.transform.case_parser import CaseParser

if TYPE_CHECKING:
    from src.oryx_equipment_loss.case import Case
    import bs4


logger = logging.getLogger(__name__)


class EquipmentModelParser:
    """Generates cases from an equipment model section.
    """

    def __init__(self, tag: bs4.Tag) -> None:
        self.tag: bs4.Tag = tag

    @property
    def country_of_production_url(self) -> Optional[str]:
        img = img = self.tag.find('img', recursive=True)
        return img.attrs.get('src', None)

    # Models are embedded in text like: "12 BRM-1K reconnaissance vehicle"
    # where that initial number denotes the total number of entries for the
    # model
    #
    # Irregular Example
    #   "  BTR-70"
    model_pattern = re.compile(r"^\s*(?P<entries>\d*)\s+(?P<model>.+)$", flags=re.DOTALL)

    def model(self) -> str:
        substring = self.tag.text.split(':', 1)[0]
        return self.model_pattern.match(substring).group('model')

    # Example 1
    #     https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/\
    #     Flag_of_the_Soviet_Union.svg/23px-Flag_of_the_Soviet_Union.svg.png
    #
    # Example 2
    #     https://upload.wikimedia.org/wikipedia/en/thumb/0/03/\
    #     Flag_of_Italy.svg/23px-Flag_of_Italy.svg.png
    national_flag_url_pattern = re.compile(
        r"^.+/Flag_of_(the_)?(?P<country>[\w]+)(_.+?)?\.svg/.+$", flags=re.DOTALL)

    def country_of_production(self) -> str:
        """Gets the name of the country in a national flag URL from WikiMedia.

        :return: Name of the country that the equipment model was produced in
        """
        try:
            return self.national_flag_url_pattern\
                .match(self.country_of_production_url)\
                .group('country')\
                .replace('_', ' ')\
                .lower()
        except AttributeError:
            logger.error(
                f"Could not extract country of production from URL:"
                f" {self.country_of_production_url}")
            return None

    def __iter__(self) -> Generator[Case, None, None]:
        """Generates Case objects for the equipment model's entries. Populates each case
        with model-related information.

        :yield: A `Case` object
        """
        model = self.model()
        country_of_production = self.country_of_production()

        for tag in self.tag.find_all('a', recursive=True):
            try:
                for case in CaseParser(tag):
                    # Set equipment model attributes
                    case.model = model
                    case.country_of_production = country_of_production
                    yield case
            except Exception:
                logger.error(f"{str(tag)[:150]}\n{traceback.format_exc()}")
