"""Network topology: the devices and links of the simulated enterprise network.

Plain dataclasses (D-011): checked by tests, not validated at runtime. Pydantic models
live at the service boundaries (simulator API, MCP tool schemas).
"""


from dataclasses import dataclass, field
from enum import StrEnum


class Status(StrEnum):
    UP = "up"
    DOWN = "down"

class SwitchRole(StrEnum):
    CORE = "core"
    ACCESS = "access"

class PortMode(StrEnum):
    ACCESS = "access" # carries exactly one VLAN, untagged
    TRUNK = "trunk" # carries several VLANs, each packet tagged (802.1Q)

class PoeStatus(StrEnum):
    OFF = "off" # no power device on this port
    DELIVERING = "delivering"
    DENIED = "denied" # device asked for power, but the switch's budget is used up

class Band(StrEnum):
    GHZ_2_4 = "2.4GHz"
    GHZ_5 = "5GHz"

@dataclass(slots=True, kw_only=True)
class Site:
    id: str # "site-1"
    name: str # "Headquarters"

@dataclass(slots=True, kw_only=True)
class SwitchPort:
    number: int # numbered from 1, like the labels on the switch's front panel
    mode: PortMode
    status: Status = Status.UP
    allowed_vlans: list[int] = field(default_factory=list)
    connected_to: str | None = None # id of the device at the other end of the cable
    poe_status: PoeStatus = PoeStatus.OFF
    poe_draw_watts: float = 0.0 # non-zero only while poe_status is DELIVERING

@dataclass(slots=True, kw_only=True)
class Switch:
    id: str # "core-1", "core-2"
    site_id: str
    role: SwitchRole
    poe_budget_watts: float = 0.0 # total power shared by all ports; 0 for a core switch
    ports: dict[int, SwitchPort] = field(default_factory=dict) # port number -> port
    uplink_port: int | None = None # access switches: the port cabled to the core

@dataclass(slots=True, kw_only=True)
class AccessPoint:
    id: str # "ap-1-01"
    site_id: str
    switch_id: str # the access switch it's cabled to...
    switch_port: int # ...and on which port (that port records the same link)
    band: Band # simplification: one radio per AP (real APs have 2-3)
    channel:  int
    status: Status = Status.UP
