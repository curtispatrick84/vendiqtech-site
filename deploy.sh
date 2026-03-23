#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# VendiQ Site — Droplet Deploy Script
# Run this on your Digital Ocean droplet as root (or with sudo).
#
# Usage:
#   chmod +x deploy.sh
#   sudo ./deploy.sh
# ─────────────────────────────────────────────────────────────
set -euo pipefail

DOMAIN="vendiqtech.com"
EMAIL="hello@vendiqtech.com"
IMAGE="ghcr.io/curtispatrick84/vendiq-site:1.3.0"
CONTAINER="vendiq"

echo "==> Installing certbot..."
apt-get update -qq
apt-get install -y -qq certbot

echo "==> Pulling container image..."
docker pull "$IMAGE"

# ── STEP 1: Start with HTTP-only config to serve ACME challenges ──
echo "==> Starting container in HTTP-only mode for cert provisioning..."

# Stop existing container if running
docker stop "$CONTAINER" 2>/dev/null || true
docker rm "$CONTAINER" 2>/dev/null || true

# Create host directories for certbot
mkdir -p /var/www/certbot
mkdir -p /etc/letsencrypt

docker run -d \
  --name "$CONTAINER" \
  -p 80:80 \
  -v /var/www/certbot:/var/www/certbot:ro \
  --restart unless-stopped \
  "$IMAGE" \
  sh -c "cp /etc/nginx/conf.d/vendiq-init.conf.disabled /etc/nginx/conf.d/vendiq-init.conf && rm /etc/nginx/conf.d/vendiq.conf && nginx -g 'daemon off;'"

# Give nginx a moment to start
sleep 3

# ── STEP 2: Get SSL certificate ──
echo "==> Requesting SSL certificate from Let's Encrypt..."
certbot certonly --webroot \
  -w /var/www/certbot \
  -d "$DOMAIN" \
  -d "www.$DOMAIN" \
  --email "$EMAIL" \
  --agree-tos \
  --non-interactive

# ── STEP 3: Restart with full SSL config ──
echo "==> Restarting container with SSL..."
docker stop "$CONTAINER"
docker rm "$CONTAINER"

docker run -d \
  --name "$CONTAINER" \
  -p 80:80 \
  -p 443:443 \
  -v /etc/letsencrypt:/etc/letsencrypt:ro \
  -v /var/www/certbot:/var/www/certbot:ro \
  --restart unless-stopped \
  "$IMAGE"

# ── STEP 4: Set up auto-renewal ──
echo "==> Configuring certificate auto-renewal..."

# Create renewal hook that reloads nginx in the container
mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/reload-vendiq.sh << 'HOOK'
#!/usr/bin/env bash
docker exec vendiq nginx -s reload 2>/dev/null || true
HOOK
chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-vendiq.sh

# Ensure certbot timer is enabled (installed by default on most distros)
systemctl enable certbot.timer 2>/dev/null || true
systemctl start certbot.timer 2>/dev/null || true

# Verify renewal works
echo "==> Testing certificate renewal (dry run)..."
certbot renew --dry-run

echo ""
echo "════════════════════════════════════════════════════"
echo "  VendiQ is live!"
echo "  https://$DOMAIN"
echo "  https://www.$DOMAIN"
echo ""
echo "  SSL auto-renewal: active (certbot.timer)"
echo "  Container: docker logs $CONTAINER"
echo "════════════════════════════════════════════════════"
