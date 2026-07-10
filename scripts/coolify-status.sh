#!/usr/bin/env bash
# Status aplikacije + provjera javnog health endpointa.
# Usage: ./scripts/coolify-status.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/coolify-api.sh
. "$SCRIPT_DIR/lib/coolify-api.sh"

app=$(coolify_curl GET "/applications/$COOLIFY_APP_UUID" 2>/dev/null)
echo "$app" | jq -r '"name: \(.name)\nstatus: \(.status)\nfqdn: \(.fqdn // .domains // "-")\nports: \(.ports_exposes // "-")\nhealth: \(.health_check_path // "-") (enabled: \(.health_check_enabled // false))"'

DOMAIN="${ESIGN_DOMAIN:-https://esign.domovina.ai}"
echo "→ GET $DOMAIN/health"
curl -s --max-time 10 "$DOMAIN/health" || true
echo
