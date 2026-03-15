#!/bin/bash
# JrDev Ubuntu Server Setup Script
# Run as root on a fresh Ubuntu 22.04 server.
# Idempotent: safe to run more than once.

set -e

APP_DIR=/var/www/jrdev
APP_USER=jrdev

echo "=== Installing system packages ==="
apt-get update -q
apt-get install -y python3 python3-venv python3-pip nginx postgresql postgresql-contrib certbot python3-certbot-nginx

echo "=== Creating app user ==="
id -u $APP_USER &>/dev/null || useradd --system --shell /bin/bash --home $APP_DIR $APP_USER

echo "=== Creating directories ==="
mkdir -p $APP_DIR
mkdir -p /var/log/jrdev
chown $APP_USER:www-data $APP_DIR
chown $APP_USER:www-data /var/log/jrdev

echo "=== Cloning / updating repo ==="
if [ -d "$APP_DIR/.git" ]; then
    sudo -u $APP_USER git -C $APP_DIR pull
else
    # Replace with your actual repo URL
    sudo -u $APP_USER git clone https://github.com/011-sam-110/jrdev.git $APP_DIR
fi

echo "=== Setting up Python venv ==="
if [ ! -d "$APP_DIR/venv" ]; then
    sudo -u $APP_USER python3 -m venv $APP_DIR/venv
fi
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip -q
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/backend/requirements.txt -q
sudo -u $APP_USER $APP_DIR/venv/bin/pip install gunicorn -q

echo "=== Checking .env file ==="
if [ ! -f "$APP_DIR/.env" ]; then
    echo "ERROR: $APP_DIR/.env not found. Create it before continuing."
    echo "Required vars: SECRET_KEY, DATABASE_URL, EMAIL_USER, EMAIL_PASS, STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET"
    exit 1
fi

echo "=== Running database migrations ==="
cd $APP_DIR/backend
sudo -u $APP_USER $APP_DIR/venv/bin/flask db upgrade

echo "=== Installing systemd service ==="
cp $APP_DIR/deploy/jrdev.service /etc/systemd/system/jrdev.service
systemctl daemon-reload
systemctl enable jrdev
systemctl restart jrdev

echo "=== Installing nginx config ==="
cp $APP_DIR/deploy/nginx-jrdev.conf /etc/nginx/sites-available/jrdev
ln -sf /etc/nginx/sites-available/jrdev /etc/nginx/sites-enabled/jrdev
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "=== Done! ==="
echo "Next steps:"
echo "  1. Edit /etc/nginx/sites-available/jrdev — replace 'yourdomain.com' with your actual domain"
echo "  2. Run: certbot --nginx -d yourdomain.com -d www.yourdomain.com"
echo "  3. Check app: systemctl status jrdev"
echo "  4. Check logs: journalctl -u jrdev -f"
