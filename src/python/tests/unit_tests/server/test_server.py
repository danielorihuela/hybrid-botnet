import pytest

from server import (
    msg_requires_to_be_signed,
    get_onion,
    get_hash_file,
    get_file_path,
    get_update_malware_info,
    NEW_NODE,
)


def test_msg_does_not_requires_to_be_signed():
    assert not msg_requires_to_be_signed(NEW_NODE)


@pytest.mark.parametrize("msg_type", [1, 2, 3, 4, 5, 6])
def test_msg_requires_to_be_signed(msg_type):
    assert msg_requires_to_be_signed(msg_type)


def test_get_onion():
    expected_onion_name = "asdf.onion"
    words = ["something", expected_onion_name, ".onion.hide"]
    actual_onion_name = get_onion(words)

    assert actual_onion_name == expected_onion_name


def test_get_hash_file():
    expected_hash = "b221d9dbb083a7f33428d7c2a3c3198ae925614d70210e28716ccaa7cd4ddb79"
    words = ["something", expected_hash, ".onion.hide"]
    actual_hash = get_hash_file(words)

    assert actual_hash == expected_hash


def test_get_file_path():
    expected_file_path = "some_file_path"
    words = ["some_file_path", "aasdfasdf", ".onion.hide"]
    exclude = ["aasdfasdf", ".onion.hide"]
    actual_file_path = get_file_path(words, exclude)

    assert actual_file_path == expected_file_path


def test_get_update_malware_info():
    file_path = "some_file_path"
    hash_ = "b221d9dbb083a7f33428d7c2a3c3198ae925614d70210e28716ccaa7cd4ddb79"
    onion = "myonion.onion"
    expected_file_path, expected_hash, expected_onion = get_update_malware_info(
        " ".join([file_path, hash_, onion])
    )

    assert file_path == expected_file_path
    assert hash_ == expected_hash
    assert onion == expected_onion
