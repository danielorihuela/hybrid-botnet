from botnet_p2p.message import get_msg_type, get_msg_data, get_signed_hash
from botnet_p2p import (
    ENCODING,
    BAD_MSG_TYPE,
    MSGTYPE_MSG_SEPARATOR,
    MSG_SIGNEDHASH_SEPARATOR,
)


def test_get_msg_type():
    msg_type = 1
    msg = f"{msg_type}{MSGTYPE_MSG_SEPARATOR}random message{MSG_SIGNEDHASH_SEPARATOR}random signed hash"
    actual_output = get_msg_type(msg)

    assert actual_output == msg_type


def test_get_msg_type_when_string_is_not_an_int():
    msg_type = "alguien ha fallado"
    msg = f"{msg_type}{MSGTYPE_MSG_SEPARATOR}random message{MSG_SIGNEDHASH_SEPARATOR}random signed hash"
    expected_output = BAD_MSG_TYPE
    actual_output = get_msg_type(msg)

    assert actual_output == expected_output


def test_get_msg_data():
    expected_output = "random data"
    msg = f"1{MSGTYPE_MSG_SEPARATOR}{expected_output}{MSG_SIGNEDHASH_SEPARATOR}signed hash"
    actual_output = get_msg_data(msg)

    assert actual_output == expected_output


def test_get_signed_data():
    expected_output = "random signed hash"
    msg = f"1{MSGTYPE_MSG_SEPARATOR}random data{MSG_SIGNEDHASH_SEPARATOR}{expected_output}"
    actual_output = get_signed_hash(msg)

    assert actual_output == expected_output.encode(ENCODING)
