import threading
import pytest
import os
import socket
import time

from botnet_p2p.comm_utils import NodeP2P


public_key_path = os.path.join(os.getcwd(), "tests/auxiliar_files/public_key")
private_key_path = os.path.join(os.getcwd(), "tests/auxiliar_files/private_key")
server_port = 50000
tor_server_port = 50001
server_host = "localhost"
server_onion_comm = None

actual_msg_type = None
actual_msg = None
actual_hash = None
actual_trusted = None

with open("/var/lib/tor/hidden_communication/hostname", "r") as onion:
    server_onion_comm = onion.read().strip()


def test_recv_signed_message():
    expected_msg_type = 1
    expected_msg = "hola"
    expected_trusted = True
    function_to_execute = server_comm_thread

    server = threading.Thread(target=server_thread, args=(function_to_execute,))
    server.start()
    time.sleep(1)
    create_client_and_send_msg(expected_msg_type, expected_msg)
    server.join()

    assert actual_msg == expected_msg
    assert actual_msg_type == expected_msg_type
    assert actual_trusted == expected_trusted


def server_thread(function_to_execute):
    server_socket = NodeP2P(public_key_path, private_key_path)
    server_socket.bind(server_host, server_port)
    server_socket.listen(1)
    client_socket, addr = server_socket.accept()
    client_thread = threading.Thread(target=function_to_execute, args=(client_socket,))
    client_thread.start()
    client_thread.join()
    client_socket.close()
    server_socket.close()


def server_comm_thread(client_socket: NodeP2P):
    global actual_msg_type
    global actual_msg
    global actual_hash
    global actual_trusted

    (actual_msg_type, actual_msg, actual_trusted,) = client_socket.recv_signed_msg()


def create_client_and_send_msg(msg_type: int, msg: str):
    client_socket = NodeP2P(public_key_path, private_key_path)
    client_socket.connect(server_onion_comm, tor_server_port)
    client_socket.send_signed_msg(msg_type, msg)
    client_socket.close()
