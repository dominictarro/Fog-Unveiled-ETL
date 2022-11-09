"""
Yale company operations parser.

The page is structured roughly like this.

<section>
    <div>
        <div>
            <div>
                <h3>
                    <!-- section title -->
                </h3>
            </div>
            <div>
                <!-- operating status content section -->
                <div>
                    <p> <!-- "Section description (n Companies) (Grade: X)" --></p>
                    ...
                </div>
                <table>
                    <thead>
                        <!-- column labels -->
                        <tr>
                            <th></th>
                            ...
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        <!-- rows of company statuses -->
                        <tr>
                            <th></th>
                            ...
                            <th></th>
                        </tr>
                        ...
                        <tr>
                            <th></th>
                            ...
                            <th></th>
                        </tr>
                    </tbody>
                </table>
            </div>
            ...
            <!--- more operating statuses -->
        </div>
    </div>
</section>

The parser is structured to generate company status objects like

for status section
    for company status
        yield company

Company statuses require the following fields

 - name:        a text title for the company

    - found in the <th> rows of the section's <tbody>

 - action:      a text description of the company's actions

    - found in the <th> rows of the section's <tbody>

 - industry:    a text label for the company's economic industry

    - found in the <th> rows of the section's <tbody>

 - country:     a text label of the country

    - found in the <th> rows of the section's <tbody>

 - grade:       a text label given by the Yale team describing their opinion of the company's actions

    - found in the <p> of the initial <div> of the 'operating status content' section

 - status:      a text label for the company's operational status in Russia

    - found in the <h3> of the first <div> of the section

 - description: a text definition of the status as defined by the Yale team

    - found in the <p> of the initial <div> of the 'operating status content' section


In the end, every document should look something like

    {
        "name": ""
    }
"""
import re
from dataclasses import asdict
from typing import Dict, Generator, List, Optional

import bs4
from prefect import task
from prefect.logging import get_run_logger

from src.rulebook import validate
from src.yale_company_operations.company import Company
from src.yale_company_operations.validation import default_rulebook


class StatusSection:
    """_summary_

    :return: _description_
    :yield: _description_
    """
    _definition_pattern = re.compile(r"^(?P<definition>.+) \(\d+ Companies\) \(Grade: (?P<grade>\w)\)$")
    descriptions_by_grade = {}

    def __init__(self, tree: bs4.Tag) -> None:
        self.tree: bs4.Tag = tree
        self._grade: str = self.grade()
        self._status: str = self.status()
        self._description: str = self.description()
        StatusSection.descriptions_by_grade[self._grade] = {'status': self._status, 'description': self._description}
    
    def status(self) -> Optional[str]:
        """Generic status of companies in the section.
        """
        name: Optional[bs4.Tag] = self.tree.find('h3', recursive=True)
        if name is None:
            return
        return name.text.strip()

    def description(self) -> Optional[str]:
        """Given description for companies in this status section.
        """
        body = self.tree.find('div', attrs={'class': "text-long"}, recursive=True)
        if body is None:
            return
        p = body.find('p', recursive=True)
        text = p.text.strip()
        match = self._definition_pattern.match(text)
        if match is None:
            return
        return match.group('definition')

    def grade(self) -> Optional[str]:
        """Assigned grade on a scale of A-F.
        """
        body = self.tree.find('div', attrs={'class': "text-long"}, recursive=True)
        if body is None:
            return
        p = body.find('p', recursive=True)
        text = p.text.strip()
        match = self._definition_pattern.match(text)
        if match is None:
            return
        return match.group('grade')


    def companies(self) -> Generator[Company, None, None]:
        """Generator for structuring rows in the section.

        :yield: Company instance
        """
        try:
            table = self.tree.find('table', attrs={'class': "responsive-enabled"})
            thead = table.find('thead')

            # Column name lookup by position in row
            col_no_to_header = {
                i: th.text for i, th in enumerate(thead.find_all('th'))
            }

            tbody = table.find('tbody')
        except Exception:
            # TODO logging and handling
            return

        # Iterate rows in the body of the table
        for tr in tbody.find_all('tr'):
            tr: bs4.Tag
            row = {}
            # Iterate elements in a row
            for i, td in enumerate(tr.find_all('td')):
                # Get column name and set
                col = col_no_to_header[i]
                row[col] = td.text.strip()

            # Expected structure, validate down the pipeline
            company = Company(
                name=row.get('Name'),
                action=row.get('Action'),
                industry=row.get('Industry'),
                country=row.get('Country'),
                grade=self._grade,
                status=self._status,
                description=self._description
            )

            yield company


class YaleParser:

    def __init__(self, soup: bs4.Tag) -> None:
        self.soup: bs4.Tag = soup
    
    def sections(self) -> Generator[bs4.Tag, None, None]:
        """Generator for the sections of the page.

        :yield: Beautiful Soup tags containing all section contents
        """
        for section_id in ('diggingin', 'buyingtime', 'scalingback', 'suspension', 'withdrawal'):
            try:
                section = self.soup.find('section', attrs={'id': section_id})
                yield section.find(attrs={'class': 'layout__region layout__region--one'})
            except Exception:
                # TODO logging and handling
                continue

    def companies(self) -> Generator[Company, None, None]:
        """Gets all companies from all status sections.

        :yield: Company dataclasses
        """
        for tree in self.sections():
            yield from StatusSection(tree).companies()

    def parse(self) -> List[Dict[str, str]]:
        """Gets all companies from all status sections as dictionaries.
        """
        return [asdict(company) for company in self.companies()]


@task
def parse_page(page: bytes) -> List[Dict[str, str]]:
    """Parses all company statuses from the given page.

    :param page:    Web page in bytes form
    :return:        All valid company statuses found in the document
    """
    logger = get_run_logger()

    soup: bs4.BeautifulSoup = bs4.BeautifulSoup(page, features="lxml")
    parser = YaleParser(soup)

    # Add validation
    parser.companies = validate(rulebook=default_rulebook, logger=logger)(parser.companies)
    return parser.parse()
