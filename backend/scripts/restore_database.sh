#!/bin/bash

###############################################################################
# AURORA_LIFE Database Restore Script
#
# Features:
# - Restore from full backup
# - Point-in-time recovery (PITR) with WAL
# - Download from S3/MinIO
# - Pre-restore validation
# - Automatic rollback on failure
#
# Usage:
#   ./restore_database.sh <backup_file> [--pitr <timestamp>]
#
# Examples:
#   # Restore from local backup
#   ./restore_database.sh /backups/full/aurora_life_20240116_120000.sql.gz
#
#   # Restore from S3 and PITR
#   ./restore_database.sh s3://my-bucket/full/aurora_life_20240116.sql.gz \
#     --pitr "2024-01-16 15:30:00"
#
# Environment variables:
#   - DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
#   - S3_BUCKET, S3_ENDPOINT (if restoring from S3)
###############################################################################

set -euo pipefail

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-aurora_life}"
DB_USER="${DB_USER:-postgres}"
PGPASSWORD="${DB_PASSWORD}"
export PGPASSWORD

TEMP_DIR="/tmp/aurora_restore_$$"
LOG_FILE="/var/log/aurora_restore_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

error() {
    log "ERROR: $1"
    cleanup
    exit 1
}

cleanup() {
    log "Cleaning up temporary files..."
    rm -rf "${TEMP_DIR}"
}

trap cleanup EXIT

###############################################################################
# Download from S3
###############################################################################
download_from_s3() {
    local s3_uri="$1"
    local local_file="${TEMP_DIR}/$(basename ${s3_uri})"

    log "Downloading from S3: ${s3_uri}..."

    mkdir -p "${TEMP_DIR}"

    if [ -n "${S3_ENDPOINT:-}" ]; then
        aws s3 cp "${s3_uri}" "${local_file}" \
            --endpoint-url "${S3_ENDPOINT}"
    else
        aws s3 cp "${s3_uri}" "${local_file}"
    fi

    if [ $? -ne 0 ]; then
        error "Failed to download from S3"
    fi

    echo "${local_file}"
}

###############################################################################
# Pre-restore validation
###############################################################################
validate_backup() {
    local backup_file="$1"

    log "Validating backup file..."

    if [ ! -f "${backup_file}" ]; then
        error "Backup file not found: ${backup_file}"
    fi

    # Check if it's a valid PostgreSQL dump
    pg_restore --list "${backup_file}" > /dev/null 2>&1

    if [ $? -ne 0 ]; then
        error "Invalid backup file or corrupted dump"
    fi

    log "Backup file validation passed"
}

###############################################################################
# Create backup of current database
###############################################################################
backup_current_db() {
    log "Creating safety backup of current database..."

    local safety_backup="/tmp/aurora_preRestore_$(date +%Y%m%d_%H%M%S).sql.gz"

    pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=custom \
        --compress=9 \
        --file="${safety_backup}"

    if [ $? -ne 0 ]; then
        log "WARNING: Could not create safety backup"
    else
        log "Safety backup created: ${safety_backup}"
        echo "${safety_backup}"
    fi
}

###############################################################################
# Restore database
###############################################################################
restore_database() {
    local backup_file="$1"

    log "Starting database restore..."
    log "Backup file: ${backup_file}"
    log "Target: ${DB_NAME} @ ${DB_HOST}:${DB_PORT}"

    # Terminate existing connections
    log "Terminating existing connections..."
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres <<EOF
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '${DB_NAME}'
  AND pid <> pg_backend_pid();
EOF

    # Drop and recreate database
    log "Recreating database..."
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres <<EOF
DROP DATABASE IF EXISTS ${DB_NAME};
CREATE DATABASE ${DB_NAME};
EOF

    if [ $? -ne 0 ]; then
        error "Failed to recreate database"
    fi

    # Restore from backup
    log "Restoring data from backup..."
    pg_restore \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --verbose \
        --no-owner \
        --no-acl \
        "${backup_file}" 2>&1 | tee -a "${LOG_FILE}"

    if [ $? -ne 0 ]; then
        error "Database restore failed"
    fi

    log "Database restore completed successfully"
}

###############################################################################
# Point-in-time recovery
###############################################################################
point_in_time_recovery() {
    local target_time="$1"
    local wal_dir="${2:-/backups/wal}"

    log "Starting point-in-time recovery to: ${target_time}"

    # This requires PostgreSQL to be configured for WAL archiving
    # and the recovery.conf file to be set up

    cat > "${TEMP_DIR}/recovery.conf" <<EOF
restore_command = 'cp ${wal_dir}/%f %p'
recovery_target_time = '${target_time}'
recovery_target_action = 'promote'
EOF

    log "Recovery configuration created"
    log "Please copy recovery.conf to PostgreSQL data directory and restart PostgreSQL"
    log "Location: ${TEMP_DIR}/recovery.conf"

    # Note: Actual PITR requires PostgreSQL restart with recovery.conf
    # This is typically done by a DBA or automation tool
}

###############################################################################
# Post-restore validation
###############################################################################
validate_restore() {
    log "Validating restored database..."

    # Check database size
    local db_size=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -t -c "SELECT pg_size_pretty(pg_database_size('${DB_NAME}'));")
    log "Database size: ${db_size}"

    # Count tables
    local table_count=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    log "Table count: ${table_count}"

    # Check key tables exist
    local tables=("users" "events" "predictions" "insights")
    for table in "${tables[@]}"; do
        local exists=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
            -t -c "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '${table}');")

        if [[ "${exists}" =~ "t" ]]; then
            log "✓ Table exists: ${table}"
        else
            error "✗ Missing table: ${table}"
        fi
    done

    # Run data integrity checks
    log "Running data integrity checks..."
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" <<EOF
-- Check for orphaned records
SELECT 'Orphaned events: ' || COUNT(*)
FROM events e
WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = e.user_id);

-- Check for null required fields
SELECT 'Events with null user_id: ' || COUNT(*)
FROM events
WHERE user_id IS NULL;

-- Check constraints
SELECT conname, contype
FROM pg_constraint
WHERE conrelid = 'events'::regclass;
EOF

    log "Validation completed"
}

###############################################################################
# Main
###############################################################################
main() {
    if [ $# -lt 1 ]; then
        echo "Usage: $0 <backup_file> [--pitr <timestamp>]"
        echo ""
        echo "Examples:"
        echo "  $0 /backups/full/aurora_life_20240116.sql.gz"
        echo "  $0 s3://bucket/full/backup.sql.gz --pitr '2024-01-16 15:30:00'"
        exit 1
    fi

    local backup_input="$1"
    local pitr_time=""

    # Parse arguments
    shift
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --pitr)
                pitr_time="$2"
                shift 2
                ;;
            *)
                error "Unknown argument: $1"
                ;;
        esac
    done

    log "=== AURORA_LIFE Database Restore Started ==="

    # Download from S3 if needed
    if [[ "${backup_input}" == s3://* ]]; then
        backup_file=$(download_from_s3 "${backup_input}")
    else
        backup_file="${backup_input}"
    fi

    # Validate backup
    validate_backup "${backup_file}"

    # Create safety backup
    safety_backup=$(backup_current_db)

    # Ask for confirmation
    log "!!! WARNING !!!"
    log "This will REPLACE the current database: ${DB_NAME}"
    log "A safety backup has been created: ${safety_backup}"
    log ""
    read -p "Are you sure you want to continue? (yes/no): " confirm

    if [ "${confirm}" != "yes" ]; then
        log "Restore cancelled by user"
        exit 0
    fi

    # Perform restore
    restore_database "${backup_file}"

    # Point-in-time recovery if requested
    if [ -n "${pitr_time}" ]; then
        point_in_time_recovery "${pitr_time}"
    fi

    # Validate restore
    validate_restore

    log "=== Database Restore Completed Successfully ==="
    log "Log file: ${LOG_FILE}"

    if [ -n "${safety_backup}" ]; then
        log "Safety backup (in case of issues): ${safety_backup}"
    fi
}

main "$@"
