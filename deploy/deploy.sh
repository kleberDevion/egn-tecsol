#!/usr/bin/env bash
# Atualiza os três projetos no servidor a partir do git e reinicia os serviços.
# Uso (como usuário tecsol):  bash /opt/tecsol/egn-tecsol/deploy/deploy.sh
set -euo pipefail

BASE=/opt/tecsol
VENV=$BASE/venv

echo "==> egn-tecsol (API + CRM)"
cd $BASE/egn-tecsol
git pull --ff-only
$VENV/bin/pip install -q -r api/requirements.txt
(cd crm && npm ci && npm run build)

echo "==> tp-app (app de indicações)"
cd $BASE/tp-app
git pull --ff-only
npm ci && npm run build

echo "==> site-tecsol (site institucional)"
cd $BASE/site-tecsol
git pull --ff-only
npm ci && npm run build

echo "==> reiniciando serviços"
sudo systemctl restart tecsol-api tecsol-worker tecsol-scheduler tecsol-parceiros
sudo systemctl reload nginx

echo "==> status"
systemctl --no-pager --lines=0 status tecsol-api tecsol-worker tecsol-scheduler tecsol-parceiros | grep -E "●|Active:"
echo "pronto."
