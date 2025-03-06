from openai import Client, AsyncClient
from typing import List, Dict
from functools import cache
from utils.logger import logger

class LLMEngine:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
    ):
        self.client = Client(
            api_key=api_key,
            base_url=base_url
        )
        self.async_client = AsyncClient(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
    
    def generate_text(
            self,
            system_prompt: str,
            messages: List[Dict[str, str]],
            *args, **kwargs
        ) -> List[str]:
        try:
            txts = []
            responses = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *messages
                ],
                *args,
                **kwargs
            )
            for response in responses.choices:
                txts.append(response.message.content)
            return txts
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return None
    
    async def generate_text_async(
            self,
            system_prompt: str,
            messages: List[Dict[str, str]],
            *args, **kwargs
        ) -> List[str]:
        try:
            txts = []
            responses = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *messages
                ],
                *args,
                **kwargs
            )
            for response in responses.choices:
                txts.append(response.message.content)
            return txts
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return None

class LLMEngineFactory:
    @staticmethod
    @cache
    def create_engine(
        api_key: str,
        base_url: str,
        model: str
    ) -> LLMEngine:
        return LLMEngine(
            api_key=api_key,
            base_url=base_url,
            model=model
        )


import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

engines = {
    # Custom
    "custom-gpt-4o-mini": LLMEngineFactory.create_engine(
        api_key=os.getenv("CUSTOM_API_KEY"),
        base_url=os.getenv("CUSTOM_BASE_URL"),
        model="gpt-4o-mini"
    ),
    
    # OpenAI
    "gpt-3.5-turbo": LLMEngineFactory.create_engine(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        model="gpt-3.5-turbo"
    ),
    "gpt-4o": LLMEngineFactory.create_engine(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        model="gpt-4o"
    ),
    "gpt-4o-mini": LLMEngineFactory.create_engine(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        model="gpt-4o-mini"
    ),
    
    # DeepSeek
    "deepseek-chat": LLMEngineFactory.create_engine(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
        model="deepseek-chat"
    ),
    "deepseek-reasoner": LLMEngineFactory.create_engine(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL"),
        model="deepseek-reasoner"
    ),
}