"""Build a seeded, deterministic network topology.

Same seed -> same network, on every run and every machine (see the L01 study note on
determinism). Each part of the network draws from its own random stream, so changing how one
part is generated doesn't reshuffle the others.
"""

import random
from ipaddress import IPv4Address, IPv4Network

from netmedic.simulator.topology import (
    AccessPoint,
    AuthMethod,
    Band,
    Client,
    ClientKind,
    DhcpPool,
    PoeStatus,
    PortMode,
    Server,
    ServerKind,
    Site,
    Switch,
    SwitchPort,
    SwitchRole,
    Topology,
    Wlan,
)

SITE_NAMES = {1: "Headquarters", 2: "Branch office"}
ACCESS_SWITCHES_PER_SITE = 2
APS_PER_SWITCH = 3
VLANS = (10, 20, 30)  # Corp, Guest, IoT. A tuple: it can't be changed by accident
UPLINK_PORT = 24  # the last port of a 24-port access switch is cabled to the core
POE_BUDGET_WATTS = 100.0

# Channel plan for the 6 APs of a site (numbered 1-6): no two APs share a channel, as a
# site survey would plan it. Faults (L03) break this plan on purpose.
CHANNEL_PLAN: dict[int, tuple[Band, int]] = {
    1: (Band.GHZ_5, 36),
    2: (Band.GHZ_5, 44),
    3: (Band.GHZ_2_4, 1),
    4: (Band.GHZ_5, 149),
    5: (Band.GHZ_5, 157),
    6: (Band.GHZ_2_4, 6),
}

WLAN_PLAN = (  # SSID, VlAN, login method
    ("Corp", 10, AuthMethod.DOT1X),
    ("Guest", 20, AuthMethod.PSK),
    ("IoT", 30, AuthMethod.PSK),
)
SERVER_PLAN = (  # id, kind, IP: shared by both sites
    ("dhcp-1", ServerKind.DHCP, "10.0.0.10"),
    ("dns-1", ServerKind.DNS, "10.0.0.11"),
    ("radius-1", ServerKind.RADIUS, "10.0.0.12"),
)
POOL_SIZES = {10: 60, 20: 40, 30: 30}  # per site and VLAN: addresses a pool may hand out
POOL_FIRST_HOST = 100  # pools hand out .100 upwards; lower addresses are for fixed devices
CLIENTS_PER_SITE = {10: (35, 45), 20: (15, 25), 30: (10, 20)}  # per VLAN: min, max
CLIENT_KINDS = {  # per VLAN: possible kinds, and how likely each one is
    10: ((ClientKind.LAPTOP, ClientKind.PHONE), (3, 1)),  # Corp: mostly laptops
    20: ((ClientKind.PHONE, ClientKind.LAPTOP), (4, 1)),  # Guest: mostly visitors' phones
    30: ((ClientKind.IOT,), (1,)),  # IoT: printers, sensors, cameras
}


def rng_for(seed: int, part: str) -> random.Random:
    """Return an independent, reproducible random stream for one part of the network."""
    return random.Random(f"{seed}:{part}")


def build_topology(seed: int) -> Topology:
    """Build the full two-site network for this seed."""
    topo = Topology(seed=seed)
    devices_rng = rng_for(seed, "devices")
    for site_num in SITE_NAMES:  # dicts keep insertion order: site 1, then site 2
        add_site(topo, site_num, devices_rng)
    add_services(topo)
    add_clients(topo, rng_for(seed, "clients"))
    return topo


def add_services(topo: Topology) -> None:
    """Add the Wi-Fi networks, the shared servers, and one DHCP pool per site and VLAN."""
    for ssid, vlan_id, auth in WLAN_PLAN:
        topo.wlans[ssid] = Wlan(ssid=ssid, vlan_id=vlan_id, auth=auth)
    for server_id, kind, ip in SERVER_PLAN:
        topo.servers[server_id] = Server(id=server_id, kind=kind, ip=IPv4Address(ip))
    for site_num in SITE_NAMES:
        for vlan_id in VLANS:
            pool = DhcpPool(
                id=f"pool-{site_num}-{vlan_id}",
                site_id=f"site-{site_num}",
                vlan_id=vlan_id,
                subnet=IPv4Network(f"10.{site_num}.{vlan_id}.0/24"),  # our addressing plan
                size=POOL_SIZES[vlan_id],
            )
            topo.pools[pool.id] = pool


def add_site(topo: Topology, site_num: int, rng: random.Random) -> None:
    """Add one site: a core switch, its access switches and their APs."""
    site_id = f"site-{site_num}"
    topo.sites[site_id] = Site(id=site_id, name=SITE_NAMES[site_num])
    core = Switch(id=f"core-{site_num}", site_id=site_id, role=SwitchRole.CORE)
    topo.switches[core.id] = core
    for sw_num in range(1, ACCESS_SWITCHES_PER_SITE + 1):
        access = add_access_switch(topo, site_num, sw_num, rng)
        core.ports[sw_num] = SwitchPort(  # core port N is cabled to access switch N
            number=sw_num,
            mode=PortMode.TRUNK,
            allowed_vlans=list(VLANS),
            connected_to=access.id,
        )


def add_access_switch(topo: Topology, site_num: int, sw_num: int, rng: random.Random) -> Switch:
    """Add an access switch, one PoE-powered AP per port, and its uplink to the core."""
    site_id = f"site-{site_num}"
    switch = Switch(
        id=f"access-{site_num}-{sw_num}",
        site_id=site_id,
        role=SwitchRole.ACCESS,
        poe_budget_watts=POE_BUDGET_WATTS,
        uplink_port=UPLINK_PORT,
    )
    topo.switches[switch.id] = switch
    for port_num in range(1, APS_PER_SWITCH + 1):
        ap_num = (sw_num - 1) * APS_PER_SWITCH + port_num  # 1-6 within the site
        band, channel = CHANNEL_PLAN[ap_num]
        ap = AccessPoint(
            id=f"ap-{site_num}-{ap_num:02d}",
            site_id=site_id,
            switch_id=switch.id,
            switch_port=port_num,
            band=band,
            channel=channel,
        )
        topo.aps[ap.id] = ap
        switch.ports[port_num] = SwitchPort(
            number=port_num,
            mode=PortMode.TRUNK,  # an AP serves all three SSIDs, so it needs all three VLANs
            allowed_vlans=list(VLANS),
            connected_to=ap.id,
            poe_status=PoeStatus.DELIVERING,
            poe_draw_watts=round(rng.uniform(13.0, 20.0), 1),
        )
    switch.ports[UPLINK_PORT] = SwitchPort(
        number=UPLINK_PORT,
        mode=PortMode.TRUNK,
        allowed_vlans=list(VLANS),
        connected_to=f"core-{site_num}",
    )
    return switch


def add_clients(topo: Topology, rng: random.Random) -> None:
    """Connect clients to each Wi-Fi network at each site, each with a DHCP lease."""
    for site_num in SITE_NAMES:
        site_id = f"site-{site_num}"
        site_aps = [ap.id for ap in topo.aps.values() if ap.site_id == site_id]
        for wlan in topo.wlans.values():
            pool = topo.pools[f"pool-{site_num}-{wlan.vlan_id}"]
            kinds, weights = CLIENT_KINDS[wlan.vlan_id]
            low, high = CLIENTS_PER_SITE[wlan.vlan_id]
            for _ in range(rng.randint(low, high)):
                client = Client(
                    mac=new_mac(topo, rng),
                    kind=rng.choices(kinds, weights)[0],
                    site_id=site_id,
                    ssid=wlan.ssid,
                    ap_id=rng.choice(site_aps),
                    ip=pool.subnet.network_address + POOL_FIRST_HOST + pool.leased,
                )
                pool.leased += 1
                topo.clients[client.mac] = client


def new_mac(topo: Topology, rng: random.Random) -> str:
    """Return a random MAC address that no client in the topology has yet."""
    while True:
        mac = ":".join(f"{byte:02x}" for byte in rng.randbytes(6))
        if mac not in topo.clients:
            return mac
