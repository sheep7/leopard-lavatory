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


def valid_address(address):
    """Check if a given string only contains characters valid for a street address
    or property.
    Note that we are allowing single quotes in the string.

    Args:
        address (str): the address string to check
    Returns:
        bool: True if the address string only contains valid characters, False otherwise.
    """
    if len(address) > 255:
        return False
    # TODO: check if all street and property names in Stockholm pass this regexp (might need ' ?)
    regex = re.compile(
        r'^[a-z0-9äöåéèáàüøæ:.&+ -]{3,255}$',
        re.IGNORECASE)
    return regex.match(address) is not None


def log_safe(string):
    """Turns any string into a quoted string (%xx escaping) to safely write it to log output.

    All characters get %xx quoted except for letters, digits, and these: _.-@
    Also the input will be cut off if longer than 1000 characters. Note that the return value
    can be a string longer than 1000 characters because of the escaping (and the three dots
    for cut strings).
    Args:
        string (str): the untrusted input string
    Returns:
        str: a
    """
    if len(string) > 1000:
        string = string[:1000] + '...'

    safe_string = quote(string, safe='@')

    return safe_string
