# Kubernetes Ingress — Strict CORS Remediation (P2, Infra-level)

## Problem

Probely DAST flagged the production ingress as returning `Access-Control-Allow-Origin: *` at the edge, even though the FastAPI application layer was later hardened with a strict allow-list (`allow_origin_regex` in `/app/backend/server.py`).

When the Kubernetes ingress (or nginx-ingress-controller) sets a wildcard CORS header, it takes precedence over the app's stricter header in some edge configurations — or, worse, duplicates the header, causing browsers to reject the response. Either way, the wildcard is an audit finding.

## Scope

This change is **infrastructure-level** and must be applied by an Emergent platform engineer with cluster write access. The main agent cannot mutate `Ingress` or `ConfigMap` resources from inside the application container.

## Current behavior (what Probely saw)

```http
HTTP/2 200
access-control-allow-origin: *
access-control-allow-methods: *
access-control-allow-headers: *
```

## Desired behavior

```http
HTTP/2 200
vary: origin
access-control-allow-origin: https://solomonai.us
access-control-allow-credentials: true
access-control-allow-methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
access-control-allow-headers: Authorization, Content-Type, X-Requested-With
```

## Fix — `Ingress` annotations

Add the following annotations to the production `Ingress` object that routes `solomonai.us` → `solomon-frontend` / `solomon-backend` services:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: solomon-prod
  annotations:
    # Delegate CORS entirely to the FastAPI layer (RECOMMENDED)
    nginx.ingress.kubernetes.io/enable-cors: "false"

    # OR, if you want to enforce CORS at the edge (defense-in-depth):
    # nginx.ingress.kubernetes.io/enable-cors: "true"
    # nginx.ingress.kubernetes.io/cors-allow-origin: "https://solomonai.us,https://www.solomonai.us,https://exec-metrics-hub.preview.emergentagent.com"
    # nginx.ingress.kubernetes.io/cors-allow-credentials: "true"
    # nginx.ingress.kubernetes.io/cors-allow-methods: "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    # nginx.ingress.kubernetes.io/cors-allow-headers: "Authorization, Content-Type, X-Requested-With"
    # nginx.ingress.kubernetes.io/cors-max-age: "600"

    # Strip any wildcard header that might leak through from upstream
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_clear_headers "Access-Control-Allow-Origin";
      more_clear_headers "Access-Control-Allow-Methods";
      more_clear_headers "Access-Control-Allow-Headers";
```

### Which option to pick?

- **Prefer "disable edge CORS" (option A above).** The FastAPI middleware already enforces a strict allow-list. One source of truth prevents drift.
- Only fall back to option B if the Emergent platform requires edge-level CORS for some gateway-level feature (WAF, caching, etc.).

## Verification after apply

```bash
# 1. Wildcard must be gone
curl -sI -H "Origin: https://evil.example" https://solomonai.us/api/health \
  | grep -i "access-control-allow-origin"
# Expected: empty output (no header) OR explicit strict value — never "*"

# 2. Legit origin must still pass
curl -sI -H "Origin: https://solomonai.us" https://solomonai.us/api/health \
  | grep -i "access-control-allow-origin"
# Expected: access-control-allow-origin: https://solomonai.us
```

## Application-level state (already done, no further action)

- `/app/backend/server.py` — `CORSMiddleware` uses strict `allow_origin_regex`
- `/app/backend/core/__init__.py` — Session TTL + `SameSite=Lax` cookies

## Rollout checklist

- [ ] Platform engineer edits the production `Ingress` in the cluster
- [ ] Apply via `kubectl apply -f` or GitOps pipeline
- [ ] Run the two verification `curl` commands above
- [ ] Re-run Probely scan; confirm CORS finding is closed
