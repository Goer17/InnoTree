from abc import ABC, abstractmethod
from agents.general import (
    LLMEngine
)
from chromadb import PersistentClient

class RAG(ABC):
    def __init__(self, *args, **kwargs):
        pass
    
    @abstractmethod
    def run(self, query: str) -> str:
        pass

from openai import Client

class TestRAG(RAG):
    def __init__(self,
                 engine: LLMEngine,
                 *args,
                 **kwargs
                 ):
        sys_prompt = (
            "You are a search engine. When I provide you with a query, you should respond with relevant research papers.\n"
            "The response format should be as follows:\n"
            "[1] Title\nContent\nReference: ... (in MLA format)\n"
            "[2] Title\nContent\nReference: ... (in MLA format)\n"
            "[3] Title\nContent\nReference: ... (in MLA format)\n"
            "...\n"
        )
        self.engine = engine
        self.sys_prompt = sys_prompt
        client = PersistentClient()
        self.collections = client.get_collection("papers")

    def run(self, query: str) -> str:
        results = self.collections.query(query_texts=[query])
        response = ""
        for i in range(len(results["ids"])):
            response += (
                f"title: {results['metadatas'][i]['title']}\n"
                f"doi: {results['metadatas'][i]['doi']}\n"
                f"abstract: {results['documents'][i]}\n\n"
            )
        
        return response
            