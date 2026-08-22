#!/usr/bin/env bash
# deploy_render.sh · Dispara el deploy de Render por su Deploy Hook.
#
# Render NO redeploya solo con cada push (render.yaml tiene autoDeploy: false
# a propósito) — este script es el único gatillo, y lo usan dos caminos:
#   1. El pipeline de CI (.github/workflows/deploy.yml), después de que el
#      smoke check pasa, en cada push a main.
#   2. Vos, a mano, para un redeploy manual sin esperar un push:
#        RENDER_DEPLOY_HOOK_URL="https://api.render.com/deploy/srv-xxx?key=yyy" \
#          ./scripts/deploy_render.sh
#
# El Deploy Hook URL sale del dashboard de Render: servicio -> Settings ->
# Deploy Hook. Es un secreto (dispara un build) — nunca se commitea; vive en
# el secret RENDER_DEPLOY_HOOK_URL de GitHub Actions y, para uso local, en tu
# entorno (no en un archivo del repo).
set -euo pipefail

if [ -z "${RENDER_DEPLOY_HOOK_URL:-}" ]; then
  echo "[deploy] falta RENDER_DEPLOY_HOOK_URL (dashboard de Render -> servicio -> Settings -> Deploy Hook)" >&2
  exit 1
fi

echo "[deploy] disparando deploy en Render..."
respuesta=$(curl -sS -w '\n%{http_code}' -X POST "$RENDER_DEPLOY_HOOK_URL")
codigo="${respuesta##*$'\n'}"
cuerpo="${respuesta%$'\n'*}"

echo "$cuerpo"
if [ "$codigo" -ge 200 ] && [ "$codigo" -lt 300 ]; then
  echo "[deploy] OK (HTTP $codigo) — seguí el build en el dashboard de Render (Logs)"
else
  echo "[deploy] el hook respondió HTTP $codigo — revisá la URL del Deploy Hook" >&2
  exit 1
fi
