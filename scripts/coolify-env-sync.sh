#!/usr/bin/env bash
# Sinkronizira SVE env varijable iz coolify.env (lokalni izvor istine, gitignoriran)
# na Coolify aplikaciju. Idempotentno (upsert). Prijavi drift: ključeve koji
# postoje na Coolifyju a nema ih lokalno (ne briše ih sam).
#
# Usage:
#   ./scripts/coolify-env-sync.sh            # sync, bez deploya
#   ./scripts/coolify-env-sync.sh --deploy   # sync + redeploy
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/coolify-api.sh
. "$SCRIPT_DIR/lib/coolify-api.sh"

ENV_FILE="${ENV_FILE:-$REPO_ROOT/coolify.env}"
[ -f "$ENV_FILE" ] || { echo "❌ $ENV_FILE ne postoji." >&2; exit 1; }

DEPLOY=false
[ "${1:-}" = "--deploy" ] && DEPLOY=true

declare -a local_keys=()
while IFS= read -r line; do
  [[ "$line" =~ ^[[:space:]]*# ]] && continue
  [[ "$line" == *=* ]] || continue
  key="${line%%=*}"; value="${line#*=}"
  local_keys+=("$key")
  echo "→ $key = $(coolify_mask "$value")"
  coolify_env_upsert "$key" "$value"
done < "$ENV_FILE"
echo "✅ ${#local_keys[@]} varijabli sinkronizirano."

remote=$(coolify_curl GET "/applications/$COOLIFY_APP_UUID/envs" 2>/dev/null | jq -r '.[]?.key')
for rk in $remote; do
  found=false
  for lk in "${local_keys[@]}"; do [ "$rk" = "$lk" ] && found=true && break; done
  $found || echo "⚠️  Na Coolifyju postoji '$rk' kojeg nema u coolify.env (obriši ručno ako je višak)."
done

if $DEPLOY; then
  echo "→ Redeploy…"
  coolify_app_deploy >/dev/null
  echo "✅ Redeploy queued."
fi
