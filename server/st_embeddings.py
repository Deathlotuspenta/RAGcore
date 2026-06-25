from langchain_core.embeddings import Embeddings
from typing import List

class STEmbeddings(Embeddings):
    def __init__(self,st_model):
        self.st_model = st_model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.st_model.encode(texts, show_progress_bar=True, batch_size=10,normalize_embeddings=True).tolist()
    
    def embed_query(self, query: str) -> List[float]:
        return self.st_model.encode([query], normalize_embeddings=True).tolist()[0]