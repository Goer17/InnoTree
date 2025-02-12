import asyncio
import random
import re
import yaml
import json
from pathlib import Path
from abc import ABC, abstractmethod
from typing import (
    List,
    Dict,
    Tuple
)
from mcts.node import (
    Context
)
from agents.general import (
    LLMEngine,
    PromptTemplate
)

class Rewarder(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def get_reward(self, contexts: List[Context], *args, **kwargs) -> Tuple[float, Dict | None]:
        pass

class IdeaArena(Rewarder):
    def __init__(self,
                 engine: LLMEngine,
                 topic: str
                 ):
        config_path = Path("agents") / "prompts" / "idea-arena.yml"
        with open(config_path) as f:
            prompts = yaml.safe_load(f)
            sys_prompt = PromptTemplate(
                template=prompts["sys_prompt"],
                parameters={
                    "topic": topic,
                    "idea_A": "",
                    "idea_B": ""
                }
            )
            self.sys_prompt = sys_prompt
        self.engine = engine
        self.idea_db = []
    
    async def combat(self,
               idea1: str,
               idea2: str,
               alpha: float = 1.0
               ) -> bool:
        idea_idx = random.randint(0, 1)
        if idea_idx == 0:
            self.sys_prompt.parameters["idea_A"] = idea1
            self.sys_prompt.parameters["idea_B"] = idea2
        else:
            self.sys_prompt.parameters["idea_A"] = idea2
            self.sys_prompt.parameters["idea_B"] = idea1
        try:
            response = (await self.engine.async_gen_from_prompt(sys_prompt=self.sys_prompt))[0]
            response = re.search(pattern=r"```json(.*?)```", string=response, flags=re.S).group(1)
            response = json.loads(response)
            s_a, s_b = 0, 0
            for key in [
                "novelty",
                "feasibility",
                "clarity",
                "impact",
                "relevance"
            ]:
                s_a += response[key]["scores"]["A"] + alpha * (response[key]["better"] == "A")
                s_b += response[key]["scores"]["B"] + alpha * (response[key]["better"] == "B")
            if idea_idx == 0 and s_a > s_b or idea_idx == 1 and s_a < s_b:
                return True
            else:
                return False
        except Exception as e:
            # Retry
            return await self.combat(
                idea1=idea1,
                idea2=idea2,
                alpha=alpha
            )
    
    def get_reward(self, contexts, *args, **kwargs) -> Tuple[float, Dict | None]:
        idea = contexts[-1].content
        win_cnt = 0
        coro_list = []
        for other_idea in self.idea_db:
            coro = self.combat(idea, other_idea)
            coro_list.append(coro)
        responses, _ = asyncio.run(asyncio.wait(coro_list, timeout=None))
        for response in responses:
            if response.result():
                win_cnt += 1

        return win_cnt / (len(self.idea_db) + 1) * 10, None

    def add_idea(self, idea: str):
        self.idea_db.append(idea)
    
    def clear_all(self):
        self.idea_db = []

class SciRewarder(Rewarder):
    def __init__(self,
                 base_url: str,
                 api_key: str,
                 model: str,
                 topic: str
                 ):
        config_path = Path("agents") / "prompts" / "sci-rewarder.yml"
        with open(config_path) as f:
            prompts = yaml.safe_load(f)
            sys_prompt = PromptTemplate(
                template=prompts["sys_prompt"],
                parameters={
                    "topic": topic,
                    "idea": ""
                }
            )
        self.engine = LLMEngine(
            api_key=api_key,
            base_url=base_url,
            model=model,
            sys_prompt=sys_prompt
        )
    
    def get_reward(self,
                   contexts: List[Context],
                   *args, **kwargs) -> Tuple[float, Dict | None]:
        idea = contexts[-1].content
        self.engine.sys_prompt.parameters["idea"] = idea
        response = self.engine.gen_from_prompt()[0]
        jud_match = re.match(pattern=r"```json(.*?)```", string=response, flags=re.DOTALL)
        if not jud_match:
            # TODO
            # current: redo
            # print("format error")
            return self.get_reward(
                contexts=contexts
                *args, **kwargs
            )
        judgments = json.loads(jud_match.group(1))
        score_sum = 0
        for key in [
            "novelty",
            "feasibility",
            "clarity",
            "impact",
            "relevance"
        ]:
            # TODO handle the key error
            # current: redo
            # print("format error")
            if key not in judgments:
                return self.get_reward(
                    contexts=contexts,
                    *args, **kwargs
                )
            score_sum += int(judgments[key]["score"])
        score_avg = score_sum / 5
        return score_avg, judgments
            

class TestRewarder(Rewarder):
    def __init__(self):
        super().__init__()
        self.path = [0, -1, -2, 1, -1, -1, 1, 2, 3, 5, -5, -10, 3, 3, 3, 3, -2, -2, 0]
        # Maximum: 24
        # +3, +3, +1, +1, +1, +3, +1, +1, +1, +3
    
    def get_reward(self, contexts, *args, **kwargs) -> Tuple[float, Dict | None]:
        reward = 0.0
        idx = 0
        for context in contexts:
            idx += int(context.content)
            if idx >= len(self.path):
                break
            reward += self.path[idx]
        return reward, None
        