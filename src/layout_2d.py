"""Simple 2D layout helpers for PD diagrams."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import networkx as nx


@dataclass(frozen=True)
class Layout2D:
    """Graph-based 2D layout for a PD code."""

    graph: nx.Graph
    positions: dict[int, tuple[float, float]]
    edge_labels: dict[tuple[int, int], str]


def build_crossing_graph(pd_code: list[list[int]]) -> Layout2D:
    """Construct a graph linking crossings that share strand labels."""

    graph = nx.Graph()
    if not pd_code:
        return Layout2D(graph=graph, positions={}, edge_labels={})

    occurrences: dict[int, list[int]] = {}
    for index, crossing in enumerate(pd_code):
        graph.add_node(index, label=str(crossing))
        for label in crossing:
            occurrences.setdefault(label, []).append(index)

    edge_labels: dict[tuple[int, int], str] = {}
    for label, owners in occurrences.items():
        if len(owners) != 2:
            continue
        a, b = owners
        graph.add_edge(a, b)
        edge_labels[(a, b)] = str(label)

    positions_raw = nx.spring_layout(graph, seed=17) if graph.nodes else {}
    positions = {node: (float(x), float(y)) for node, (x, y) in positions_raw.items()}
    return Layout2D(graph=graph, positions=positions, edge_labels=edge_labels)
