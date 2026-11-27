"""Unit tests for the Base62 encode/decode implementation."""

import pytest

from app.services.base62 import decode, encode


def test_encode_zero() -> None:
    assert encode(0) == "0"


def test_encode_61_is_last_alphabet_char() -> None:
    # 61 is the last index in the 62-character alphabet ("...XYZ").
    assert encode(61) == "Z"


def test_encode_62_rolls_over_to_two_digits() -> None:
    # 62 is exactly one full "rotation" of the alphabet -> "10" in base62.
    assert encode(62) == "10"


@pytest.mark.parametrize(
    "number",
    [1, 10, 100, 1_000, 123_456, 9_999_999, 2**31, 2**53],
)
def test_encode_decode_round_trip(number: int) -> None:
    assert decode(encode(number)) == number


def test_encode_negative_raises() -> None:
    with pytest.raises(ValueError):
        encode(-1)


def test_decode_empty_string_raises() -> None:
    with pytest.raises(ValueError):
        decode("")


def test_decode_invalid_character_raises() -> None:
    with pytest.raises(ValueError):
        decode("abc!")


def test_encode_is_deterministic() -> None:
    assert encode(555) == encode(555)


def test_larger_numbers_produce_longer_codes() -> None:
    assert len(encode(62**3)) > len(encode(62**2))
