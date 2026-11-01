"""
Semantic Matching Pipeline (Stage C)
Computes dense/semantic textual similarity for descriptions, addresses, and remarks.
Supports SentenceTransformers when available, with a resilient Scikit-Learn TF-IDF /
subword cosine similarity fallback.
"""

from typing import Optional, List, Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SemanticMatcher:
    def __init__(self, use_sentence_transformers_if_available: bool = True):
        self._st_model = None
        self._use_st = use_sentence_transformers_if_available
        self._fallback_vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            lowercase=True
        )

    def _get_st_model(self):
        if self._use_st and self._st_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._st_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                self._st_model = False # Mark as unavailable
        return self._st_model if self._st_model is not False else None

    def compute_semantic_similarity(self, text_a: Optional[str], text_b: Optional[str]) -> Optional[float]:
        """
        Computes semantic similarity score in [0.0, 1.0].
        Returns None if either text is empty.
        """
        if not text_a or not text_b:
            return None
            
        str_a = str(text_a).strip()
        str_b = str(text_b).strip()
        if not str_a or not str_b:
            return None

        # Check identical strings
        if str_a.lower() == str_b.lower():
            return 1.0

        model = self._get_st_model()
        if model:
            try:
                embeddings = model.encode([str_a, str_b], convert_to_numpy=True)
                sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                return round(float(np.clip((sim + 1.0) / 2.0, 0.0, 1.0)), 4)
            except Exception:
                pass

        # Fallback to subword character n-gram TF-IDF cosine similarity
        try:
            tfidf_matrix = self._fallback_vectorizer.fit_transform([str_a, str_b])
            sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return round(float(np.clip(sim, 0.0, 1.0)), 4)
        except Exception:
            return None

