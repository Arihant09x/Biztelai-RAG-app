#!/usr/bin/env python3
"""BiztelAI Manufacturing SOP Copilot - Local Development Server Runner.

Usage:
    python run.py
    python run.py --port 5000 --debug
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env")

# Prime DNS cache on Windows for Neon cloud pooler
try:
    import socket
    socket.getaddrinfo("ep-noisy-bonus-b3o3sjfv-pooler.c-4.ap-southeast-1.aws.neon.tech", 5432, socket.AF_INET)
except Exception:
    pass

from app import create_app
from app.config import get_config


def print_startup_banner(host: str, port: int, cfg):
    """Display startup diagnostics and URL endpoints."""
    db_display = cfg.DATABASE_URL.split("@")[-1] if "@" in cfg.DATABASE_URL else "local"
    redis_display = cfg.REDIS_URL.split("@")[-1] if "@" in cfg.REDIS_URL else "local"

    print("\n" + "=" * 75)
    print("  BIZTELAI MANUFACTURING SOP AI COPILOT BACKEND")
    print("=" * 75)
    print(f"  * Environment:    {cfg.APP_ENV.upper()}")
    print(f"  * Database:       {db_display}")
    print(f"  * Redis Broker:   {redis_display}")
    print(f"  * LLM Provider:   {cfg.LLM_API_BASE_URL} [{cfg.LLM_MODEL}]")
    print(f"  * Embedding:      {cfg.EMBEDDING_MODEL} (dim {cfg.EMBEDDING_DIMENSION})")
    print(f"  * Reranker:       {cfg.RERANKER_MODEL if cfg.RERANKER_ENABLED else 'Disabled'}")
    print("-" * 75)
    print(f"  * Server URL:     http://localhost:{port}")
    print(f"  * Swagger UI:     http://localhost:{port}/api/v1/docs")
    print(f"  * Health Check:   http://localhost:{port}/api/v1/health")
    print(f"  * Readiness:      http://localhost:{port}/api/v1/health/ready")
    print("=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(description="BiztelAI SOP Copilot Server")
    parser.add_argument("--host", default=os.getenv("HOST", "0.0.0.0"), help="Host IP to bind (default: 0.0.0.0 for LAN/mobile access)")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 5000)), help="Port to bind (default: 5000)")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug auto-reloader")
    parser.add_argument("--prod", action="store_true", help="Run in production mode (debug off, multi-threaded)")
    args = parser.parse_args()

    env_name = "production" if args.prod else os.getenv("APP_ENV", "development")
    cfg = get_config(env_name)
    debug_mode = False if args.prod else (args.debug or cfg.DEBUG)

    app = create_app()
    print_startup_banner(args.host, args.port, cfg)

    # Pre-warm SentenceTransformer embedding model to eliminate query cold-start latency
    print("  * Pre-warming SentenceTransformer embedding model in memory...")
    try:
        from app.services.embedding_service import EmbeddingService
        emb = EmbeddingService()
        emb.embed_query("warmup sentence-transformers")
        print("  * SentenceTransformer embedding model pre-warmed successfully.")
    except Exception as e:
        print(f"  * Warning: Embedding pre-warm skipped: {e}")

    # Check if waitress is available for production WSGI on Windows
    if args.prod:
        try:
            import waitress
            print(f"  * Production WSGI: Waitress serving on http://{args.host}:{args.port} (threads=8)")
            waitress.serve(app, host=args.host, port=args.port, threads=8)
            return
        except ImportError:
            pass

    # High-performance threaded Flask runner
    app.run(
        host=args.host,
        port=args.port,
        debug=debug_mode,
        threaded=True,
        use_reloader=False,  # Avoid double model loads in memory
    )


if __name__ == "__main__":
    main()

