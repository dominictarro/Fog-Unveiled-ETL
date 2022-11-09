"""
Container for company operations data.
"""
import dataclasses


@dataclasses.dataclass
class Company:
    name: str
    action: str
    industry: str
    country: str
    grade: str
    status: str
    description: str

