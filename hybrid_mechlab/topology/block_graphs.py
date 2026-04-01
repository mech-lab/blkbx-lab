"""Block graph helpers."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

from hybrid_mechlab.schedules import HybridSchedule


@dataclass
class BlockGraph:
    nodes: List[int]
    edges: List[Tuple[int, int]]


def make_block_graph(schedule: HybridSchedule) -> BlockGraph:
    nodes = list(range(len(schedule.ops)))
    edges = [(i, i + 1) for i in range(len(schedule.ops) - 1)]
    return BlockGraph(nodes=nodes, edges=edges)
