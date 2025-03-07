from typing import List

from chromadb import PersistentClient
from abc import ABC, abstractmethod

class RAG(ABC):
    @abstractmethod
    def query(self, q: str) -> str:
        pass


class VanillaRAG(RAG):
    def __init__(self) -> None:
        client = PersistentClient()
        self.collection = client.get_or_create_collection("rag")

    def add(self, ids: list[str], documents: list[str], metadatas: list[dict] = None):
        self.collection.add(ids=ids, documents=documents, metadatas=metadatas) 

    def query(self, q: str, n_results: int = 1) -> str:
        results = self.collection.query(query_texts=[q], n_results=n_results)
        response = ""
        for i in range(n_results):
            response += f"Document {i+1}:\n"
            response += f"ID: {results['ids'][0][i]}\n"
            response += "Metadata:\n"
            for key, value in results["metadatas"][0][i].items():
                response += f"  {key}: {value}\n"
            response += f"Abstract:\n{results['documents'][0][i]}\n"
            response += "=" * 100 + "\n"
        return response
    
    def get(self, ids: list[str]):
        return self.collection.get(ids=ids)