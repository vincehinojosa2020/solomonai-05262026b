#!/usr/bin/env bash
#
# Solomon AI — MongoDB backup driver
# ===================================
# Wraps `mongodump` with sane defaults, gzip + timestamp + retention,
# and an upload hook for object storage. Designed to run from cron OR as a
# one-shot during a deploy/migration.
#
# Usage:
#   ./scripts/backup.sh                     # backup → /var/backups/solomon
#   ./scripts/backup.sh --target /mnt/foo   # custom dir
#   ./scripts/backup.sh --retain-days 30    # custom retention
#   ./scripts/backup.sh --upload s3         # also upload to S3
#                                           # (set S3_BUCKET, S3_PREFIX in env)
#
# Cron suggestion (hourly point-in-time, 30-day retention, S3 sync):
#   0 * * * * /app/backend/scripts/backup.sh --retain-days 30 --upload s3 \
#               >> /var/log/solomon-backup.log 2>&1
#
# When you migrate to MongoDB Atlas, this script becomes the local-disk
# fallback — Atlas continuous backups (point-in-time-restore, RPO 1 min)
# remain primary.

set -euo pipefail

# ── Args ──────────────────────────────────────────────────────────────
TARGET="/var/backups/solomon"
RETAIN_DAYS=14
UPLOAD=""
ENV_FILE="/app/backend/.env"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)        TARGET="$2"; shift 2 ;;
        --retain-days)   RETAIN_DAYS="$2"; shift 2 ;;
        --upload)        UPLOAD="$2"; shift 2 ;;
        --env)           ENV_FILE="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,30p' "$0"
            exit 0
            ;;
        *)
            echo "Unknown arg: $1" >&2
            exit 2
            ;;
    esac
done

# ── Load env (MONGO_URL + DB_NAME) ───────────────────────────────────
if [[ -f "$ENV_FILE" ]]; then
    # shellcheck disable=SC2046
    set -a; source "$ENV_FILE"; set +a
fi

if [[ -z "${MONGO_URL:-}" ]]; then
    echo "FATAL: MONGO_URL not set (looked at $ENV_FILE)" >&2
    exit 1
fi
DB_NAME="${DB_NAME:-test_database}"

# ── Names ─────────────────────────────────────────────────────────────
TS="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="$TARGET/solomon-$DB_NAME-$TS.archive.gz"
mkdir -p "$TARGET"

echo "──────────────────────────────────────────────────────────────"
echo " Solomon AI MongoDB backup"
echo "   db:        $DB_NAME"
echo "   target:    $ARCHIVE"
echo "   retain:    ${RETAIN_DAYS}d"
echo "   upload:    ${UPLOAD:-none}"
echo "──────────────────────────────────────────────────────────────"

# ── Run mongodump ─────────────────────────────────────────────────────
# --archive + --gzip = single compressed file. Streams, so RAM-bounded.
START=$(date +%s)
mongodump \
    --uri="$MONGO_URL" \
    --db="$DB_NAME" \
    --archive="$ARCHIVE" \
    --gzip \
    --quiet
END=$(date +%s)
DUR=$((END - START))
SIZE_BYTES=$(stat -c '%s' "$ARCHIVE" 2>/dev/null || stat -f '%z' "$ARCHIVE")
SIZE_MB=$((SIZE_BYTES / 1024 / 1024))

echo "✓ dump completed in ${DUR}s (${SIZE_MB}MB)"

# ── Integrity check ───────────────────────────────────────────────────
# `mongorestore --dryRun` parses the archive and reports any corruption.
mongorestore --archive="$ARCHIVE" --gzip --dryRun --quiet \
    >> "$TARGET/.last-verify.log" 2>&1 || {
        echo "✗ archive failed integrity check — aborting upload + retention" >&2
        exit 3
    }
echo "✓ archive integrity verified"

# ── Upload (optional) ─────────────────────────────────────────────────
if [[ "$UPLOAD" == "s3" ]]; then
    if [[ -z "${S3_BUCKET:-}" ]]; then
        echo "✗ --upload s3 requires S3_BUCKET in env" >&2
        exit 4
    fi
    S3_KEY="${S3_PREFIX:-solomon-ai/backups}/$(basename "$ARCHIVE")"
    aws s3 cp "$ARCHIVE" "s3://$S3_BUCKET/$S3_KEY" --quiet
    echo "✓ uploaded → s3://$S3_BUCKET/$S3_KEY"
fi

# ── Retention ─────────────────────────────────────────────────────────
# Delete archive files older than RETAIN_DAYS. Never touch other files.
find "$TARGET" -maxdepth 1 -name "solomon-*.archive.gz" -type f \
    -mtime +"$RETAIN_DAYS" -print -delete | sed 's/^/  pruned: /' || true

echo "──────────────────────────────────────────────────────────────"
echo " ✓ DONE  — archive=$ARCHIVE  size=${SIZE_MB}MB  duration=${DUR}s"
echo "──────────────────────────────────────────────────────────────"

# ── Restore reminder (printed once a month, always at the bottom) ────
cat <<EOM

To restore from this archive (TEST against a staging DB first!):
   mongorestore --uri="<DEST_MONGO_URL>" --archive="$ARCHIVE" --gzip \
                --drop --nsInclude="$DB_NAME.*"

Recovery objectives baseline (with this script alone):
   RPO ≈ 1 hour  (when run hourly)
   RTO ≈ 5–15 min on a 1GB dump
   For RPO ≤ 1 minute, migrate to MongoDB Atlas continuous backups.
EOM
