#!/bin/bash

###############################################################################
# AURORA_LIFE Database Backup Script
#
# Features:
# - Full database dumps with compression
# - Incremental WAL archiving
# - Retention policy (30 days full, 7 days WAL)
# - S3/MinIO upload support
# - Email notifications on failure
# - Backup verification
#
# Usage:
#   ./backup_database.sh [--full|--incremental]
#
# Environment variables required:
#   - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
#   - BACKUP_DIR (default: /backups)
#   - S3_BUCKET (optional for remote backup)
#   - NOTIFY_EMAIL (optional for alerts)
###############################################################################

set -euo pipefail

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/backups}"
FULL_BACKUP_DIR="${BACKUP_DIR}/full"
WAL_BACKUP_DIR="${BACKUP_DIR}/wal"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS_FULL=30
RETENTION_DAYS_WAL=7

# Database connection
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-aurora_life}"
DB_USER="${DB_USER:-postgres}"
PGPASSWORD="${DB_PASSWORD}"
export PGPASSWORD

# S3 configuration (optional)
S3_BUCKET="${S3_BUCKET:-}"
S3_ENDPOINT="${S3_ENDPOINT:-}"

# Logging
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

error() {
    log "ERROR: $1"
    send_notification "AURORA_LIFE Backup Failed" "$1"
    exit 1
}

send_notification() {
    local subject="$1"
    local message="$2"

    if [ -n "${NOTIFY_EMAIL:-}" ]; then
        echo "${message}" | mail -s "${subject}" "${NOTIFY_EMAIL}" || true
    fi

    # Could also integrate with Slack, PagerDuty, etc.
}

# Create backup directories
mkdir -p "${FULL_BACKUP_DIR}" "${WAL_BACKUP_DIR}"

###############################################################################
# Full Backup
###############################################################################
full_backup() {
    log "Starting full database backup..."

    local backup_file="${FULL_BACKUP_DIR}/aurora_life_${TIMESTAMP}.sql.gz"

    # Dump database with compression
    pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=custom \
        --compress=9 \
        --verbose \
        --file="${backup_file}" 2>&1 | tee -a "${LOG_FILE}"

    if [ $? -ne 0 ]; then
        error "pg_dump failed"
    fi

    # Verify backup
    log "Verifying backup integrity..."
    pg_restore --list "${backup_file}" > /dev/null 2>&1

    if [ $? -ne 0 ]; then
        error "Backup verification failed"
    fi

    # Get file size
    local size=$(du -h "${backup_file}" | cut -f1)
    log "Backup completed successfully: ${backup_file} (${size})"

    # Upload to S3 if configured
    if [ -n "${S3_BUCKET}" ]; then
        upload_to_s3 "${backup_file}" "full/$(basename ${backup_file})"
    fi

    # Cleanup old backups
    cleanup_old_backups "${FULL_BACKUP_DIR}" "${RETENTION_DAYS_FULL}"

    log "Full backup process completed"
}

###############################################################################
# Incremental Backup (WAL archiving)
###############################################################################
incremental_backup() {
    log "Starting incremental backup (WAL archiving)..."

    # Archive WAL files
    local wal_files=$(find /var/lib/postgresql/data/pg_wal -type f -name "0*" -mmin -60)

    if [ -z "${wal_files}" ]; then
        log "No new WAL files to archive"
        return 0
    fi

    for wal_file in ${wal_files}; do
        local filename=$(basename "${wal_file}")
        local dest="${WAL_BACKUP_DIR}/${filename}"

        cp "${wal_file}" "${dest}"
        gzip "${dest}"

        log "Archived WAL file: ${filename}"

        # Upload to S3 if configured
        if [ -n "${S3_BUCKET}" ]; then
            upload_to_s3 "${dest}.gz" "wal/${filename}.gz"
        fi
    done

    # Cleanup old WAL archives
    cleanup_old_backups "${WAL_BACKUP_DIR}" "${RETENTION_DAYS_WAL}"

    log "Incremental backup process completed"
}

###############################################################################
# Upload to S3/MinIO
###############################################################################
upload_to_s3() {
    local local_file="$1"
    local s3_key="$2"

    log "Uploading to S3: ${S3_BUCKET}/${s3_key}..."

    if [ -n "${S3_ENDPOINT}" ]; then
        # MinIO or custom S3 endpoint
        aws s3 cp \
            "${local_file}" \
            "s3://${S3_BUCKET}/${s3_key}" \
            --endpoint-url "${S3_ENDPOINT}" \
            2>&1 | tee -a "${LOG_FILE}"
    else
        # AWS S3
        aws s3 cp \
            "${local_file}" \
            "s3://${S3_BUCKET}/${s3_key}" \
            2>&1 | tee -a "${LOG_FILE}"
    fi

    if [ $? -ne 0 ]; then
        error "S3 upload failed for ${s3_key}"
    fi

    log "Successfully uploaded to S3"
}

###############################################################################
# Cleanup old backups
###############################################################################
cleanup_old_backups() {
    local backup_dir="$1"
    local retention_days="$2"

    log "Cleaning up backups older than ${retention_days} days in ${backup_dir}..."

    find "${backup_dir}" -type f -mtime +${retention_days} -delete

    local deleted=$(find "${backup_dir}" -type f -mtime +${retention_days} | wc -l)
    log "Deleted ${deleted} old backup files"
}

###############################################################################
# Database statistics
###############################################################################
collect_stats() {
    log "Collecting database statistics..."

    local stats_file="${BACKUP_DIR}/stats_${TIMESTAMP}.txt"

    {
        echo "=== Database Statistics ==="
        echo "Timestamp: $(date)"
        echo ""

        echo "Database size:"
        psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
            -c "SELECT pg_size_pretty(pg_database_size('${DB_NAME}'));"

        echo ""
        echo "Table sizes:"
        psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
            -c "SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10;"

        echo ""
        echo "Row counts:"
        psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
            -c "SELECT
                    schemaname,
                    relname,
                    n_live_tup
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC
                LIMIT 10;"

    } > "${stats_file}"

    log "Statistics saved to ${stats_file}"
}

###############################################################################
# Main
###############################################################################
main() {
    local backup_type="${1:-full}"

    log "=== AURORA_LIFE Database Backup Started ==="
    log "Backup type: ${backup_type}"
    log "Database: ${DB_NAME} @ ${DB_HOST}:${DB_PORT}"

    # Check prerequisites
    if ! command -v pg_dump &> /dev/null; then
        error "pg_dump not found. Install postgresql-client."
    fi

    # Collect statistics
    collect_stats

    # Perform backup
    case "${backup_type}" in
        --full|full)
            full_backup
            ;;
        --incremental|incremental)
            incremental_backup
            ;;
        *)
            error "Invalid backup type: ${backup_type}. Use --full or --incremental"
            ;;
    esac

    log "=== Backup Completed Successfully ==="

    # Send success notification
    send_notification "AURORA_LIFE Backup Successful" \
        "Backup type: ${backup_type}\nTimestamp: ${TIMESTAMP}\nLog: ${LOG_FILE}"
}

# Run main with all arguments
main "$@"
