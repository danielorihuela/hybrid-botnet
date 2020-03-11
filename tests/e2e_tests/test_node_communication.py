import threading
import pytest
import os
import socket
import time

from botnet_p2p.comm_utils import NodeP2P


public_key_path = os.path.join(os.getcwd(), "tests/auxiliar_files/public_key")
private_key_path = os.path.join(os.getcwd(), "tests/auxiliar_files/private_key")
server_port = 50001

actual_msg_type = None
actual_msg = None
actual_hash = None
actual_trusted = None


def server_thread():
    server_socket = NodeP2P(public_key_path, private_key_path)
    with open("/var/lib/tor/hidden_communication/hostname", "r") as onion:
        comm_onion = onion.read().strip()
    server_socket.bind(comm_onion, server_port)
    server_socket.listen(1)
    client_socket, addr = server_socket.accept()
    client_thread = threading.Thread(target=server_comm_thread, args=(client_socket,))
    client_thread.start()
    client_thread.join()
    client_socket.close()
    server_socket.close()


def server_comm_thread(client_socket: socket.socket):
    global actual_msg_type
    global actual_msg
    global actual_hash
    global actual_trusted

    (
        actual_msg_type,
        actual_msg,
        actual_hash,
        actual_trusted,
    ) = client_socket.recv_signed_msg()


def test_recv_signed_message():
    server = threading.Thread(target=server_thread, args=())
    server.start()
    time.sleep(1)
    client_socket = NodeP2P(public_key_path, private_key_path)
    client_socket.connect(server_dir, server_port)
    expected_msg_type = 1
    expected_msg = "hola"
    client_socket.send_signed_msg(expected_msg_type, expected_msg)
    client_socket.close()
    server.join()

    assert actual_msg == expected_msg
    assert actual_msg_type == expected_msg_type
    assert actual_trusted == True
