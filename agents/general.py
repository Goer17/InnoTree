import json
import re
from typing import List, Dict
from openai import (
    Client,
    AsyncOpenAI
)
from mcts.node import (
    Context
)

class PromptTemplate:
    def __init__(self,
                 template: str,
                 parameters: Dict
                 ):
        self.template = template
        self.parameters = parameters
    
    @property
    def value(self):
        prompt = self.template
        for key, content in self.parameters.items():
            prompt = prompt.replace(f"${key}", content)
        return prompt

class PromatParser:
    @staticmethod
    def to_context(string: str) -> Context | None:
        match_key = re.match(pattern=r"\[(.*?)\]", string=string)
        match_content = re.match(pattern=r"\[.*?\](.*)\[END\]", string=string, flags=re.DOTALL)
        if not match_key or not match_content:
            # Error format
            return None
        key, content = match_key.group(1), match_content.group(1).strip()
        context = Context(key=key, content=content)
        return context
    
    @staticmethod
    def format_idea(idea: str) -> str | None:
        refs_match = re.search(pattern=r"```json(.*?)```", string=idea, flags=re.S)
        if refs_match is None:
            return None
        content_match = re.search(pattern=r"==START==(.*?)==END==", string=idea, flags=re.DOTALL)
        if content_match is None:
            return None
        content = content_match.group(1).strip()
        refs_json =  json.loads(refs_match.group(1))
        refs = "## References\n" + "\n".join([f"{idx} {content}" for idx, content in refs_json.items()])
        
        return content + "\n\n" + refs


class LLMEngine:
    def __init__(self,
                 api_key: str,
                 base_url: str,
                 model: str = "gpt-4o"
                 ):
        self.client = Client(
            api_key=api_key,
            base_url=base_url
        )
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
    
    async def async_gen_from_prompt(self,
                                    sys_prompt: str | PromptTemplate = "You are an AI assistant.",
                                    prompt: PromptTemplate | str | None = None,
                                    n_choices: int = 1,
                                    *args, **kwargs
                                    ) -> List[str]:
        sys_prompt = sys_prompt if isinstance(sys_prompt, str) else sys_prompt.value
        messages = [
            {
                "role": "system",
                "content": sys_prompt
            }
        ]
        if prompt is not None:
            prompt_content = prompt if isinstance(prompt, str) else prompt.value
            messages.append(
                {
                    "role": "user",
                    "content": prompt_content
                }
            )
        responses = await self.async_client.chat.completions.create(
            model=self.model,
            messages=messages,
            n=n_choices,
            *args, **kwargs
        )
        results = []
        for i in range(len(responses.choices)):
            response = responses.choices[i].message.content
            results.append(response)
        return results
    
    def gen_from_prompt(self,
                        sys_prompt: str | PromptTemplate = "You are an AI assistant.",
                        prompt: PromptTemplate | str | None = None,
                        n_choices: int = 1,
                        *args, **kwargs
                         ) -> List[str]:
        sys_prompt = sys_prompt if isinstance(sys_prompt, str) else sys_prompt.value
        messages = [
            {
                "role": "system",
                "content": sys_prompt
            }
        ]
        if prompt is not None:
            prompt_content = prompt if isinstance(prompt, str) else prompt.value
            messages.append(
                {
                    "role": "user",
                    "content": prompt_content
                }
            )
        responses = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            n=n_choices,
            *args, **kwargs
        )
        results = []
        for i in range(len(responses.choices)):
            response = responses.choices[i].message.content
            results.append(response)
        return results
    
    def gen_from_contexts(self,
                          contexts: List[Context],
                          sys_prompt: str | PromptTemplate = "You are an AI assistant.",
                          n_choices: int = 1,
                          legal_actions: List[str] = ["reasoning", "search", "gen_idea"],
                          *args, **kwargs
                          ) -> List[Context]:
        sys_prompt = sys_prompt if isinstance(sys_prompt, str) else sys_prompt.value
        messages = [
            {
                "role": "system",
                "content": sys_prompt
            }
        ]
        for context in contexts:
            messages.append(
                {
                    "role": "assistant",
                    "content": context.value
                }
            )
            if context.observation is None:
                continue
            messages.append(
                {
                    "role": "user",
                    "content": context.observation
                }
            )
        responses = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            n=n_choices,
            *args, **kwargs,
            stop=["[END]"]
        )
        results = []
        for i in range(len(responses.choices)):
            result = responses.choices[i].message.content + "[END]"
            context = PromatParser.to_context(result)
            if context is not None and context.key in legal_actions:
                results.append(context)
        if len(results) == n_choices:
            return results
        return results + self.gen_from_contexts(contexts=contexts,
                                                sys_prompt=sys_prompt,
                                                n_choices=n_choices - len(results))