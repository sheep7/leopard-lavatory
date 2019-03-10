"""Helper functions used by other modules."""

import re
from secrets import token_urlsafe
from urllib.parse import quote

TOKEN_BYTES = 42


def create_token():
    """Create a new url safe, high-entropy string that can be used as access token for for
    example confirm, delete or modify operations.

    Returns:
        str: url safe, cryptographically secure token
    """
    return token_urlsafe(nbytes=TOKEN_BYTES)


def valid_email(email):
    """Checks if the given string is a valid email address according to the W3C HTML5 definition.
    https://www.w3.org/TR/html5/forms.html#valid-e-mail-address

    Note that this allows single quotes ', the ` and more special characters in the email string.

    Args:
        email (str): string to check
    Returns:
        bool: True if the input is a valid email address, False otherwise.
    """
    # max length of a valid mail address is 254 characters
    # https://www.rfc-editor.org/errata_search.php?rfc=3696&eid=1690
    if len(email) > 254:
        return False
    # regexp from https://www.w3.org/TR/html5/forms.html#valid-e-mail-address
    regex = re.compile(
        r'^[a-zA-Z0-9.!#$%&\'*+\\/=?^_`{|}~-]+@'
        r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?'
        r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$')
    return regex.match(email) is not None


def valid_address(address, min_len=3):
    """Check if a given string only contains characters valid for a street address or property, is at least `min_len`
    characters long and not longer than 255
    not too long

    Args:
        address (str): the address string to check
        min_len (int): the required minimum length of the address string
    Returns:
        bool: True if the address string only contains valid characters and is of correct length, False otherwise.
    """
    if not isinstance(address, str):
        return False
    if not min_len <= len(address) <= 256:
        return False
    # TODO: check if all street and property names in Stockholm pass this regexp (might need ' ?)
    regex = re.compile(
        r'^[a-z0-9äöåéèáàüøæ:.&+ -]*$',
        re.IGNORECASE)
    return regex.match(address) is not None


def log_safe(string, max_len=300):
    """Turns any string into a quoted string (%xx escaping) to safely write it to log output.

    All characters get %xx quoted except for letters, digits, and these: _.-@
    Also the input will be cut off if longer than `max_len` characters. Note that the return value
    can be a string longer than `max_len` characters because of the escaping (and the three dots
    for cut strings).
    Args:
        string (str): the untrusted input string
        max_len (int): maximum allowed length of the input (longer will be cut)
    Returns:
        str: a string with only letters, digits, and %_.-@
    """
    if len(string) > max_len:
        string = string[:max_len] + '...'

    safe_string = quote(string, safe='@')

    return safe_string


def all_prefixes(full_string):
    """Yield all prefixes of a given string.

    So all_prefixes('abc') will yield 'a', 'ab', and 'abc'.
    Args:
        full_string (str): the complete string
    Yields:
        str: all prefixes of full_string, including full_string
    """
    for i in range(len(full_string)):
        yield full_string[:i+1]


def all_substrings(full_string):
    """Yield all substrings of a given string.

    So all_prefixes('abc') will yield 'a', 'b', 'c', 'ab', 'bc', and 'abc'.
    Args:
        full_string (str): the complete string
    Yields:
        str: all substrings of full_string, including full_string
    """
    for i in range(len(full_string)):
        for j in range(i, len(full_string)):
            yield full_string[i:j+1]

