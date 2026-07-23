# Subir tudo numa VPS (Ubuntu 22.04/24.04)

Roda os quatro serviços numa máquina só, sem Docker e sem depender de nenhuma
plataforma paga:

| O quê | Onde fica |
|---|---|
| API Flask | `127.0.0.1:5000` (Nginx faz proxy) |
| App de indicações (tp-app, SSR) | `127.0.0.1:3000` (Nginx faz proxy) |
| CRM | arquivos estáticos em `crm/dist` |
| Site institucional | arquivos estáticos em `site-tecsol/dist` |
| PostgreSQL e Redis | locais, via `apt` |

Servidor grátis: **Oracle Cloud Always Free** (4 vCPU ARM + 24 GB RAM).
Alternativas pagas baratas: Hetzner, Hostinger VPS, Contabo.

---

## 1. Pacotes do sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip \
  postgresql redis-server nginx git curl certbot python3-certbot-nginx
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

## 2. Usuário e pastas

```bash
sudo adduser --system --group --home /opt/tecsol tecsol
sudo mkdir -p /opt/tecsol && sudo chown tecsol:tecsol /opt/tecsol
sudo -u tecsol -H bash
cd /opt/tecsol
git clone https://github.com/kleberDevion/egn-tecsol.git
git clone https://github.com/kleberDevion/tp-app.git
git clone https://github.com/kleberDevion/site-tecsol.git   # ajustar se o nome do repo for outro
```

## 3. Banco

```bash
sudo -u postgres psql -c "CREATE USER tecsol WITH PASSWORD 'TROCAR_ESSA_SENHA';"
sudo -u postgres psql -c "CREATE DATABASE tecsol OWNER tecsol;"
```

## 4. Python

```bash
sudo -u tecsol -H bash
cd /opt/tecsol
python3 -m venv venv
venv/bin/pip install -r egn-tecsol/api/requirements.txt
```

## 5. Variáveis de ambiente

Criar `/opt/tecsol/egn-tecsol/api/.env` (esse arquivo **nunca** vai pro git):

```
DATABASE_URL=postgresql://tecsol:TROCAR_ESSA_SENHA@127.0.0.1:5432/tecsol
REDIS_URL=redis://127.0.0.1:6379/0
SOLARZ_API_TOKEN=<token da Solarz>
GOOGLE_ADS_DEVELOPER_TOKEN=<token do Google Ads>
SECRET_KEY=<string aleatória longa>
COOKIE_CROSS_SITE=1
CORS_ORIGINS=https://crm.SEUDOMINIO,https://parceiros.SEUDOMINIO,https://SEUDOMINIO
```

> `SECRET_KEY`: gerar com `python3 -c "import secrets; print(secrets.token_hex(32))"`.
> Se tudo ficar no mesmo domínio (subdomínios do mesmo site), dá pra usar
> `COOKIE_CROSS_SITE=0`, que é mais seguro.

## 6. Frontends

O endereço da API entra no build (variáveis `VITE_*`), então precisa estar
definido **antes** do `npm run build`:

```bash
# CRM
cd /opt/tecsol/egn-tecsol/crm
echo 'VITE_API_URL=https://api.SEUDOMINIO' > .env
npm ci && npm run build

# App de indicações
cd /opt/tecsol/tp-app
echo 'VITE_TECSOL_API_URL=https://api.SEUDOMINIO/api/v1' > .env
npm ci && npm run build

# Site institucional
cd /opt/tecsol/site-tecsol
echo 'VITE_TECSOL_API_URL=https://api.SEUDOMINIO/api/v1' > .env
npm ci && npm run build
```

## 7. Serviços (systemd)

```bash
sudo cp /opt/tecsol/egn-tecsol/deploy/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tecsol-api tecsol-worker tecsol-scheduler tecsol-parceiros
systemctl status tecsol-api
```

## 8. Nginx + HTTPS

```bash
sudo cp /opt/tecsol/egn-tecsol/deploy/nginx-tecsol.conf /etc/nginx/sites-available/tecsol
sudo ln -sf /etc/nginx/sites-available/tecsol /etc/nginx/sites-enabled/tecsol
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# HTTPS grátis (renova sozinho). Só funciona com domínio apontando pro servidor.
sudo certbot --nginx -d SEUDOMINIO -d www.SEUDOMINIO -d api.SEUDOMINIO \
  -d crm.SEUDOMINIO -d parceiros.SEUDOMINIO
```

> **Sem domínio ainda?** Dá pra subir tudo pelo IP (troque os `server_name` por
> `_`), mas aí o HTTPS não existe — e sem HTTPS o cookie `Secure` não funciona,
> então use `COOKIE_CROSS_SITE=0` enquanto for só IP.

## 9. Atualizar depois de mudar o código

```bash
bash /opt/tecsol/egn-tecsol/deploy/deploy.sh
```

## 10. Backup do banco (importante)

```bash
sudo -u postgres sh -c 'pg_dump tecsol | gzip > /var/backups/tecsol-$(date +%F).sql.gz'
```

Automatizar com cron (diário às 3h):

```bash
sudo crontab -e
# 0 3 * * * sudo -u postgres sh -c 'pg_dump tecsol | gzip > /var/backups/tecsol-$(date +\%F).sql.gz'
```

---

## Coisas que não rodam aqui

**DWG**: a geração do desenho usa automação COM do AutoCAD, que só existe no
Windows com AutoCAD instalado. Continua manual, feito pela engenharia como
hoje. Os outros quatro documentos (memorial, contrato, procuração e RT) são
gerados normalmente pelo servidor.

**Modelos .docx**: colocar os arquivos da engenharia em
`egn-tecsol/api/templates_documentos/` — ver o `LEIA-ME.md` de lá.
