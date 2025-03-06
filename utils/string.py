from typing import List, Dict
from mcts.node import Context
from utils.logger import logger
import re
import json
class Parser:
    @staticmethod
    def ctx2msg(contexts: List[Context]) -> List[Dict[str, str]]:
        res = []
        for ctx in contexts:
            res.append({
                "role": "assistant",
                "content": ctx.value
            })
            if ctx.observation:
                res.append({
                    "role": "user",
                    "content": ctx.observation
                })
        return res

    @staticmethod
    def msg2ctx(string: str) -> Context:
        try:
            key = re.search(r"\[(.*?)\]", string, re.DOTALL).group(1)
            content = re.search(r"\[.*?\](.*?)\[END\]", string, re.DOTALL).group(1)
            return Context(
                key=key,
                content=content
            )
        except Exception as e:
            logger.error(f"Error parsing context from string: {e}")
            return None
    
    @staticmethod
    def parse_json(string: str) -> Dict:
        try:
            data = re.search(r"```json(.*?)```", string, re.DOTALL).group(1)
            return json.loads(data)
        except Exception as e:
            logger.error(f"Error parsing json from string: {e}")
            return None
