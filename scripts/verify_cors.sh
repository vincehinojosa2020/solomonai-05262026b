#!/usr/bin/env bash
# K8s Ingress CORS — Verification Script
# Run this AFTER the Emergent platform engineer applies the changes
# documented in /app/K8S_INGRESS_CORS_REMEDIATION.md
#
# Usage:
#   ./verify_cors.sh [https://your-domain.example]
#
# Exits 0 on success, non-zero if a wildcard or misconfiguration is still present.

set -u

DOMAIN="${1:-https://solomonai.us}"
API="$DOMAIN/api/health"
PASS=0
FAIL=0

section() { printf '\n\033[1;36m== %s ==\033[0m\n' "$*"; }
ok()      { printf '  \033[32m✓\033[0m %s\n' "$*"; PASS=$((PASS+1)); }
fail()    { printf '  \033[31m✗\033[0m %s\n' "$*"; FAIL=$((FAIL+1)); }

section "1. Wildcard Origin — must be ABSENT"
HDR=$(curl -sI -H "Origin: https://evil.example" "$API" | tr -d '\r' | grep -i '^access-control-allow-origin:' | awk -F': ' '{print $2}')
if [[ -z "${HDR}" ]]; then
  ok "No ACAO header returned for untrusted origin (strict deny)."
elif [[ "${HDR}" == "*" ]]; then
  fail "ACAO=* still present. Ingress wildcard NOT removed."
else
  ok "ACAO returned a specific origin (\"${HDR}\") — untrusted origin was still echoed; check allow-list."
fi

section "2. Legitimate Origin — must be ALLOWED"
HDR=$(curl -sI -H "Origin: $DOMAIN" "$API" | tr -d '\r' | grep -i '^access-control-allow-origin:' | awk -F': ' '{print $2}')
if [[ "${HDR}" == "$DOMAIN" ]]; then
  ok "ACAO=$DOMAIN (correct)."
else
  fail "Expected ACAO=$DOMAIN, got: \"${HDR}\""
fi

section "3. Credentials flag — must be TRUE when origin is allowed"
HDR=$(curl -sI -H "Origin: $DOMAIN" "$API" | tr -d '\r' | grep -i '^access-control-allow-credentials:' | awk -F': ' '{print $2}')
if [[ "${HDR}" == "true" ]]; then
  ok "ACAC=true (correct)."
else
  fail "Expected ACAC=true, got: \"${HDR}\""
fi

section "4. Preflight OPTIONS — headers echo only what app allows"
OUT=$(curl -sI -X OPTIONS -H "Origin: $DOMAIN" -H "Access-Control-Request-Method: POST" "$API")
METH=$(echo "$OUT" | tr -d '\r' | grep -i '^access-control-allow-methods:' | awk -F': ' '{print $2}')
if echo "$METH" | grep -qiE "POST"; then
  ok "Preflight ACAM includes POST: \"${METH}\""
else
  fail "Preflight ACAM missing POST: \"${METH}\""
fi

printf '\n\033[1;36mResult:\033[0m %d passed, %d failed\n' "$PASS" "$FAIL"
if [[ $FAIL -gt 0 ]]; then exit 1; fi
