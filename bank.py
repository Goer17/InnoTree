import json
from pathlib import Path
from utils.logger import logger
from utils.rag import VanillaRAG
from tqdm import tqdm

def init_vanilla_rag_from_arxiv(lines: int = 100000):
    dataset_path = Path("datasets") / "arxiv.json"
    rag = VanillaRAG()
    with open(dataset_path, "r") as f:
        for _ in tqdm(range(lines), unit="line"):
            try:
                data = json.loads(f.readline())
                ids, documents, metadatas = [data["id"]], [data["abstract"]], [{"title": data["title"]}]
                if len(rag.get(ids)['ids']):
                    continue
                rag.add(ids, documents, metadatas)
            except Exception as e:
                logger.error(f"One error occurred: {e}")

if __name__ == "__main__":
    init_vanilla_rag_from_arxiv()