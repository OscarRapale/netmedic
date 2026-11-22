"""Shared fixtures for the simulator tests."""

import pytest

from netmedic.simulator.generator import build_topology
from netmedic.simulator.topology import Topology

# Invariants must hold for any seed, not only the one we happen to use in examples.
SEEDS = [0, 1, 42, 2026]


@pytest.fixture(params=SEEDS, ids=[f"seed-{seed}" for seed in SEEDS])
def topo(request: pytest.FixtureRequest) -> Topology:
    """A freshly built topology. Every test that uses it runs once per seed."""
    return build_topology(request.param)
