"""Tests for the seeded topology generator."""

from netmedic.simulator.generator import build_topology
from netmedic.simulator.topology import Topology


def test_same_seed_builds_identical_network() -> None:
    assert build_topology(42) == build_topology(42)


def test_different_seeds_build_different_networks() -> None:
    assert build_topology(42) != build_topology(7)


def test_network_shape(topo: Topology) -> None:
    assert len(topo.sites) == 2
    assert len(topo.switches) == 6  # 2 core + 4 access
    assert len(topo.aps) == 12
    assert 120 <= len(topo.clients) <= 180  # spec: "about 150 clients"


def test_ap_and_switch_port_agree_on_their_cable(topo: Topology) -> None:
    for ap in topo.aps.values():
        port = topo.switches[ap.switch_id].ports[ap.switch_port]
        assert port.connected_to == ap.id


def test_no_two_aps_at_a_site_share_a_channel(topo: Topology) -> None:
    for site_id in topo.sites:
        channels = [ap.channel for ap in topo.aps.values() if ap.site_id == site_id]
        assert len(channels) == len(set(channels))


def test_ports_have_independent_vlan_lists(topo: Topology) -> None:
    ports = [port for switch in topo.switches.values() for port in switch.ports.values()]
    ports[0].allowed_vlans.remove(20)
    assert all(20 in port.allowed_vlans for port in ports[1:])


def test_every_client_has_an_ip_from_its_own_pool(topo: Topology) -> None:
    for client in topo.clients.values():
        vlan_id = topo.wlans[client.ssid].vlan_id
        pool = topo.pools[f"pool-{client.site_id.removeprefix('site-')}-{vlan_id}"]
        assert client.ip is not None
        assert client.ip in pool.subnet


def test_pool_lease_counts_match_their_clients(topo: Topology) -> None:
    for pool in topo.pools.values():
        holders = [c for c in topo.clients.values() if c.ip is not None and c.ip in pool.subnet]
        assert len(holders) == pool.leased


def test_healthy_pools_have_headroom(topo: Topology) -> None:
    for pool in topo.pools.values():
        assert pool.size > 0
        assert pool.utilization <= 0.75
