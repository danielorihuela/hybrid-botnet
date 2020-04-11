import pytest

from python.botnet_p2p.message import (
    structure_msg,
    sign_structured_msg,
    __get_msg_and_type,
    __join_with_separator,
    signed_by_master,
    __get_signed_hash,
    breakdown_msg,
)
from python.botnet_p2p import (
    ENCODING,
    MSG_SEPARATOR,
)

public_key_path = "src/python/tests/auxiliar_files/public_key"
private_key_path = "src/python/tests/auxiliar_files/private_key"


@pytest.fixture(scope="module")
def msg_info():
    return {
        "num_anonymizers": 10,
        "onion": "onion",
        "msg_type": 3,
        "msg": "hello",
    }


@pytest.fixture(scope="module")
def structured_msg():
    return b"10<<onion<<3<<hello"


def join_texts(texts: list):
    if isinstance(texts[0], bytes):
        return MSG_SEPARATOR.encode(ENCODING).join(texts)
    return MSG_SEPARATOR.join(texts)


def transform_to_bytes(text: str):
    return text.encode(ENCODING)


def test_structure_msg_default_values():
    msg_info = {
        "msg_type": 1,
        "msg": "hello",
    }

    expected_output = transform_to_bytes(join_texts(["0", "default", "1", "hello"]))
    actual_output = structure_msg(msg_info)

    assert isinstance(actual_output, bytes)
    assert actual_output == expected_output


def test_structure_msg(msg_info, structured_msg):
    output = structure_msg(msg_info)

    assert isinstance(output, bytes)
    assert output == structured_msg


def test_structure_msg_with_sign(msg_info, structured_msg):
    msg_info["sign"] = "this sign"

    expected_output = join_texts([structured_msg, b"this sign"])
    actual_output = structure_msg(msg_info)

    assert isinstance(actual_output, bytes)
    assert actual_output == expected_output


def test_sign_structured_msg(msg_info, structured_msg):
    sample_structured_msg = structure_msg(msg_info)
    actual_output = sign_structured_msg(sample_structured_msg, private_key_path)

    assert isinstance(actual_output, bytes)
    assert actual_output.startswith(structured_msg)


def test_get_msg_and_type_from_unsigned_msg(structured_msg):
    expected_output = b"3<<hello"
    actual_output = __get_msg_and_type(structured_msg)

    assert actual_output == expected_output


def test_get_msg_and_type_from_signed_msg(structured_msg):
    expected_output = b"3<<hello"
    actual_output = __get_msg_and_type(structured_msg)

    assert actual_output == expected_output


def test_join_with_separator():
    strings = ["first word", "second word"]
    expected_output = b"first word<<second word"
    actual_output = __join_with_separator(strings, MSG_SEPARATOR)

    assert actual_output == expected_output


def test_signed_by_master(structured_msg):
    signed_structured_msg = sign_structured_msg(structured_msg, private_key_path)
    actual_output = signed_by_master(signed_structured_msg, public_key_path)

    assert actual_output is True


def test_not_signed_by_master(structured_msg):
    badly_signed_msg = join_texts([structured_msg, b"bad signature"])
    actual_output = signed_by_master(badly_signed_msg, public_key_path)

    assert actual_output is False


def test_get_signed_hash(structured_msg):
    expected_output = b"sign"
    signed_msg = join_texts([structured_msg, expected_output])
    actual_output = __get_signed_hash(signed_msg)

    assert actual_output == expected_output


@pytest.mark.parametrize("num_anonymizers, msg_type", [(10, "a"), ("a", 2), ("a", "b")])
def test_breakdown_structure_incorrect_numbers(num_anonymizers, msg_type):
    sample_input_encoded = transform_to_bytes(
        join_texts(
            [str(num_anonymizers), "onion", str(msg_type), "hello", "this other"]
        )
    )

    expected_output = {
        "num_anonymizers": -1,
        "onion": "onion",
        "msg_type": -1,
        "msg": "hello",
        "sign": "this other",
    }
    actual_output = breakdown_msg(sample_input_encoded)

    assert isinstance(actual_output, dict)
    assert expected_output == actual_output


def test_breakdown_structure(msg_info, structured_msg):
    sample_input_encoded = join_texts([structured_msg, b"this other"])

    msg_info["sign"] = "this other"
    expected_output = msg_info
    actual_output = breakdown_msg(sample_input_encoded)

    assert isinstance(actual_output, dict)
    assert expected_output == actual_output
