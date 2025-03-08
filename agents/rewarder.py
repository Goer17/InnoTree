from abc import ABC, abstractmethod
from typing import List
from utils.string import Parser
from .engine import LLMEngine
from utils.logger import logger
import yaml
from pathlib import Path
import asyncio
import random

class Rewarder(ABC):
    @abstractmethod
    def reward(self, topic: str, idea: str, *args, **kwargs):
        pass

class ScienceRewarder(Rewarder):
    def __init__(self, engine: LLMEngine):
        self.engine = engine
        config_path = Path("config") / "prompts" / "rewarder.yml"
        with open(config_path) as f:
            prompts = yaml.safe_load(f)
            self.sys_prompt = prompts["system"]

    def reward(self, topic: str, idea: str) -> float:
        self.sys_prompt = self.sys_prompt.replace("$topic", topic)
        self.sys_prompt = self.sys_prompt.replace("$idea", idea)
        try:
            response = self.engine.generate_text(
                system_prompt=self.sys_prompt,
                messages=[]
            )[0]
            response = Parser.parse_json(response)
            score = 0
            for _, content in response.items():
                score += content["score"]

            return score / len(response), None
        except Exception as e:
            logger.error(f"Error rewarding idea: {e}")
            
            return 0, None

class IdeaArenaRewarder(Rewarder):
    def __init__(self, engine: LLMEngine):
        self.engine = engine
        config_path = Path("config") / "prompts" / "idea-arena.yml"
        with open(config_path) as f:
            prompts = yaml.safe_load(f)
            self.sys_prompt = prompts["system"]
    
    def reward(self, topic: str, idea: str, idea_db: List[str]) -> float:
        sys_prompt = self.sys_prompt.replace("$topic", topic)
        judges = []
        async def _reward(idea_x: str, idea_y: str) -> bool:
            if idea_x == idea_y:
                return True
            tag_x, tag_y = "A", "B"
            if random.random() < 0.5:
                tag_x, tag_y = tag_y, tag_x
            _sys_prompt = sys_prompt.replace(f"$idea_{tag_x}", idea_x)
            _sys_prompt = sys_prompt.replace(f"$idea_{tag_y}", idea_y)
            try:
                response = (await self.engine.generate_text_async(
                    system_prompt=_sys_prompt,
                    messages=[]
                ))[0]
                response = Parser.parse_json(response)
                score_x, score_y = 0, 0
                res = ""
                for key, content in response.items():
                    score_x += content["scores"][tag_x] + (content["better"] == tag_x)
                    score_y += content["scores"][tag_y] + (content["better"] == tag_y)
                    res += (
                        f"{key}:\n"
                        f"{content['comparison']}\n"
                        f"score: {tag_x}: {content['scores'][tag_x]} vs. {tag_y}: {content['scores'][tag_y]}\n"
                    )
                judges.append(
                    f"Idea {tag_x}:\n{idea_x}\n"
                    f"Idea {tag_y}:\n{idea_y}\n"
                    f"Result:\n{res}\n\n"
                )
                return score_x > score_y
            except Exception as e:
                logger.error(f"Error rewarding idea: {e}")
                return False

        total = len(idea_db)
        if total == 0:
            return 0.0, None
            
        coro_list = [_reward(idea, other_idea) for other_idea in idea_db]
        done, pedding = asyncio.run(asyncio.wait(coro_list))
        wins = sum(task.result() for task in done)
                
        return 10 * (wins / total), judges
        
