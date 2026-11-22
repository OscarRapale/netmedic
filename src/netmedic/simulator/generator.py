"""Build a seeded, deterministic network topology.

Same seed -> same network, on every run and every machine (see the L01 study note on
determinism). Each part of the network draws from its own random stream, so changing how one
part is generated doesn't reshuffle the others.
"""

import random

from netmedic.simulator.topology import Topology


def rng_for(seed: int, part: str) -> random.Random:
    """Return an independent, reproducible random stream for one part of the network."""
    return random.Random(f"{seed}:{part}")


def build_topology(seed: int) -> Topology:
    """Build the full two-site network for this seed."""
    topo = Topology(seed=seed)

    return topo
