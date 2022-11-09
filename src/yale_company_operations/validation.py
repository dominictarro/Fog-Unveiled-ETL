"""
Validation module to enforce logic or formatting within Company documents.
"""
from __future__ import annotations

from src.yale_company_operations.company import Company
from src.rulebook import RuleBook


default_rulebook = RuleBook()


@default_rulebook
def rule_name(company: Company):
    """Rules for Company.name attribute.

    :param company:         Company to validate
    :raises AssertionError: Failed validation
    """
    if not isinstance(company.name, str):
        raise AssertionError("Company.name is not a string")


@default_rulebook
def rule_action(company: Company):
    if not isinstance(company.action, str):
        raise AssertionError("Company.action is not a string")


@default_rulebook
def rule_industry(company: Company):
    if not isinstance(company.industry, str):
        raise AssertionError("Company.industry is not a string")


@default_rulebook
def rule_country(company: Company):
    if not isinstance(company.country, str):
        raise AssertionError("Company.country is not a string")


@default_rulebook
def rule_grade(company: Company):
    if not isinstance(company.grade, str):
        raise AssertionError("Company.grade is not a string")
    if company.grade not in ('A', 'B', 'C', 'D', 'F'):
        raise AssertionError(f"Company.grade is not recognized")


@default_rulebook
def rule_status(company: Company):
    if not isinstance(company.status, str):
        raise AssertionError("Company.status is not a string")


@default_rulebook
def rule_description(company: Company):
    if not isinstance(company.description, str):
        raise AssertionError("Company.description is not a string")

