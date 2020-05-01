import random

from botnet_p2p.operations import (
    __execute_command,
    __update_num_anonymizers,
    __select_random_neighbour,
    __get_next_hop,
)


random.seed(30)
node_files = "src/python/tests/auxiliar_files/nodes"


def test_execute_ls_command_returns_correct_output():
    command = "ls /bin/ls"
    expected_result = "/bin/ls\n"
    actual_result = __execute_command(command)

    assert actual_result == expected_result


def test_update_num_anonymizers():
    sample_msg_info = {
        "num_anonymizers": 10,
    }

    expected_output = {
        "num_anonymizers": 9,
    }
    actual_output = __update_num_anonymizers(sample_msg_info)

    assert actual_output == expected_output


def test_select_random_neighbour():
    expected_output = __select_random_neighbour(node_files)

    assert "b" in expected_output


def test_get_next_hop_when_num_anonymizers_greater_than_one():
    actual_output = __get_next_hop(2, node_files, "something")
    expected_output = __select_random_neighbour(node_files)

    assert actual_output == expected_output


def test_get_next_hop_when_num_anonymizers_equals_one():
    expected_output = "something"
    actual_output = __get_next_hop(1, node_files, expected_output)

    assert actual_output == expected_output
