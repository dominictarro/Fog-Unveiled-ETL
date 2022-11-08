"""
Case parser for a listing of an Oryx asset category.
"""
from __future__ import annotations
import logging
import re
import traceback
from typing import TYPE_CHECKING, Generator
from src.oryx_equipment_loss.transform.equipment_model import EquipmentModelParser

if TYPE_CHECKING:
    from src.oryx_equipment_loss.case import Case
    import bs4


logger = logging.getLogger(__name__)


class AssetCategoryParser:

    def __init__(self, tag: bs4.Tag) -> None:
        self.tag: bs4.Tag = tag

    asset_category_pattern: re.Pattern = re.compile(r"^(?P<asset_category>.+?)\s\(\d+,.*")

    def asset_category(self) -> str:
        """Gets the label of the asset category.

        :return: Lowercase label of the asset cateogry.
        """
        h3 = self.tag.text.strip()
        match = self.asset_category_pattern.match(h3)
        return match.group('asset_category')\
            .strip()\
            .lower()

    def __iter__(self) -> Generator[Case, None, None]:
        """Generates Case objects for the asset category's equipment models. Populates each case
        with asset-related information.

        :yield: A `Case` object
        """
        asset_category = self.asset_category()
        ul_tag: bs4.Tag = self.tag.find_next('ul')
        for tag in ul_tag.find_all('li', recursive=False):
            try:
                for case in EquipmentModelParser(tag):
                    # Set asset category attributes
                    case.asset_category = asset_category
                    yield case
            except Exception:
                logger.error(f"{str(tag)[:150]}\n{traceback.format_exc()}")
