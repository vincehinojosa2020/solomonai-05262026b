"""Production Gunicorn config for the Solomon AI backend.

BLOCKER #7 from production audit: replace `uvicorn --workers 1 --reload`
(dev mode, 1 worker, single event loop) with gunicorn supervising N
UvicornWorker processes so Sunday-morning concurrency doesn't melt one
worker.

USAGE
=====
    cd /app/backend
    gunicorn server:app -c gunicorn.conf.py

ENV OVERRIDES
=============
    GUNICORN_WORKERS              default: 4
    GUNICORN_THREADS              default: 1   (UvicornWorker is async — keep low)
    GUNICORN_BIND                 default: 0.0.0.0:8001
    GUNICORN_LOG_LEVEL            default: info
    GUNICORN_TIMEOUT              default: 60  (seconds; Stripe round-trips can be slow)
    GUNICORN_MAX_REQUESTS         default: 10000  (recycle workers periodically)
    GUNICORN_MAX_REQUESTS_JITTER  default: 1000

NOTES
=====
* `--reload` is NEVER set in production.
* Workers should be approximately (2 * num_cpu_cores). On a 2-core box,
  start with 4. Tune with load testing, not guessing.
* On Kubernetes, run a single gunicorn process per pod and let HPA scale
  the pod count. Don't both gunicorn-fork AND k8s-replicate.
"""
import os

# ── Bind ───────────────────────────────────────────────────────────────
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8001")

# ── Workers ────────────────────────────────────────────────────────────
workers = int(os.environ.get("GUNICORN_WORKERS", "4"))
worker_class = "uvicorn.workers.UvicornWorker"
threads = int(os.environ.get("GUNICORN_THREADS", "1"))

# ── Timeouts ───────────────────────────────────────────────────────────
# Long enough for Stripe round-trips + Mongo aggregations, short enough
# that hung workers get killed before they wedge the process pool.
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
graceful_timeout = 30
keepalive = 5

# ── Worker lifecycle ───────────────────────────────────────────────────
# Recycle each worker after N requests to bound memory leaks. Jitter so
# they don't all recycle at the same instant.
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "10000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "1000"))

# ── Logging ────────────────────────────────────────────────────────────
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
accesslog = "-"   # stdout — collect via your platform's log aggregator
errorlog = "-"
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" rt=%(L)s'
)

# ── Hardening ──────────────────────────────────────────────────────────
proc_name = "solomon-api"
preload_app = False  # let each worker initialize its own DB/Stripe clients
forwarded_allow_ips = "*"  # behind a trusted ingress / Cloudflare

# Refuse to start if ENVIRONMENT=production and someone tries to enable reload
def on_starting(server):
    if os.environ.get("ENVIRONMENT", "").lower() == "production":
        if os.environ.get("GUNICORN_RELOAD") == "true":
            raise RuntimeError("--reload is forbidden in production.")
        if workers < 2:
            server.log.warning(f"WORKERS={workers} in production — recommend >= 2")
