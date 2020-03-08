"""Basic message manipulation"""

from botnet_p2p import (
    ENCODING,
    BAD_MSG_TYPE,
    MSGTYPE_MSG_SEPARATOR,
    MSG_SIGNEDHASH_SEPARATOR,
)


def get_msg_type(msg: str) -> int:
    msg_type, _ = msg.split(MSGTYPE_MSG_SEPARATOR)
    try:
        return int(msg_type)
    except ValueError:
        return BAD_MSG_TYPE


def get_msg_data(msg: str) -> str:
    """ Get the data of the message. The data is the real message
        without the message type nor the signed hash

        Args:
            msg: Message

        Returns:
            The message itself
    """
    msg_data = msg.split(MSGTYPE_MSG_SEPARATOR)[1].split(MSG_SIGNEDHASH_SEPARATOR)[0]
    return msg_data


def get_signed_hash(msg: str) -> bytes:
    _, signed_hash = msg.split(MSG_SIGNEDHASH_SEPARATOR)
    return signed_hash.encode(ENCODING)
