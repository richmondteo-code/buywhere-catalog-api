#!/bin/bash
set -euo pipefail
set -o pipefail

CERT_DIR="/etc/letsencrypt/live/api.buywhere.ai"
RENEWAL_CONF="/etc/letsencrypt/renewal/api.buywhere.ai.conf"
LOG_FILE="/var/log/ssl_renewal.log"
WEBROOT_PATH="/var/www/html"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$LOG_FILE" >&2
}

setup_webroot() {
    if [[ ! -d "$WEBROOT_PATH" ]]; then
        log "Creating webroot directory at $WEBROOT_PATH"
        mkdir -p "$WEBROOT_PATH"
    fi
}

reload_nginx() {
    log "Reloading nginx after certificate renewal..."
    if systemctl reload nginx 2>&1 | tee -a "$LOG_FILE"; then
        log "nginx reloaded successfully"
    else
        error "Failed to reload nginx"
        return 1
    fi
    return 0
}

check_cert_expiry() {
    if [[ ! -f "$CERT_DIR/fullchain.pem" ]]; then
        error "Certificate file not found at $CERT_DIR/fullchain.pem"
        return 1
    fi

    local expiry_date
    expiry_date=$(openssl x509 -in "$CERT_DIR/fullchain.pem" -noout -enddate 2>/dev/null | cut -d= -f2)
    if [[ -z "$expiry_date" ]]; then
        error "Could not read certificate expiry date"
        return 1
    fi

    local expiry_epoch
    expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$expiry_date" +%s 2>/dev/null)
    local now_epoch
    now_epoch=$(date +%s)
    local days_until_expiry=$(( (expiry_epoch - now_epoch) / 86400 ))

    log "Certificate expires: $expiry_date ($days_until_expiry days)"
    echo "$days_until_expiry"
}

renew_certs() {
    log "Starting SSL certificate renewal check..."

    if ! command -v certbot &> /dev/null; then
        error "certbot not found in PATH"
        return 1
    fi

    setup_webroot

    if [[ ! -f "$RENEWAL_CONF" ]]; then
        error "Renewal configuration not found at $RENEWAL_CONF"
        error "Please deploy certbot/renewal/api.buywhere.ai.conf to $RENEWAL_CONF"
        return 1
    fi

    local days_until_expiry
    days_until_expiry=$(check_cert_expiry)

    if [[ $days_until_expiry -lt 0 ]]; then
        error "Certificate has already expired!"
        return 1
    fi

    if [[ $days_until_expiry -lt 30 ]]; then
        log "Certificate expires in $days_until_expiry days, attempting renewal..."
        if certbot renew --quiet --conf "$RENEWAL_CONF" 2>&1 | tee -a "$LOG_FILE"; then
            log "Certificate renewal completed"
            reload_nginx
            return 0
        else
            error "Certificate renewal failed"
            return 1
        fi
    else
        log "Certificate still valid for $days_until_expiry days, no renewal needed"
        return 0
    fi
}

case "${1:-renew}" in
    check)
        check_cert_expiry
        ;;
    renew)
        renew_certs
        ;;
    *)
        echo "Usage: $0 {check|renew}"
        exit 1
        ;;
esac