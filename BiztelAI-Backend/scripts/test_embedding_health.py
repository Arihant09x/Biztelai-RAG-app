#!/usr/bin/env python3
"""Dynamic Embedding Health and Dimension Validation Script.

Verifies local Sentence Transformers embedding generation, vector dimension,
normalization properties, and semantic similarity scoring.
Exits with 0 on success, 1 on failure.
"""

import math
import os
import sys
import time
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

import numpy as np
from app.services.embedding_service import EmbeddingService


def run_embedding_health_test() -> int:
    print("=" * 70)
    print("BIZTELAI MANUFACTURING SOP COPILOT - EMBEDDING HEALTH TEST")
    print("=" * 70)

    expected_dim = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    print(f"Target Embedding Model: {model_name}")
    print(f"Expected Dimension:    {expected_dim}")
    print("-" * 70)
    print("Initializing embedding service and computing test vectors...")

    start_time = time.time()
    try:
        service = EmbeddingService()

        test_sentences = [
            "Emergency stop button procedure and lockout tagout electrical isolation.",
            "Inspect hydraulic spindle pressure gauge and verify 50 bar operating limit.",
            "Chocolate cake recipe with flour and sugar.",
        ]

        vectors = service.provider.embed_texts(test_sentences)
        latency_ms = round((time.time() - start_time) * 1000, 2)

        # 1. Dimension check
        for idx, vec in enumerate(vectors):
            if len(vec) != expected_dim:
                print(f"\n[FAIL] Vector {idx} dimension mismatch: got {len(vec)}, expected {expected_dim}")
                return 1

        # 2. Normalization check
        for idx, vec in enumerate(vectors):
            norm = np.linalg.norm(vec)
            if not math.isclose(norm, 1.0, rel_tol=1e-3):
                print(f"\n[FAIL] Vector {idx} not normalized: magnitude = {norm:.4f} (expected 1.0)")
                return 1

        # 3. Semantic similarity verification
        # Sentence 0 and 1 are both industrial SOP procedures, Sentence 2 is unrelated
        sim_sop = float(np.dot(vectors[0], vectors[1]))
        sim_cake = float(np.dot(vectors[0], vectors[2]))

        print(f"Embedding Generation Latency: {latency_ms} ms")
        print(f"Similarity (SOP 1 vs SOP 2):  {sim_sop:.4f}")
        print(f"Similarity (SOP 1 vs Cake):   {sim_cake:.4f}")

        if sim_sop <= sim_cake:
            print("\n[FAIL] Semantic relationship test failed: unrelated sentence scored higher than SOP pair.")
            return 1

        print("\n[SUCCESS] Embedding model is healthy, properly normalized, and dimension verified!")
        print("=" * 70)
        return 0

    except Exception as e:
        print(f"\n[FAIL] Embedding health check threw exception: {type(e).__name__}: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(run_embedding_health_test())

