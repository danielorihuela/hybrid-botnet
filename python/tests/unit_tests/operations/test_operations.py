import pytest

from botnet_p2p.operations import execute_command, select_random_neighbour


def test_execute_ls_command_returns_correct_output():
    command = "ls /bin/ls"
    expected_result = "/bin/ls\n"
    actual_result = execute_command(command)

    assert actual_result == expected_result


def test_execute_mkdir_and_rm_command_returns_correct_output():
    folder_name = "test_folder_with_a_name_hard_to_repeat_randomly"
    mkdir = f"mkdir {folder_name}"
    ls = f"ls | grep {folder_name}"
    expected_result = f"{folder_name}\n"
    execute_command(mkdir)
    actual_result = execute_command(ls)

    assert actual_result == expected_result

    rm = f"rm {folder_name} -r"
    expected_result = ""
    execute_command(rm)
    actual_result = execute_command(ls)

    assert actual_result == expected_result
