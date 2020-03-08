import logging
import os

BAD_MSG_TYPE=-1

MAX_PUBLIC_PEER_LIST_LENGTH = 2
MSGTYPE_MSG_SEPARATOR = "||"
MSG_SIGNEDHASH_SEPARATOR = "--"

BUFFER_SIZE = 4096
ENCODING = "latin1"

FILES_PATH = "/etc/rootkit_demo/"
PUBLIC_PEER_LIST = FILES_PATH + "public/peer_list"
PRIVATE_PEER_LIST = FILES_PATH + "private/full_peer_list"


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(name)s(%(levelname)s) - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def setup_peer_lists_locations(public_peer_list: str, private_peer_list: str):
    """Set up keys needed for sign and verify messages

        Args:
            public_peer_list: Path where the public peer list is located
            private_peer_list: Path where the private peer list is located

        Returns:
            Paths in string format where public and
            private peer lists are located
    """
    global PRIVATE_PEER_LIST
    global PUBLIC_PEER_LIST

    PRIVATE_PEER_LIST = private_peer_list
    PUBLIC_PEER_LIST = public_peer_list
