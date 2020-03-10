import logging
import os

BAD_MSG_TYPE=-1

MAX_PUBLIC_PEER_LIST_LENGTH = 2
MSGTYPE_MSG_SEPARATOR = "||"
MSG_SIGNEDHASH_SEPARATOR = "--"

BUFFER_SIZE = 4096
ENCODING = "latin1"


logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(name)s(%(levelname)s) - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
