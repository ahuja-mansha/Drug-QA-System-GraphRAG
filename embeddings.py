from sentence_transformers import SentenceTransformer
import numpy as np

# Load once globally
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def embed_text(text: str) -> np.ndarray:
    """Generate embedding for input text."""
    return embedding_model.encode(text).tolist()
