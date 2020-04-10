"""Basic message manipulation"""

from . import (
    ENCODING,
    MSG_SEPARATOR,
    DEFAULT_INT,
    logger,
)

from .security import (
    calculate_hash,
    sign_hash,
    verify_message,
)


def structure_msg(msg_info: dict) -> bytes:
    num_anonymizers = msg_info.get("num_anonymizers", 0)
    final_onion = msg_info.get("onion", "default")
    msg_type = msg_info.get("msg_type", DEFAULT_INT)
    msg = msg_info.get("msg", "")
    sign = msg_info.get("sign", "")

    elements_to_join = [num_anonymizers, final_onion, msg_type, msg]
    if sign:
        elements_to_join.append(sign)

    builded_msg = __join_with_separator(elements_to_join)

    logger.debug(f"Message info is {msg_info}")
    logger.debug(f"Resulting structured message = {builded_msg}")

    return builded_msg


def sign_structured_msg(msg: bytes, private_key_path: str) -> bytes:
    msg_to_sign = __get_msg_and_type(msg)
    msg_hash = calculate_hash(msg_to_sign)
    sign = sign_hash(msg_hash, private_key_path)
    signed_msg = __join_with_separator([msg.decode(ENCODING), sign.decode(ENCODING)])

    logger.debug(f"Message is {msg}")
    logger.debug(f"Resulting signed message = {signed_msg}")

    return signed_msg


def signed_by_master(msg: bytes, public_key_path: str) -> bool:
    signed_msg_part = __get_msg_and_type(msg)
    signed_hash = __get_signed_hash(msg)
    veredict = verify_message(public_key_path, signed_msg_part, signed_hash)

    return veredict


def breakdown_msg(msg: bytes) -> dict:
    info = msg.decode(ENCODING).split(MSG_SEPARATOR)
    try:
        num_anonymizers = int(info[0])
        msg_type = int(info[2])
    except ValueError:
        num_anonymizers = DEFAULT_INT
        msg_type = DEFAULT_INT

    msg_info = {
        "num_anonymizers": num_anonymizers,
        "onion": info[1],
        "msg_type": msg_type,
        "msg": info[3],
        "sign": info[4],
    }
    logger.debug(f"From message {msg} info = {msg_info}")

    return msg_info


def __get_msg_and_type(msg: bytes) -> bytes:
    separator_encoded = MSG_SEPARATOR.encode(ENCODING)
    splitted_msg = msg.split(separator_encoded)

    if len(splitted_msg) == 4:
        msg_to_sign = separator_encoded.join(splitted_msg[2:])
    else:
        msg_to_sign = separator_encoded.join(splitted_msg[2:4])

    logger.debug(f"Message {msg}")
    logger.debug(f"Part to sign = {msg_to_sign}")

    return msg_to_sign


def __join_with_separator(elements: list, separator: str = MSG_SEPARATOR) -> bytes:
    elements_converted_to_string = [str(item) for item in elements]
    elements_with_separator = separator.join(elements_converted_to_string)
    encoded_string = elements_with_separator.encode(ENCODING)

    logger.debug(f"With {elements} to join and {separator} as separator")
    logger.debug(f"Result = {encoded_string}")

    return encoded_string


def __get_signed_hash(msg: bytes) -> bytes:
    signed_hash = msg.split(MSG_SEPARATOR.encode(ENCODING))[-1]
    logger.debug(f"{msg} hash = {signed_hash}")

    return signed_hash
