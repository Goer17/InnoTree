from agents.engine import LLMEngine
from mcts.node import Context
from utils.rag import RAG
from typing import List
import asyncio

class Feedbacker:
    def __init__(
        self,
        engine: LLMEngine,
        rag: RAG,
        n_results: int = 3
    ):
        self.engine = engine
        self.rag = rag
        self.n_results = n_results

    def feedback(self, context: Context) -> str:
        if context.key == "search":
            return self.rag.query(context.content, self.n_results)
        return None
