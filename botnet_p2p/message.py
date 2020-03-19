"""Basic message manipulation"""

from botnet_p2p import (
    ENCODING,
    BAD_MSG_TYPE,
    MSGTYPE_MSG_SEPARATOR,
    MSG_SIGNEDHASH_SEPARATOR,
)

from botnet_p2p.security import (
    calculate_hash,
    sign_hash,
    encrypt,
    decrypt,
    verify_message,
)


class Message(object):
    """Message with security features"""

    def __init__(self, msg_type: int = None, msg: str = None):
        if isinstance(msg_type, int):
            self.__msg_type = msg_type
        else:
            self.__msg_type = BAD_MSG_TYPE

        self.__msg = msg

    def get_msg_type(self) -> int:
        return self.__msg_type

    def get_msg_body(self) -> str:
        return self.__msg
    
    def get_signed_hash(self) -> bytes:
        return self.__signed_hash

    def sign_msg(self, private_key_path: str) -> bytes:
        """ Build message following a structure so every bot in the P2P
            can understand each other

            Args:
                private_key_path: Location of private key to sign

            Returns:
                Bytes in a structured format
        """
        type_msg_joined = self.__join_msg_type_and_msg()
        msg_hash = calculate_hash(type_msg_joined)
        signed_hash = sign_hash(msg_hash, private_key_path)
        final_msg = (
            type_msg_joined.encode(ENCODING)
            + f"{MSG_SIGNEDHASH_SEPARATOR}".encode(ENCODING)
            + signed_hash
        )
        return final_msg

    def __join_msg_type_and_msg(self) -> str:
        msg = f"{self.__msg_type}{MSGTYPE_MSG_SEPARATOR}{self.__msg}"
        return msg

    def from_signed_msg(self, structured_msg: bytes, public_key_path: str) -> bool:
        """ A message following the required structured
            will be received. Private variables will be
            filled.

            Args:
                structured_msg: Message with specific structure
                publick_key_path: Publick key location
            
            Return:
                Whether the message can be trusted or not
            
            Raises:
                cryptography.exceptions.InvalidSignature when signed hash
                and hash do not match
        """
        structured_msg_decoded = structured_msg.decode(ENCODING)

        self.__msg_type = self.__get_msg_type_from_signed_msg(structured_msg_decoded)
        self.__msg = self.__get_msg_data_from_signed_msg(structured_msg_decoded)
        self.__signed_hash = self.__get_signed_hash_from_signed_msg(structured_msg_decoded)

        type_msg_join = self.__join_msg_type_and_msg()
        return verify_message(public_key_path, type_msg_join, self.__signed_hash)

    def __get_msg_type_from_signed_msg(self, msg: str) -> int:
        msg_type, _ = msg.split(MSGTYPE_MSG_SEPARATOR)
        try:
            return int(msg_type)
        except ValueError:
            return BAD_MSG_TYPE

    def __get_msg_data_from_signed_msg(self, msg: str) -> str:
        """ Get the data of the message. The data is the real message
            without the message type nor the signed hash

            Args:
                msg: Received text

            Returns:
                The message itself
        """
        msg_data = msg.split(MSGTYPE_MSG_SEPARATOR)[1].split(MSG_SIGNEDHASH_SEPARATOR)[
            0
        ]
        return msg_data

    def __get_signed_hash_from_signed_msg(self, msg: str) -> bytes:
        _, signed_hash = msg.split(MSG_SIGNEDHASH_SEPARATOR)
        return signed_hash.encode(ENCODING)

    def __verify_sign(self, public_key_path: str) -> bool:
        type_msg_joined = self.__join_msg_type_and_msg()
        veredict = verify_message(public_key_path, type_msg_joined, self.__signed_hash)
        return veredict
