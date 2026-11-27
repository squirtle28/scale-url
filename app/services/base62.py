"""
Base62 encoding/decoding.

ScaleURL never generates random short codes. Instead, every new URL row
gets a normal auto-incrementing integer primary key from PostgreSQL,
and that integer is encoded into a short, URL-safe string using Base62.
This keeps short codes compact, collision-free by construction (since
they map 1:1 to unique database IDs), and trivially reversible: given a
short code we can decode it straight back to the row's primary key
without an extra lookup table.

Alphabet order matters and must stay fixed once used in production,
since it defines the mapping between integers and strings.
"""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)  # 62
_CHAR_TO_INDEX = {char: index for index, char in enumerate(ALPHABET)}


def encode(number: int) -> str:
    """Encode a non-negative integer into a Base62 string.

    Examples:
        encode(0)  -> "0"
        encode(61) -> "Z"
        encode(62) -> "10"
    """
    if number < 0:
        raise ValueError("Base62 encoding only supports non-negative integers")

    if number == 0:
        return ALPHABET[0]

    digits: list[str] = []
    while number > 0:
        number, remainder = divmod(number, BASE)
        digits.append(ALPHABET[remainder])

    return "".join(reversed(digits))


def decode(code: str) -> int:
    """Decode a Base62 string back into its original integer.

    Raises ValueError if the string contains characters outside the
    Base62 alphabet.
    """
    if not code:
        raise ValueError("Cannot decode an empty string")

    number = 0
    for char in code:
        if char not in _CHAR_TO_INDEX:
            raise ValueError(f"Invalid Base62 character: {char!r}")
        number = number * BASE + _CHAR_TO_INDEX[char]

    return number
