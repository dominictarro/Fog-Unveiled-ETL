import logging
import random
import string
from typing import Any, Callable, Dict, Generator, Optional, Set


class RuleBook:

    def __init__(self) -> None:
        self.rules: Set[Callable[[Any], None]] = set()

    def __call__(self, func):
        """Wrapper to add a function to the RuleBook.

        :param func: Rule function to add to the RuleBook
        """
        self.rules.add(func)
        return func

    def validate(self, o: Any):
        for rule in self.rules:
            rule(o)


def validate(rulebook: RuleBook, logger: Optional[logging.Logger] = None):
    """Decorates a generator to validate objects. Failed objects are not yielded.

    Can use a custom RuleBook and logger for checking and recording cases.

    :param rulebook: Rules to enforce for the case, defaults to rulebook
    :param logger: Logger to output failed case debug and summaries, defaults to None
    :return: A generator that only yields cases that meet the requirements
    :yield: A valid object
    """
    if logger is None:
        logger_name = f"{__file__}-{''.join(random.choices(string.ascii_letters + string.digits, k=6))}"
        logger = logging.getLogger(logger_name)

    def decorator(func):
        def wrapper(*args, **kwds) -> Generator[Any, None, None]:
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
