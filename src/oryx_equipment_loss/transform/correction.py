"""
Corrections to apply to cases in the pipeline.

"""
from __future__ import annotations
import functools
import logging
import re
import traceback
from copy import copy
from typing import TYPE_CHECKING, Any, Callable, Generator

if TYPE_CHECKING:
    from src.oryx_equipment_loss.case import Case
    CaseGenerator = Callable[[Any], Generator[Case, None, None]]

logger = logging.getLogger(__name__)


def autoid(func: CaseGenerator):
    """Auto increment the Case.case_model_id according to the model's count.

    :param func: Generator function to auto increment IDs from
    """

    @functools.wraps(func)
    def wrapper(*args, **kwds):
        model_counts = {}
        for case in func(*args, **kwds):
            case: Case
            if case.model not in model_counts:
                model_counts[case.model] = 1
            case.model_case_id = model_counts[case.model]
            yield case
            model_counts[case.model] += 1

    return wrapper


def set_attachments(func: CaseGenerator):
    """Remove equipment names from Case.model set Case.attachment with them.

    :param func: Generator function to set attachments from
    """
    rgx: re.Pattern = re.compile(
        r"^(?P<model>.+?)"
        r"(?P<clause_start> with )"
        r"(?P<attachment>.*)$")

    @functools.wraps(func)
    def wrapper(*args, **kwds):
        for case in func(*args, **kwds):
            match = rgx.match(case.model)
            if match is not None:
                try:
                    _case = copy(case)
                    _case.model = match.group('model')
                    _case.attachment = match.group('attachment')
                    case = _case
                except Exception:
                    logger.debug(
                        f"Failed to correct attachment in {case}\n{traceback.format_exc()}")
            yield case

    return wrapper
