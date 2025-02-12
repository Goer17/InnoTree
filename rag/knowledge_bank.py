import json
from chromadb import PersistentClient
from tqdm import tqdm

from utils.log import logger

def init_bank():
    client = PersistentClient()
    collection = client.get_or_create_collection("papers")
    bs = 16
    with open("dataset/arxiv.jsonl", "r") as f:
        for t in tqdm(range(10000), unit="batch"):
            ids, metadatas, documents = [], [], []
            for i in range(bs):
                try:
                    line: dict = json.loads(f.readline())
                    pid, title, doc = line['id'], line['title'], line['abstract']
                    doi = line.get("doi")
                    if doi is None: doi = "empty"
                    ids.append(pid)
                    metadatas.append(
                        {
                            "title": title,
                            "doi": doi
                        }
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.info(str(e))
            try:
                collection.add(
                    ids=ids, metadatas=metadatas, documents=documents
                )
            except Exception as e:
                logger.info(f"{str(e)}")
        