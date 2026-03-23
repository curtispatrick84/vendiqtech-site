#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# VendiQ Site — Droplet Deploy Script
#
# First-time setup (fresh droplet):
#   sudo ./deploy.sh --init
#
# Subsequent deploys:
#   sudo ./deploy.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

DOMAIN="vendiqtech.com"
EMAIL="hello@vendiqtech.com"
REPO_DIR="/opt/vendiqtech-site"

# ── Check for .env ──
if [ ! -f "$REPO_DIR/.env" ]; then
  echo "ERROR: $REPO_DIR/.env not found."
  echo "Copy .env.example to .env and fill in your SMTP credentials."
  exit 1
fi

# ── First-time init (certbot + SSL) ──
if [ "${1:-}" = "--init" ]; then
  echo "==> First-time setup: installing certbot..."
  apt-get update -qq
  apt-get install -y -qq certbot

  mkdir -p /var/www/certbot /etc/letsencrypt

  echo "==> Starting nginx in HTTP-only mode for cert provisioning..."
  cd "$REPO_DIR"
  docker compose up --build -d api
  docker compose run -d --name vendiq-certbot-nginx \
    -p 80:80 \
    -v /var/www/certbot:/var/www/certbot:ro \
    nginx sh -c "cp /etc/nginx/conf.d/vendiq-init.conf.disabled /etc/nginx/conf.d/vendiq-init.conf && rm /etc/nginx/conf.d/vendiq.conf && nginx -g 'daemon off;'"

  sleep 3

  echo "==> Requesting SSL certificate from Let's Encrypt..."
  certbot certonly --webroot \
    -w /var/www/certbot \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive

  echo "==> Stopping cert provisioning container..."
  docker stop vendiq-certbot-nginx 2>/dev/null || true
  docker rm vendiq-certbot-nginx 2>/dev/null || true

  echo "==> Configuring certificate auto-renewal..."
  mkdir -p /etc/letsencrypt/renewal-hooks/deploy
  cat > /etc/letsencrypt/renewal-hooks/deploy/reload-vendiq.sh << 'HOOK'
#!/usr/bin/env bash
cd /opt/vendiqtech-site && docker compose exec nginx nginx -s reload 2>/dev/null || true
HOOK
  chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-vendiq.sh

  systemctl enable certbot.timer 2>/dev/null || true
  systemctl start certbot.timer 2>/dev/null || true

  echo "==> Testing certificate renewal (dry run)..."
  certbot renew --dry-run
fi

# ── Deploy ──
echo "==> Deploying VendiQ..."
cd "$REPO_DIR"

echo "==> Building and starting services..."
docker compose down 2>/dev/null || true
docker compose up --build -d

echo "==> Cleaning up old images..."
docker image prune -f

echo ""
echo "════════════════════════════════════════════════════"
echo "  VendiQ is live!"
echo "  https://$DOMAIN"
echo ""
echo "  Services:  docker compose -f $REPO_DIR/docker-compose.yml ps"
echo "  API logs:  docker compose -f $REPO_DIR/docker-compose.yml logs api"
echo "  Nginx:     docker compose -f $REPO_DIR/docker-compose.yml logs nginx"
echo "════════════════════════════════════════════════════"
