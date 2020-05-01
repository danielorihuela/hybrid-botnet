import pytest

from client import seed_name_list, node_name_list, complete_node_list, node_from_index


seed_directions = [("down.onion", "comm.onion")]
node_files = "src/python/tests/auxiliar_files/node_list"


def test_seed_name_list():
    actual_seed_list = seed_name_list(seed_directions)
    expected_seed_list = ["seed0"]

    assert expected_seed_list == actual_seed_list


def test_not_node_name_list():
    expected_node_list = []
    actual_node_list = node_name_list()

    assert expected_node_list == actual_node_list


def test_node_name_list():
    expected_node_list = ["a", "b"]
    actual_node_list = node_name_list(node_files)

    assert expected_node_list == actual_node_list


def test_complete_node_list_without_node_files():
    expected_node_list = ["seed0"]
    actual_node_list = complete_node_list()

    assert expected_node_list == actual_node_list


def test_complete_node_list_with_node_files():
    expected_node_list = ["seed0", "a", "b"]
    actual_node_list = complete_node_list(node_files)

    assert expected_node_list == actual_node_list


def test_node_from_index_lower_than_seed_directions_len_without_node_file_type_comm():
    expected_node = "comm.onion"
    actual_node = node_from_index(0, seed_directions)

    assert expected_node == actual_node


def test_node_from_index_lower_than_seed_directions_len_without_node_file_type_down():
    expected_node = "down.onion"
    actual_node = node_from_index(0, seed_directions, type="down")

    assert expected_node == actual_node


def test_node_from_index_higher_than_seed_directions_len_without_node_file():
    with pytest.raises(UnboundLocalError):
        node_from_index(1, seed_directions)


def test_node_from_index_negative_number_lower_than_list_length():
    with pytest.raises(IndexError):
        node_from_index(-2, seed_directions)


def test_node_from_index_lower_than_seed_directions_len_with_node_file_type_comm():
    expected_node = "comm.onion"
    actual_node = node_from_index(0, seed_directions, node_files)

    assert expected_node == actual_node


def test_node_from_index_lower_than_seed_directions_len_with_node_file_type_down():
    expected_node = "down.onion"
    actual_node = node_from_index(0, seed_directions, node_files, type="down")

    assert expected_node == actual_node


def test_node_from_index_lower_than_complete_directions_len_with_node_file_type_comm():
    expected_node = "comm1.onion"
    actual_node = node_from_index(2, seed_directions, node_files)

    assert expected_node == actual_node


def test_node_from_index_lower_than_complete_directions_len_with_node_file_type_down():
    expected_node = "down1.onion"
    actual_node = node_from_index(2, seed_directions, node_files, type="down")

    assert expected_node == actual_node


def test_node_from_index_higher_than_complete_directions_len_with_node_file():
    with pytest.raises(UnboundLocalError):
        node_from_index(10, seed_directions)
