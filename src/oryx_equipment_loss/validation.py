"""
Validation module to enforce logic or formatting within Case documents.
"""
from __future__ import annotations
import logging
import random
import string
from typing import Callable, Dict, Generator, Optional, Set

try:
    from src.oryx_equipment_loss.case import Case
except ImportError:
    from case import Case


class RuleBook:

    def __init__(self) -> None:
        self.rules: Set[Callable[[Case], None]] = set()

    def __call__(self, func):
        """Wrapper to add a function to the RuleBook.

        :param func: Rule function to add to the RuleBook
        """
        self.rules.add(func)
        return func

    def validate(self, case: Case):
        for rule in self.rules:
            rule(case)


default_rulebook = RuleBook()


@default_rulebook
def rule_model_case_id(case: Case):
    """Rules for the Case.model_case_id attribute.

    :param case:            Case to validate
    :raises AssertionError: Failed validation
    """
    if not isinstance(case.model_case_id, int):
        raise AssertionError("Case.model_case_id is not an integer")
    if case.model_case_id < 1:
        raise AssertionError("Case.model_case_id is less than 1")


@default_rulebook
def rule_status(case: Case):
    """Rules for the Case.status attribute.

    :param case:            Case to validate
    :raises AssertionError: Failed validation
    """
    if not isinstance(case.asset_status, tuple):
        raise AssertionError("Case.status is not a tuple")
    if len(case.asset_status) == 0:
        raise AssertionError("Case.status is empty")
    if any(len(status) == 0 for status in case.asset_status):
        raise AssertionError("Case.status contains an empty element")
    if not all(isinstance(status, str) for status in case.asset_status):
        raise AssertionError("Case.status element is not a string")


@default_rulebook
def rule_confirmation_url(case: Case):
    """Rules for the Case.confirmation_url attribute.

    :param case:            Case to validate
    :raises AssertionError: Failed validation
    """
    if not isinstance(case.confirmation_url, str):
        raise AssertionError("Case.confirmation_url is not a string")
    if len(case.confirmation_url) == 0:
        raise AssertionError("Case.confirmation_url is an empty string")


@default_rulebook
def rule_cause(case: Case):
    """Rules for the Case.cause attribute.

    :param case:            Case to validate
    :raises AssertionError: Failed validation
    """
    if case.cause is None:
        return
    if not isinstance(case.cause, tuple):
        raise AssertionError("Case.cause is not a tuple")
    if len(case.cause) == 0:
        raise AssertionError("Case.cause is an empty tuple")
    if any(len(cause) == 0 for cause in case.cause):
        raise AssertionError("Case.cause contains an empty element")


@default_rulebook
def rule_asset_category(case: Case):
    """Rules for the Case.asset_category attribute.

    :param case:            Case to validate
    :raises AssertionError: Failed validation
    """
    if not isinstance(case.asset_category, str):
        raise AssertionError("Case.asset_category is not a string")
    if len(case.asset_category) == 0:
        raise AssertionError("Case.asset_category is an empty string")
    if not case.asset_category.islower():
        raise AssertionError("Case.asset_category is not lowercase")


@default_rulebook
def rule_model(case: Case):
    """Rules for the Case.model attribute.

    :param case:            Case to validate
    :raises AssertionError: Failed validation
    """
    if not isinstance(case.model, str):
        raise AssertionError("Case.model is not a string")
    if len(case.model) == 0:
        raise AssertionError("Case.model is an empty string")


@default_rulebook
def rule_country_of_loss(case: Case):
    """Rules for the Case.country_of_loss attribute.

    :param case:            Case to validate
    :raises AssertionError: Failed validation
    """
    if not isinstance(case.country_of_loss, str):
        raise AssertionError("Case.country_of_loss is not a string")
    if len(case.country_of_loss) == 0:
        raise AssertionError("Case.country_of_loss is an empty string")
    if not case.country_of_loss.islower():
        raise AssertionError("Case.country_of_loss is not lowercase")


@default_rulebook
def rule_country_of_production(case: Case):
    """Rules for the Case.country_of_production attribute.

    :param case:            Case to validate
    :raises AssertionError: Failed validation
    """
    if not isinstance(case.country_of_production, str):
        raise AssertionError("Case.country_of_production is not a string")
    if len(case.country_of_production) == 0:
        raise AssertionError("Case.country_of_production is an empty string")
    if not case.country_of_production.islower():
        raise AssertionError("Case.country_of_production is not lowercase")


@default_rulebook
def rule_attachment(case: Case):
    """Rules for the Case.attachment attribute.

    :param case:            Case to validate
    :raises AssertionError: Failed validation
    """
    if case.attachment is None:
        return
    if not isinstance(case.attachment, str):
        raise AssertionError("Case.attachment is not null or string")


def validate(rulebook: RuleBook = default_rulebook, logger: Optional[logging.Logger] = None):
    """Decorates a generator to validate Case objects. Failed cases are not yielded.

    Can use a custom RuleBook and logger for checking and recording cases.

    :param rulebook: Rules to enforce for the case, defaults to rulebook
    :param logger: Logger to output failed case debug and summaries, defaults to None
    :return: A generator that only yields cases that meet the requirements
    :yield: A valid case
    """
    if logger is None:
        logger_name = f"{__file__}-{''.join(random.choices(string.ascii_letters + string.digits, k=6))}"
        logger = logging.getLogger(logger_name)

    def decorator(func):
        def wrapper(*args, **kwds) -> Generator[Case, None, None]:
            reason_tracker: Dict[str, int] = {}
            for case in func(*args, **kwds):
                try:
                    rulebook.validate(case)
                except AssertionError as e:
                    # Log failed validation
                    _e = str(e)
                    msg = f"{case} failed validation: {_e}"
                    logger.debug(msg)

                    # Track reason for failure
                    if _e not in reason_tracker:
                        reason_tracker[_e] = 0
                    reason_tracker[str(e)] += 1
                    continue
                yield case

            reason_tracker['total'] = sum(reason_tracker.values())
            pairs = (f'"{k}"={v}' for k, v in reason_tracker.items())
            msg = f"Validation Tracker: {' '.join(pairs)}"
            if reason_tracker['total'] > 0:
                logger.error(msg)
        return wrapper

    return decorator
