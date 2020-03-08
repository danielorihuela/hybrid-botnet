import os
import pytest

from botnet_p2p import ENCODING
from botnet_p2p.comm_utils import NodeP2P

public_key_path = os.path.join(os.getcwd(), "tests/auxiliar_files/public_key")
private_key_path = os.path.join(os.getcwd(), "tests/auxiliar_files/private_key")
test_socket = NodeP2P(public_key_path, private_key_path)


@pytest.mark.parametrize("msg_type", list(range(5)))
@pytest.mark.parametrize(
    "msg", ["random message"],
)
def test_build_msg_structure(msg_type, msg):
    expected_output = f"{msg_type}||{msg}--"

    build_msg_structure = test_socket._NodeP2P__build_msg_structure
    actual_output = build_msg_structure(msg_type, msg)
    actual_output_str = actual_output.decode(ENCODING)

    assert actual_output_str.startswith(expected_output)


@pytest.mark.parametrize("msg_type", list(range(5)))
@pytest.mark.parametrize(
    "msg", ["random message"],
)
def test_extract_info_from_message(msg_type, msg):
    received_message = f"{msg_type}||{msg}--SIGNED HASH"
    received_message_bytes = received_message.encode(ENCODING)

    extract_info_from_message = test_socket._NodeP2P__extract_info_from_message
    actual_type, actual_msg, actual_hash = extract_info_from_message(
        received_message_bytes
    )

    expected_output_type = msg_type
    expected_output_msg = f"{msg}"
    expected_output_hash = "SIGNED HASH".encode(ENCODING)

    assert actual_type == expected_output_type
    assert actual_msg == expected_output_msg
    assert actual_hash == expected_output_hash


def test_set_private_key():
    expected_private_key_path = os.path.join(os.getcwd(), "tests/auxiliar_files/private_key2")

    private_key_path_when_node_created = test_socket._NodeP2P__private_key_path
    test_socket.set_private_key_path(expected_private_key_path)
    actual_private_key_path = test_socket._NodeP2P__private_key_path

    assert private_key_path_when_node_created == private_key_path
    assert actual_private_key_path == expected_private_key_path

