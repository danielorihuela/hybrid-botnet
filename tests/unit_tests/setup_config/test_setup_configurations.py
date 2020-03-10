from botnet_p2p.operations import (
    public_peer_list_path,
    private_peer_list_path,
    change_peer_lists_locations,
)


def test_default_peer_lists_locations():
    public_peer_list = "/etc/rootkit_demo/public/peer_list"
    private_peer_list = "/etc/rootkit_demo/private/full_peer_list"

    assert public_peer_list == public_peer_list_path
    assert private_peer_list == private_peer_list_path


def test_setup_peer_lists_locations_change_paths_correctly():
    public_peer_list = "~"
    private_peer_list = "/"
    change_peer_lists_locations(public_peer_list, private_peer_list)

    from botnet_p2p.operations import public_peer_list_path, private_peer_list_path

    assert public_peer_list == public_peer_list_path
    assert private_peer_list == private_peer_list_path
