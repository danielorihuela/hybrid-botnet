import os
import pytest

from botnet_p2p.message import (
    structure_msg,
    sign_structured_msg,
    __get_msg_and_type,
    __append,
    signed_by_master,
    __get_signed_hash,
    breakdown_msg,
)
from botnet_p2p import (
    ENCODING,
    MSG_SEPARATOR,
)

public_key_path = os.path.join(os.getcwd(), "tests/auxiliar_files/public_key")
private_key_path = os.path.join(os.getcwd(), "tests/auxiliar_files/private_key")


def test_structure_msg_default_values():
    sample_msg_info = {
        "msg_type": 1,
        "msg": "hello",
    }

    expected_output = f"0{MSG_SEPARATOR}default{MSG_SEPARATOR}1{MSG_SEPARATOR}hello".encode(
        ENCODING
    )
    actual_output = structure_msg(sample_msg_info)

    assert isinstance(actual_output, bytes)
    assert actual_output == expected_output


def test_structure_msg():
    sample_msg_info = {
        "num_anonymizers": 10,
        "onion": "this one",
        "msg_type": 1,
        "msg": "hello",
    }

    expected_output = (
        "10"
        + MSG_SEPARATOR
        + "this one"
        + MSG_SEPARATOR
        + "1"
        + MSG_SEPARATOR
        + "hello"
    ).encode(ENCODING)
    actual_output = structure_msg(sample_msg_info)

    assert isinstance(actual_output, bytes)
    assert actual_output == expected_output


def test_structure_msg_with_sign():
    sample_msg_info = {
        "num_anonymizers": 10,
        "onion": "this one",
        "msg_type": 1,
        "msg": "hello",
        "sign": "this sign",
    }

    expected_output = (
        "10"
        + MSG_SEPARATOR
        + "this one"
        + MSG_SEPARATOR
        + "1"
        + MSG_SEPARATOR
        + "hello"
        + MSG_SEPARATOR
        + "this sign"
    ).encode(ENCODING)
    actual_output = structure_msg(sample_msg_info)

    assert isinstance(actual_output, bytes)
    assert actual_output == expected_output


def test_sign_structured_msg():
    sample_msg_info = {
        "num_anonymizers": 10,
        "onion": "this one",
        "msg_type": 1,
        "msg": "hello",
    }
    sample_structured_msg = structure_msg(sample_msg_info)

    expected_output = (
        "10"
        + MSG_SEPARATOR
        + "this one"
        + MSG_SEPARATOR
        + "1"
        + MSG_SEPARATOR
        + "hello"
        + MSG_SEPARATOR
    ).encode(ENCODING)
    actual_output = sign_structured_msg(sample_structured_msg, private_key_path)

    assert isinstance(actual_output, bytes)
    assert actual_output.startswith(expected_output)


def test_get_msg_and_type_from_unsigned_msg():
    unsigned_msg = b"10<<onion<<3<<hello"

    expected_output = b"3<<hello"
    actual_output = __get_msg_and_type(unsigned_msg)

    assert actual_output == expected_output


def test_get_msg_and_type_from_signed_msg():
    signed_msg = b"10<<onion<<2<<hello<<sign"

    expected_output = b"2<<hello"
    actual_output = __get_msg_and_type(signed_msg)

    assert actual_output == expected_output


def test_append():
    expected_output = b"to that<<this"
    actual_output = __append(b"this", b"to that")

    assert actual_output == expected_output


def test_signed_by_master():
    sample_msg_info = {
        "num_anonymizers": 2,
        "onion": "this one",
        "msg_type": 1,
        "msg": "hello",
    }
    structured_msg = structure_msg(sample_msg_info)
    signed_structured_msg = sign_structured_msg(structured_msg, private_key_path)
    sign = signed_structured_msg.split(MSG_SEPARATOR.encode(ENCODING))[-1]
    decoded_sign = sign.decode(ENCODING)
    sample_msg_info_with_sign = {
        "num_anonymizers": 10,
        "onion": "this one",
        "msg_type": 1,
        "msg": "hello",
        "sign": decoded_sign,
    }
    signed_msg = structure_msg(sample_msg_info_with_sign)

    expected_output = True
    actual_output = signed_by_master(signed_msg, public_key_path)

    assert actual_output == expected_output


def test_get_signed_hash():
    signed_msg = b"10<<onion<<2<<hello<<sign"

    expected_output = b"sign"
    actual_output = __get_signed_hash(signed_msg)

    assert actual_output == expected_output

@pytest.mark.parametrize("num_anonymizers, msg_type", [(10, "a"), ("a", 2), ("a", "b")])
def test_breakdown_structure_incorrect_numbers(num_anonymizers, msg_type):
    sample_input = f"{num_anonymizers}<<this one<<{msg_type}<<hello<<this other"
    sample_input_encoded = sample_input.encode(ENCODING)

    expected_output = {
        "num_anonymizers": -1,
        "onion": "this one",
        "msg_type": -1,
        "msg": "hello",
        "sign": "this other",
    }
    actual_output = breakdown_msg(sample_input_encoded)

    assert isinstance(actual_output, dict)
    assert expected_output == actual_output


def test_breakdown_structure():
    sample_input = "10<<this one<<1<<hello<<this other"
    sample_input_encoded = sample_input.encode(ENCODING)

    expected_output = {
        "num_anonymizers": 10,
        "onion": "this one",
        "msg_type": 1,
        "msg": "hello",
        "sign": "this other",
    }
    actual_output = breakdown_msg(sample_input_encoded)

    assert isinstance(actual_output, dict)
    assert expected_output == actual_output
