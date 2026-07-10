#!/usr/bin/env bash
# Jednokratna konfiguracija Coolify aplikacije kroz API — da se u dashboardu
# ne mora klikati ništa: port 3355, healthcheck /health, domena esign.domovina.ai.
#
# Usage: ./scripts/coolify-configure.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/coolify-api.sh
. "$SCRIPT_DIR/lib/coolify-api.sh"

DOMAIN="${ESIGN_DOMAIN:-https://esign.domovina.ai}"

payload=$(jq -nc --arg domains "$DOMAIN" '{
  domains: $domains,
  ports_exposes: "3355",
  health_check_enabled: true,
  health_check_path: "/health",
  health_check_return_code: 200
}')
echo "→ PATCH /applications/$COOLIFY_APP_UUID ($DOMAIN, port 3355, /health)"
resp=$(coolify_curl PATCH "/applications/$COOLIFY_APP_UUID" --data "$payload" 2>/tmp/_cc); code=$(cat /tmp/_cc); rm -f /tmp/_cc
case "$code" in
  200|201) echo "✅ Konfigurirano." ;;
  *) echo "❌ HTTP $code"; echo "$resp" | head -5; exit 1 ;;
esac
