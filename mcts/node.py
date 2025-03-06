import math
from typing import (
    List, Dict,
    Literal
)
import random
import datetime
from shortuuid import uuid

class Context:
    def __init__(self,
                 key: Literal["root", "reasoning", "search", "idea", "refine", "terminate"],
                 content: str = "",
                 observation: str | None = None
                 ):
        self.key = key
        self.content = content
        self.observation = observation
    
    @property
    def value(self) -> str:
        return (
            f"[{self.key}]\n"
            f"{self.content}\n"
            "[END]"
        )
    
    def __str__(self):
        string = self.value
        if self.observation:
            string += (
                "[observation]\n"
                f"{self.observation}\n"
                "[END]"
            )
        return string

class Node:
    def __init__(self, context: Context, parent: 'Node' = None, depth: int = 0, short_live: bool = False):
        self.parent: Node | None = parent
        self.children: List['Node'] = []
        self.value: float = 0
        self.visits: int = 0
        self.context: Context = context
        self.depth: int = depth
        self.n_id: str = f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]-[#{uuid()[:8]}]"
        self.short_live: bool = short_live
    def uct(self, exploration_weight: float = 1.0):
        if self.visits == 0:
            return float('inf')
        return (self.value / self.visits) + exploration_weight * math.sqrt(math.log(self.parent.visits) / self.visits)

    def best_child(self, exploration_weight: float = 1.0) -> 'Node':
        if not self.children:
            return None
        return max(self.children, key=lambda child: child.uct(exploration_weight))
    
    def epsilon_sample(self, epsilon: float = 0.05, explaration_weight: float = 1.0) -> 'Node':
        if not self.children:
            return None
        if random.random() < 1 - epsilon:
            return self.best_child(exploration_weight=explaration_weight)
        return random.choice(self.children)

    def update(self, reward: float):
        self.visits += 1
        self.value += reward
    
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def clear(self):
        self.parent = None
        self.children = []
        self.visits = 0
        self.value = 0
        # self.depth = 0

    @staticmethod
    def root_node() -> 'Node':
        ctx = Context(key='root')
        return Node(context=ctx)