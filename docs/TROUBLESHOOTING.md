# BiztelAI Manufacturing SOP AI Copilot — Troubleshooting & Runbook

## 1. Upstash Redis TLS (`rediss://`) Setup
### Problem:
Celery worker fails to connect to Upstash Redis with SSL verification error:
`ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED]`

### Solution:
Ensure `app/config.py` uses the built-in helper:
```python
if is_upstash_redis(REDIS_URL):
    CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE}
    CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": ssl.CERT_NONE}
```
In `.env`, use the full connection string:
`REDIS_URL=rediss://default:YOUR_PASSWORD@YOUR_ENDPOINT.upstash.io:6379`

---

## 2. HuggingFace Model Cache & Offline Sandbox
### Problem:
Loading `SentenceTransformer` or `CrossEncoder` hangs or times out in environments without direct internet access.

### Solution:
Models are pre-cached in `~/.cache/huggingface/hub`. The service code utilizes:
```python
try:
    model = SentenceTransformer(model_name, local_files_only=True)
except Exception:
    model = SentenceTransformer(model_name)
```
This guarantees instant startup without outbound network requests.

---

## 3. Database Connection in Local SQLite Mode
### Problem:
Running scripts without Docker postgres causes connection failure.

### Solution:
Pass `--sqlite` to scripts:
```bash
python scripts/seed_sample_data.py --sqlite
python scripts/run_evaluation.py --sqlite --mock-llm
```

---

## 4. Ingestion Worker Not Consuming Tasks
### Check:
1. Ensure Celery is running:
   ```bash
   celery -A app.tasks.celery_app.celery worker --loglevel=info
   ```
2. Verify Redis broker connectivity:
   ```bash
   python -c "import redis; r = redis.from_url('YOUR_REDIS_URL'); print(r.ping())"
   ```

