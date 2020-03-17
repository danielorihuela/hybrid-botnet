import os
import pytest

from botnet_p2p.message import Message
from botnet_p2p import (
    ENCODING,
    BAD_MSG_TYPE,
    MSGTYPE_MSG_SEPARATOR,
    MSG_SIGNEDHASH_SEPARATOR,
)

public_key_path = os.path.join(os.getcwd(), "tests/auxiliar_files/public_key")
private_key_path = os.path.join(os.getcwd(), "tests/auxiliar_files/private_key")


def test_get_msg_type():
    expected_output = 1
    msg_body = "random_message"

    msg = Message(expected_output, msg_body)
    actual_output = msg.get_msg_type()

    assert actual_output == expected_output


def test_get_msg_type_when_string_is_not_an_int():
    expected_output = BAD_MSG_TYPE
    msg_type = "alguien ha fallado"
    msg_body = "random_message"

    msg = Message(msg_type, msg_body)
    actual_output = msg.get_msg_type()

    assert actual_output == expected_output


def test_get_msg_data():
    expected_output = "random data"
    msg_type = 1

    msg = Message(msg_type, expected_output)
    actual_output = msg.get_msg_body()

    assert actual_output == expected_output


@pytest.mark.parametrize("msg_type", list(range(5)))
@pytest.mark.parametrize(
    "msg", ["random message"],
)
def test_sign_msg(msg_type, msg):
    expected_output = f"{msg_type}||{msg}--"

    actual_output = Message(msg_type, msg).sign_msg(private_key_path)
    actual_output_str = actual_output.decode(ENCODING)

    assert actual_output_str.startswith(expected_output)


@pytest.mark.parametrize("actual_msg_type", list(range(5)))
@pytest.mark.parametrize(
    "actual_msg", ["random message"],
)
@pytest.mark.parametrize("string_hash", ["SIGNED HASH"])
def test_from_signed_msg(actual_msg_type, actual_msg, string_hash):
    actual_hash = string_hash.encode(ENCODING)
    received_message = f"{actual_msg_type}||{actual_msg}--{string_hash}"
    received_message_bytes = received_message.encode(ENCODING)

    message_to_fill = Message()
    trusted = message_to_fill.from_signed_msg(received_message_bytes, public_key_path)

    expected_output_type = message_to_fill.get_msg_type() 
    expected_output_msg = message_to_fill.get_msg_body()
    expected_output_hash = message_to_fill.get_signed_hash()

    assert actual_msg_type== expected_output_type
    assert actual_msg == expected_output_msg
    assert actual_hash == expected_output_hash
    assert trusted == False 
