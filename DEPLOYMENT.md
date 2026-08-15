# Deployment (Ubuntu 22.04, SQLite)

Deploys this Django app behind Gunicorn + Nginx. Another app on this VPS
already uses port 8000, so Gunicorn here binds to **127.0.0.1:8001** instead —
adjust if 8001 is also taken (`sudo ss -ltnp`).

Replace `example.com` and `/srv/oquv_reja` below with your actual domain and
path.

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
ALLOWED_HOSTS=example.com,www.example.com
EOF
chmod 600 .env
```

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

Create a new server block (separate file so it doesn't touch the existing
app's config):

```bash
sudo tee /etc/nginx/sites-available/oquv_reja > /dev/null <<'EOF'
server {
    listen 80;
    server_name example.com www.example.com;

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

If this app doesn't have its own domain, route it by path on the existing
server block instead (e.g. `location /reja/ { proxy_pass
http://127.0.0.1:8001/; }` on the site that already listens on 80/443), and
set `FORCE_SCRIPT_NAME`/adjust `STATIC_URL` accordingly — ask before doing
this since it means editing the other app's Nginx config.

## 8. Firewall

Only Nginx needs to be reachable from outside; Gunicorn stays on localhost.

```bash
sudo ufw allow 'Nginx Full'
sudo ufw status
```

Do **not** open port 8001 externally.

## 9. HTTPS (optional but recommended)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d example.com -d www.example.com
```

Certbot edits the Nginx block above and sets up auto-renewal.

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
