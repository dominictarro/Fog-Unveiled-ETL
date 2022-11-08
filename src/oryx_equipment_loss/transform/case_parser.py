"""
Case parser for an entry to an Oryx equipment model.
"""
from __future__ import annotations
import logging
import re
import traceback
from typing import TYPE_CHECKING, Generator, Iterable, Optional, Tuple

from src.oryx_equipment_loss.case import Case
from src.oryx_equipment_loss.utils import multisplit, series_splitter

if TYPE_CHECKING:
    import bs4


logger = logging.getLogger(__name__)


class CaseParser:

    def __init__(self, tag: bs4.Tag) -> None:
        self.tag: bs4.Tag = tag

    @property
    def confirmation_url(self) -> Optional[str]:
        return self.tag.attrs.get('href')

    def text(self) -> str:
        """Gets the text contents of the case entry.

        :return: Text contents of the case entry

        Entries have two components:

        1. the case id for the model
        2. the asset's status

        Some have a third component

        3. the cause of status

        Generally speaking, the entries are formatted like:

            - '{ids}, {statuses}'
            - '{ids}, with {causes}, {statuses}'
            - '{ids}, {statuses} by {causes}'

        """
        return self.tag.text.strip('()')

    with_cause_rgx = re.compile(r"^with (.+?),", flags=re.DOTALL)
    by_cause_rgx = re.compile(r".*by (.+)$", flags=re.DOTALL)

    def causes(self, text: Optional[str] = None) -> Optional[Tuple[str]]:
        """Extracts the causes from the case text.

        :param text: Case's text contents, defaults to None
        :return: Tuple of the causes or `None` if none are found
        """
        try:
            if ' with ' in text:
                rgx = self.with_cause_rgx
            elif ' by ' in text:
                rgx = self.by_cause_rgx
            else:
                return None
            match = rgx.match(text).group(1)
            return tuple(series_splitter(match))
        except AttributeError:
            # No match
            return None

    def ids(self, items: Optional[Iterable[str]] = None) -> Tuple[int]:
        """Extracts the ids from the case's items list.

        :param items: Series-split items from the case's text, defaults to None
        :return: Tuple of the case's ids
        """
        ids = set()
        for item in items:
            if item.isnumeric():
                ids.add(int(item))
            else:
                # End of IDs section will be the first non-integer
                break
        return tuple(ids)

    STATUS_OPTIONS = (
        'abandoned',
        'captured',
        'damaged',
        'destroyed',
        'raised',
        'scuttled',
        'stripped',
        'sunk',
        'beyond economical repair'
    )

    def statuses(self, text: Optional[str] = None) -> Tuple[str]:
        """Extracts the statuses from the case's text.

        :param text: Case's text contents, defaults to None
        :return: Tuple of the case's statuses
        """
        statuses = []
        for status in self.STATUS_OPTIONS:
            if status in text:
                statuses.append(status)
        return tuple(statuses)

    def __iter__(self) -> Generator[Case, None, None]:
        """Generates Case objects for every case in the entry.

        :yield: A Case object
        """
        text = self.text()
        # Split instead of lex so the end of the IDs section can be detected
        items = multisplit(text, (',', ' and ', ' or '))
        for _id in self.ids(items):
            try:
                statuses = self.statuses(text)
                causes = self.causes(text)
                yield Case(
                    model_case_id=_id,
                    asset_status=statuses,
                    confirmation_url=self.confirmation_url,
                    cause=causes)
            except Exception:
                logger.error(f"model_case_id={_id}\n{traceback.format_exc()}")
