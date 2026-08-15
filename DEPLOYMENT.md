# Deployment (Ubuntu 22.04, SQLite)

Deploys this Django app behind Gunicorn + Nginx. Another app on this VPS
already uses port 8000, so Gunicorn here binds to **127.0.0.1:8001** instead —
adjust if 8001 is also taken (`sudo ss -ltnp`).

No domain is assumed. Nginx listens on **port 8080** (also check it's free
with `sudo ss -ltnp`) with `server_name _;` — a catch-all that serves any
request regardless of hostname — so the app is reached at
`http://YOUR_VPS_IP:8080/`. This is a separate Nginx server block from
whatever serves the other app; it doesn't touch that config.

Replace `/srv/oquv_reja` and `YOUR_VPS_IP` below with your actual path and
server IP.

## 1. System packages

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git nginx
```

Skip `nginx` if it's already installed and running the other app.

## 2. Get the code

```bash
sudo mkdir -p /srv/oquv_reja
sudo chown "$USER":"$USER" /srv/oquv_reja
git clone git@github.com:me-ilyos/oquv-reja.git /srv/oquv_reja
cd /srv/oquv_reja
git checkout main
```

## 3. Virtualenv and dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Environment file

`settings.py` reads `.env` via `django-environ`. Create it:

```bash
cat > .env <<'EOF'
SECRET_KEY=replace-with-a-long-random-value
DEBUG=False
ALLOWED_HOSTS=YOUR_VPS_IP
CSRF_TRUSTED_ORIGINS=http://YOUR_VPS_IP:8080
EOF
chmod 600 .env
```

`CSRF_TRUSTED_ORIGINS` must include the full scheme + host + port you're
serving from (`http://YOUR_VPS_IP:8080`, not just the bare IP) — Django
checks login/POST requests' `Origin` header against this list separately
from `ALLOWED_HOSTS`, and rejects them with a 403 if it's missing.

Generate a secret key:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 5. Database, static files, superuser

SQLite needs no separate service — the DB file is created on first migrate.

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Make sure the app user can write to the SQLite file and its directory
(SQLite needs to create `db.sqlite3-wal`/`-shm` alongside it):

```bash
mkdir -p media
chmod 664 db.sqlite3 2>/dev/null || true
```

## 6. Gunicorn systemd service

```bash
sudo tee /etc/systemd/system/oquv_reja.service > /dev/null <<'EOF'
[Unit]
Description=oquv_reja Gunicorn daemon
After=network.target

[Service]
User=YOUR_LINUX_USER
Group=www-data
WorkingDirectory=/srv/oquv_reja
ExecStart=/srv/oquv_reja/.venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8001 \
    oquv_reja.wsgi:application
Restart=on-failure
EnvironmentFile=/srv/oquv_reja/.env

[Install]
WantedBy=multi-user.target
EOF
```

Replace `YOUR_LINUX_USER` with the account that owns `/srv/oquv_reja`.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now oquv_reja
sudo systemctl status oquv_reja
```

## 7. Nginx reverse proxy

Create a new server block file — it's independent of whatever config serves
the other app, so this won't disturb it:

```bash
sudo tee /etc/nginx/sites-available/oquv_reja > /dev/null <<'EOF'
server {
    listen 8080;
    server_name _;

    location /static/ {
        alias /srv/oquv_reja/staticfiles/;
    }

    location /media/ {
        alias /srv/oquv_reja/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/oquv_reja /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

`server_name _;` means "match any Host header" — there's no domain to match
against, so this block just handles everything that arrives on port 8080.
Visit `http://YOUR_VPS_IP:8080/` to confirm it's serving.

If you get a domain later, swap `server_name _;` for the real domain,
`listen 8080` back to `listen 80;`, and see the HTTPS note below.

## 8. Firewall

Nginx's new port needs to be reachable from outside; Gunicorn stays on
localhost.

```bash
sudo ufw allow 8080/tcp
sudo ufw status
```

Do **not** open port 8001 externally — only Nginx (8080) should be exposed.

## 9. HTTPS

Skipped for now — Let's Encrypt/certbot issues certificates for domain
names, not bare IPs, so TLS isn't available until you point a domain at
this server. Revisit this once you have one; at that point switch Nginx
back to port 80/443 and run `certbot --nginx -d your-domain`.

## 10. Deploying updates

```bash
cd /srv/oquv_reja
source .venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart oquv_reja
```

## 11. Backups

SQLite is a single file — back it up before every migration and on a
schedule:

```bash
cp /srv/oquv_reja/db.sqlite3 /srv/oquv_reja/backups/db-$(date +%F).sqlite3
```

Consider a cron job for this since there's no separate DB server doing it
for you.
