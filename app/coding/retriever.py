"""
Hybrid Retriever: TF-IDF + mxbai-embed-large embeddings
Finds candidate ICD-10-AM codes for clinical text
"""
import json
import requests
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Optional

from app.config import settings
from app.coding.sanitizer import sanitize_text


class HybridRetriever:
    """Hybrid retrieval using TF-IDF and semantic embeddings"""

    def __init__(self):
        self.codes: List[Dict] = []
        self.embeddings: Optional[np.ndarray] = None
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self._initialized = False

    def initialize(self):
        """Load codes and build indexes (call once at startup)"""
        if self._initialized:
            return

        print("Loading ED Short List codes...")
        self.codes = self._load_codes()
        print(f"Loaded {len(self.codes)} codes")

        print("Building TF-IDF index...")
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words='english',
            max_features=5000
        )
        corpus = [c['search_text'] for c in self.codes]
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

        print("Loading embeddings cache...")
        self._load_embeddings()

        self._initialized = True
        print("Retriever ready!")

    def _load_codes(self) -> List[Dict]:
        """Load ICD-10-AM codes from JSON file"""
        with open(settings.ED_CODES_FILE, 'r') as f:
            return json.load(f)

    def _load_embeddings(self):
        """Load pre-built embeddings from cache"""
        if settings.EMBEDDINGS_CACHE.exists():
            self.embeddings = np.load(settings.EMBEDDINGS_CACHE)
            if len(self.embeddings) == len(self.codes):
                print(f"Loaded {len(self.embeddings)} cached embeddings")
                return

        print("WARNING: Embeddings cache not found or mismatched!")
        self.embeddings = None

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding from Ollama API"""
        try:
            clean_text = sanitize_text(text)
            if len(clean_text) > 2000:
                clean_text = clean_text[:2000]

            url = f"{settings.OLLAMA_URL}/api/embeddings"
            resp = requests.post(
                url,
                json={"model": settings.EMBED_MODEL, "prompt": clean_text},
                timeout=60
            )
            if resp.status_code == 200:
                return np.array(resp.json()["embedding"])
            else:
                print(f"Embedding API error: {resp.status_code}")
        except Exception as e:
            print(f"Embedding error: {e}")
        return None

    def find_candidates(self, clinical_text: str, top_k: int = 50) -> List[Dict]:
        """
        Find top-k candidate codes using hybrid retrieval

        Args:
            clinical_text: The clinical notes to code
            top_k: Number of candidates to return

        Returns:
            List of candidate codes with scores
        """
        if not self._initialized:
            self.initialize()

        # Sanitize input
        clean_text = sanitize_text(clinical_text)

        # TF-IDF retrieval
        query_vec = self.vectorizer.transform([clean_text])
        tfidf_sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        tfidf_top = tfidf_sims.argsort()[-settings.TOP_K_TFIDF:][::-1]

        # Embedding retrieval (if available)
        embed_top = []
        embed_sims = np.zeros(len(self.codes))

        if self.embeddings is not None:
            query_emb = self._get_embedding(clean_text)
            if query_emb is not None:
                embed_sims = cosine_similarity([query_emb], self.embeddings).flatten()
                embed_top = embed_sims.argsort()[-settings.TOP_K_EMBED:][::-1]

        # Merge results
        merged = {}
        for idx in tfidf_top:
            code = self.codes[idx]['code']
            if code not in merged:
                merged[code] = {
                    'idx': idx,
                    'tfidf_score': float(tfidf_sims[idx]),
                    'embed_score': float(embed_sims[idx]),
                    'source': 'tfidf'
                }

        for idx in embed_top:
            code = self.codes[idx]['code']
            if code not in merged:
                merged[code] = {
                    'idx': idx,
                    'tfidf_score': float(tfidf_sims[idx]),
                    'embed_score': float(embed_sims[idx]),
                    'source': 'embed'
                }
            else:
                merged[code]['source'] = 'both'

        # Score and sort
        def combined_score(item):
            return (item['tfidf_score'] * 2 + item['embed_score']) / 2

        sorted_codes = sorted(
            merged.items(),
            key=lambda x: combined_score(x[1]),
            reverse=True
        )

        # Build candidate list
        candidates = []
        for code, info in sorted_codes[:top_k]:
            idx = info['idx']
            candidates.append({
                'code': self.codes[idx]['code'],
                'descriptor': self.codes[idx]['descriptor'],
                'term': self.codes[idx]['term'],
                'conditions': self.codes[idx]['conditions'][:150] if self.codes[idx]['conditions'] else '',
                'score': combined_score(info),
                'source': info['source'],
                'complexity': self.codes[idx].get('complexity', 1)
            })

        return candidates


# Singleton instance
retriever = HybridRetriever()
