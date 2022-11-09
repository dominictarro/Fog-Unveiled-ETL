"""
Oryx equipment losses parser.

The page is structured roughly like this

<article>
    ...
    <div>
        <!-- info about the article -->
    </div>
    ...
    <div>
        <h3>
            <!-- asset category and its summary statistics -->
        </h3>
        <ul>
            <li>
                <!-- asset model and its supporting data -->
                <a>
                    <!-- confirmed equipment losses -->
                    <!-- these are just image/video URLs, there may be more than one loss
                    per <a> tag -->
                </a>
                <a>
                    <!-- confirmed equipment losses -->
                </a>
                ...
            </li>
            ...
        </ul>
        <!-- repeat the pattern of h3 tags followed by respective ul tags -->
        ...
    </div>
    ...
</article>

So the parser is structured to generate standardized confirmed losses like so

for asset category
    for asset model
        for confirmed loss <a> tag
            for confirmed loss
                yield case


Confirmed losses have several required fields

 - Asset Category:          a text descriptor of the asset (e.g. tanks, infantry transports, etc.)

     - lowercase
     - may include non alphanumerics
     - found in the <h3> tag

 - Model:                   a text descriptor of the machine's model (e.g. T-64BV)

     - uses exact spelling as seen on the website
     - found in the <li> tag

 - Country of Loss:         a text label of the country that the asset belonged to

     - lowercase
     - set by the parsing function

 - Country of production:   a text label of the country that produces or produced the asset

     - lowercase
     - derived from the flag <img>'s source url (Wikimedia origin)

 - Model case ID:           an integer ID assigned to the case

     - every asset model starts at 1 (e.g. T-64BV and T-62M both have one case where its id=1)
     - on the website, can find multiple in the same <a> tag
     - found in the <a> tag

 - Confirmation URL:        a url to the visual confirmation (image, video)

     - may not point directly to the media (e.g. to a tweet that has an image/video)
     - found in the <a> tag

 - Status:                  a list of states the asset is or was in (e.g. damaged, captured)

     - some have multiple (e.g. damaged and captured)
     - all elements of the list are lowercase strings
     - found in the <a> tag


Optional fields include

 - Cause:                   a list of causes related to the asset's status

     - Many point to other weapons systems
     - Some have multiple (e.g. damaged and captured)
     - All elements of the list are lowercase strings
     - found in the <a> tag


In the end, every document should look something like

    {
        "model_case_id": 2,
        "status": [
            "damaged"
        ],
        "confirmation_url": "https://i.postimg.cc/yYx8J43v/Screenshot-8073.png",
        "cause": [
            "Bayraktar TB2"
        ],
        "asset_category": "towed artillery",
        "model": "152mm 2A65 Msta-B howitzer",
        "country_of_loss": "russia",
        "country_of_production": "soviet union"
    }

    or

    {
        "model_case_id": 6,
        "status": [
            "destroyed"
        ],
        "confirmation_url": "https://postimg.cc/hJQ6678b",
        "cause": [
            "Bayraktar TB2",
            "artillery"
        ],
        "asset_category": "helicopters",
        "model": "Mi-8 transport helicopter",
        "country_of_loss": "russia",
        "country_of_production": "russia"
    }

    or

    {
        "model_case_id": 7,
        "status": [
            "abandoned",
            "destroyed"
        ],
        "confirmation_url": "https://i.postimg.cc/ncL87Pvg/65.png",
        "cause": null,
        "asset_category": "helicopters",
        "model": "Mi-8 transport helicopter",
        "country_of_loss": "russia",
        "country_of_production": "russia"
    }


Limitations of the data

    While the Oryx article is consistently formatted quite well, it isn't perfect. There are some
    issues with

        1. the case information being divided between <a> tags
        2. Unprecedented status values

    There are others, but these are a few that I have spotted. Fortunately, they are not frequent
    and the error between Oryx's stated totals and the scraped totals is insignificant.


Extras

 - Russian Equipment Losses
     - https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html

 - Ukrainian Equipment Losses
     - https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-ukrainian.html


"""
from __future__ import annotations
import logging
import re
import traceback
from dataclasses import asdict
from typing import TYPE_CHECKING, Any, Dict, Generator, Tuple

import bs4

from src.oryx_equipment_loss.transform.asset_category import AssetCategoryParser
from src.oryx_equipment_loss.transform.correction import autoid, set_attachments
from src.oryx_equipment_loss.validation import default_rulebook
from src.rulebook import validate

if TYPE_CHECKING:
    from src.oryx_equipment_loss.case import Case


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class OryxParser:

    def __init__(self, tag: bs4.Tag) -> None:
        self.tag: bs4.Tag = tag

    @property
    def sections(self) -> bs4.ResultSet:
        return self.tag.find_all('div', recursive=False)

    category_header_regex: re.Pattern = re.compile(
        r"^.+\(\d+, .+\)\s*$", flags=re.DOTALL)

    def categories(self, country_of_loss: str) -> Tuple[bs4.Tag]:
        categories = []

        data_section: bs4.Tag
        if country_of_loss == 'ukraine':
            # The Ukraine page is broken into 2 sections instead of 8
            data_section = self.sections[1]
        elif country_of_loss == 'russia':
            data_section = self.sections[7]
        else:
            raise ValueError(f"Not a valid belligerent: {country_of_loss}")

        for tag in data_section.find_all('h3'):
            if self.category_header_regex.match(tag.text) is not None:
                categories.append(tag)
        return tuple(categories)

    @validate(rulebook=default_rulebook, logger=logger)
    @autoid
    @set_attachments
    def cases(self, country_of_loss: str) -> Generator[Case, None, None]:
        """Generates Case objects for the Oryx page.

        :yield: A `Case` object
        """
        for tag in self.categories(country_of_loss):
            try:
                for case in AssetCategoryParser(tag):
                    case.country_of_loss = country_of_loss
                    yield case
            except Exception:
                logger.error(f"{str(tag)[:150]}\n{traceback.format_exc()}")

    @classmethod
    def from_bytes(cls, _bytes: bytes) -> OryxParser:
        soup: bs4.BeautifulSoup = bs4.BeautifulSoup(_bytes, features="lxml")
        return OryxParser.from_soup(soup)

    @classmethod
    def from_soup(cls, soup: bs4.BeautifulSoup) -> OryxParser:
        article = soup.find(attrs={'class': 'post-body entry-content', 'itemprop': 'articleBody'})
        return OryxParser(article)


OryxResult = Generator[Dict[str, Any], None, None]


def parse(belligerent: str, _bytes: bytes) -> OryxResult:
    """Generator for structuring visually confirmed cases of equipment loss on the belligerent's
    Oryx page.

    :param belligerent: Name of the belligerent whose page is being structured
    :param _bytes:      Page in bytes format
    :yield:             Visually confirmed equipment losses in dictionary format

    Additional arguments to the extractor should be passed as keyword arguments.
    """
    parser: OryxParser = OryxParser.from_bytes(_bytes)
    for case in parser.cases(belligerent):
        yield asdict(case)
