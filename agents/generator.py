from pathlib import Path
import yaml
from typing import (
    List
)
from mcts.node import (
    Context
)
from .engine import LLMEngine
from utils.string import Parser
from utils.logger import logger


import yaml

class Generator:
    def __init__(self,
                 engine: LLMEngine,
                 topic: str
                 ):
        super().__init__()
        self.engine = engine
        self.topic = topic
        config_path = Path("config") / "prompts" / "generator.yml"
        with open(config_path) as f:
            prompts = yaml.safe_load(f)
            self.sys_prompt = prompts["system"]
            self.sys_prompt = self.sys_prompt.replace("$topic", self.topic)


    def generate(self, contexts: List[Context], *args, **kwargs) -> List[Context]:
        msgs = Parser.ctx2msg(contexts)
        ctxs = []
        try:
            responses = self.engine.generate_text(
                system_prompt=self.sys_prompt,
                messages=msgs,
                stop=["[END]"],
                *args,
                **kwargs
            )
            for response in responses:
                ctx = Parser.msg2ctx(response + "[END]")
                if ctx is None:
                    raise RuntimeError("Format mistake")
                ctxs.append(ctx)
            return ctxs
        except Exception as e:
            logger.error(f"Error generating idea: {e}")
            # retry...
            return self.generate(contexts)
