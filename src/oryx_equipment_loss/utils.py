"""
Supporting classes and methods for parsing.
"""
import functools
import inspect
import logging
import string
from datetime import datetime
from typing import Any, Generator, List, Optional, Tuple

ALPHANUMERICS = string.ascii_letters + string.digits


class DummyLogger(logging.Logger):

    def __getattr__(self, *args, **kwds) -> None:
        return


def type_cast(func):
    """Allows function output to be cast to a particular type with the `cast_as` keyword argument.

    :param func:    Function to allow type casting for
    :return:        Function with type casting
    """

    @functools.wraps(func)
    def wrapper(*args, cast_as: Optional[type] = None, **kwds):
        result = func(*args, **kwds)
        if cast_as is None:
            return result
        return cast_as(result)

    return wrapper


@type_cast
def lex_alphabet_items(text: str, alphabet: str) -> Generator[None, None, str]:
    """Iterate a string and yield sections of contiguous characters found in the given alphabet.

    :param text:        Text to iterate
    :param alphabet:    Characters to look for
    :yield:             A section of `text` where all characters are found in `alphabet`

    >>> lex_alphabet_items("one, two three, four")
    >>> ('one', 'two', 'three', 'four')

    >>>  lex_alphabet_items("12, 34a 5b6 7", alphabet=string.digits)
    >>> ('12', '34', '5', '6', '7')
    """
    a, b = 0, 0
    while True:
        # skip those not in alphabet
        while b < len(text) and text[b] not in alphabet:
            b += 1

        # terminate lexing if at end
        if b >= len(text):
            break

        # start of item
        a = b
        while b < len(text) and text[b] in alphabet:
            b += 1

        # add range to items list
        yield text[a:b]

        b += 1


def series_splitter(text: str, delimiter: str = ',') -> Tuple[str]:
    """Splits a string list with or without an Oxford comma (delimiter).

    :param text: Comma separated list
    :return: A tuple of the series's items

    >>> series_splitter("a, b, c, and d")
    >>> ('a', 'b', 'c', 'd')

    >>> series_splitter("a, b, c and d")
    >>> ('a', 'b', 'c', 'd')
    """
    items = [item.strip() for item in text.split(f"{delimiter} ")]

    for conjunction in ('and', 'nor', 'but', 'or',):
        if items[-1].startswith(f"{conjunction} "):
            # Oxford comma case
            items[-1] = items[-1].removeprefix(f"{conjunction} ")
        elif f" {conjunction} " in items[-1]:
            item = items.pop(-1)
            items.extend([_item.strip() for _item in item.split(f" {conjunction} ")])
        else:
            # try another conjunction
            continue
        # conjunction found, go no further
        break
    return tuple(items)


def multisplit(text: str, delimiters: List[str]) -> Tuple[str]:
    """Splits a text with multiple delimiters.

    :param text:        Text to split
    :param delimiters:  Delimiters to use
    :return:            Tuple of strings
    """
    items = []
    delimiter = delimiters[0]
    for item in text.split(delimiter):
        if len(delimiters) > 1:
            items.extend(multisplit(item, delimiters[1:]))
        else:
            items.append(item.strip())
    return tuple(items)


def append_timestamp(name: str, _datetime: Optional[datetime] = None, separator: str = '_') -> str:
    """Appends a timestamp to a string. The timestamp uses descending units so it is sortable by
    datetime.

    :param name:        String to have timestamp appended to
    :param _datetime:   Datetime to use
    :param separator:   Character(s) to separate the `name` and timestamp with, defaults to '_'
    :return:            A name with a timestamp string appended
    """
    if _datetime is None:
        _datetime = datetime.utcnow()
    ts: str = _datetime.strftime(r"%Y-%m-%d_%H-%M-%S")
    return separator.join((name, ts))


def arbitrary_argument_value(func, name: str, *positionals, **keywords) -> Any:
    """Retrieves the value of an argument from an array of positional arguments and dictionary of
    keyword arguments.

    :param func:    Function accepting the arguments
    :param name:    Name of the parameter
    :return:        Value of the parameter
    """
    if name in keywords:
        # param is defined or is VAR_KEYWORD
        return keywords[name]

    # Search undeclared
    sig: inspect.Signature = inspect.signature(func)
    try:
        param = sig.parameters[name]
    except KeyError:
        raise ValueError(f"Parameter '{name}' does not exist in function '{func.__name__}'")

    if param.kind == param.KEYWORD_ONLY:
        # Keyword was not explicitly defined, return default
        return param.default
    elif param.kind == param.POSITIONAL_ONLY:
        i = tuple((_name for _name in sig.parameters.keys())).index(name)
        return positionals[i]
    elif param.kind == param.POSITIONAL_OR_KEYWORD:
        i = tuple((_name for _name in sig.parameters.keys())).index(name)
        if len(positionals) > i:
            return positionals[i]
        # Parameter not defined with positional or keyword, return default
        return param.default
    elif param.kind == param.VAR_POSITIONAL:
        i = tuple((_name for _name in sig.parameters.keys())).index(name)
        # Arbitrary length arguments consume all subsequent positionals
        # Return all positionals following at and after the arbitrary length's position
        return positionals[i:]
    else:
        return param.default
