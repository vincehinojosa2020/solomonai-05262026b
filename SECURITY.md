# Solomon AI — Security Policy (CISO Edition)

Last updated: **Apr 22, 2026** · Owner: Platform / Security

This is the executive-level playbook. If you read **only one thing** before shipping code, read this. Detailed technical writeups are linked inline.

---

## 1. Non-negotiables (enforced by CI)

| # | Control | Enforcement | Regression signal |
|---|---|---|---|
| 1 | Dependency floor for every CVE we've ever fixed | `backend/tests/test_security_baseline.py` — pytest blocks merge | "SECURITY REGRESSION — `<pkg>`==`<ver>` is below the required minimum" |
| 2 | Denylisted packages (`python-jose`, `ecdsa`) cannot be re-installed | same test file | "is installed but is on the security denylist" |
| 3 | Python runtime >= 3.11 | same test file | "Python X.Y is below the minimum supported 3.11" |
| 4 | No known-exploitable CVEs in installed deps | `pip-audit --strict` in `.github/workflows/security.yml` | Pipeline fails with CVE number + fixed version |
| 5 | No Snyk HIGH / CRITICAL SCA finding | `snyk test --severity-threshold=high --fail-on=upgradable` | Snyk action annotates the PR with vulnerable package |
| 6 | No Snyk Code HIGH SAST finding | `snyk code test --severity-threshold=high` | Snyk annotates PR with file + line |
| 7 | No HIGH/CRITICAL yarn audit | `yarn npm audit --severity high` | Audit report in workflow logs |
| 8 | Strict CORS allow-list (no wildcards) | `backend/server.py` CORSMiddleware uses `allow_origin_regex` — Probely DAST verifies post-deploy | Probely scan report |
| 9 | TLS 1.2+ only, secure ciphers | Nginx config + Probely DAST | Probely scan report |
| 10 | CSP + X-Frame-Options + HSTS + X-Content-Type-Options | Middleware in `backend/server.py` | Probely scan report |

**Blocking merge:** all of the above. If CI goes red on security, the PR does not merge. Full stop.

---

## 2. Code-level invariants (enforced at review)

### Frontend (`/app/frontend/src/utils/sanitize.js` — single source of truth)
- **All** `<a href={...}>` from dynamic state → wrap in `safeHref()`
- **All** `<img src={...}>` from dynamic state → wrap in `safeImgSrc()`
- **All** `<iframe src={...}>` → wrap in `safeIframeSrc(url, allowedHostList)` — host allowlist mandatory
- **All** `window.location.href = x` → wrap in `safeRedirect()` (rejects external URLs)
- **All** `mailto:` / `tel:` hrefs → wrap in `safeMailto()` / `safeTel()`
- **Any** `dangerouslySetInnerHTML` → must go through `DOMPurify.sanitize()`
- **Blob downloads** (`URL.createObjectURL`) → content-type validated via `blobFromResponse(response, ['application/pdf'])`
- **Stripe / external redirects** → `safeStripeCheckoutUrl()` or similar URL-parser-based hostname check, **never** `startsWith()`

If a reviewer sees a raw sink in a PR, reject it — every new XSS vector in the Snyk Apr 2026 report traced to a developer inlining a regex instead of importing the util.

### Backend
- **AuthN** — `PyJWT` only (see denylist for why). Always pass `algorithms=["HS256"]` explicitly; never `algorithms=["none"]`.
- **Path handling** — any user-controlled path → `Path(...).resolve().is_relative_to(base_dir)` check. Never string concat.
- **Shell commands** — `subprocess.run([list], shell=False)` with arg arrays, never `shell=True` or string templates.
- **Rate limiting** — any endpoint that executes heavy work (AST, LLM, DB aggregation) → `express-rate-limit` (dev plugin) or FastAPI slowapi (prod).
- **Env vars** — secrets read via `dotenv_values(Path(...))` when the pod env may have conflicting defaults (see `backend/routes/stripe_elements.py` for why).
- **CORS** — strict `allow_origin_regex` in `server.py`. Never `allow_origins=["*"]` with `allow_credentials=True`.
- **MongoDB responses** — every Pydantic response model or `find({}, {"_id": 0})` projection. Never return a bare document.

---

## 3. Scan cadence

| Tool | Scope | Frequency | Owner |
|---|---|---|---|
| Snyk Open Source (SCA) | `backend/requirements.txt`, `frontend/package.json` | Every PR + nightly | Platform |
| Snyk Code (SAST) | All source | Every PR | Platform |
| Probely (DAST) | Production URL | Weekly | Security |
| pip-audit | `backend/requirements.txt` | Every PR (CI) | Platform |
| yarn npm audit | `frontend/package.json` | Every PR (CI) | Platform |
| Pen test | Full app | Quarterly | External vendor |

## 4. Incident / Stale-scan protocol

When a Snyk/Probely/pen-test report lands with findings, before paging engineering:

1. **Confirm the scan ran against `HEAD`** (branch + commit SHA). Our requirements.txt carries already-patched versions — scans of stale commits will flag fixed issues. Runtime `Python 3.7` in the report banner is a tell (we run 3.11). Ask for a rescan on current commit first.
2. If findings persist on HEAD → log in the security tracker, assign priority by CVSS × exploit maturity.
3. P0 (HIGH + mature exploit): patch + deploy within 24h, then run the SECURITY_FLOOR regression test to lock it in.
4. P1 (HIGH + PoC): patch within 7 days.
5. P2 (MEDIUM): batch into the next sprint.

## 5. Past incidents (feeds the floor)

| Date | Finding | Fixed in | Locked in by |
|---|---|---|---|
| 2026-02-20 | Snyk SCA — 58 deps (aiohttp, cryptography, PyJWT, urllib3, requests, pyasn1, zipp, python-jose, ecdsa) | `backend/requirements.txt` v2 | `test_security_baseline.py::SECURITY_FLOOR` + `DENYLIST` |
| 2026-02-20 | Snyk SAST — 71 XSS / open-redirect / path-traversal | `frontend/src/utils/sanitize.js`, DOMPurify, safe* helpers | Code review + Snyk Code CI gate |
| 2026-02-20 | Probely DAST — wildcard CORS, weak TLS, missing CSP, clickjacking | `backend/server.py` middleware, Nginx config | Probely weekly rescan |
| 2026-04-20 | Snyk SAST — 27 new XSS / open-redirect across 19 files | Centralized `safeIframeSrc`, `safeImgSrc`, `safeMailto`, `safeTel`, `safeStripeCheckoutUrl`, `blobFromResponse` | Code review + lint |
| 2026-04-22 | Snyk SCA — same 42 findings re-reported | **False alarm** — scan ran against stale commit, current HEAD already at fixed versions | Dependency baseline test makes this impossible to regress |

## 6. Response templates

**To execs asking "is this finding real?"**
> The Snyk report lists `Python 3.7.17` as the runtime; we run Python 3.11. Our current `requirements.txt` at HEAD carries `aiohttp 3.13.5`, `cryptography 46.0.7`, `PyJWT 2.12.1` — all above Snyk's fix thresholds. The scan ran against an older commit. Requesting a rescan at `<commit SHA>` will return 0 findings. Our `test_security_baseline.py` CI gate makes regression impossible.

**To auditors asking "how do you prevent regression?"**
> Three layers: (1) pytest in CI enforces a per-package minimum version floor derived from every CVE we've ever patched — a downgrade fails the build; (2) pip-audit runs `--strict` in the same workflow; (3) Snyk Open Source + Snyk Code are blocking checks on every PR with severity-threshold=high. All three gates must be green to merge to main.

---

## 7. Key files

- `/app/backend/tests/test_security_baseline.py` — the floor
- `/app/.github/workflows/security.yml` — CI gates
- `/app/frontend/src/utils/sanitize.js` — frontend invariants
- `/app/backend/server.py` — CORS, CSP, middleware
- `/app/STRIPE_PAYMENT_REQUEST_INTEGRATION.md` — live-key activation guide
- `/app/K8S_INGRESS_CORS_REMEDIATION.md` — infra CORS remediation
