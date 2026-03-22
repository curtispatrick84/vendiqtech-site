# VendiQ — vendiqtech.com

Marketing site for VendiQ — smart retrofit kits that add cashless payments, real-time inventory tracking, and revenue reporting to legacy vending machines.

## Structure

```
index.html          Landing page (coming soon / waitlist)
beta/index.html     Password-protected beta portal stub
nginx.conf          Nginx config with SSL (HTTPS + ACME challenges)
nginx-init.conf     HTTP-only config for initial cert provisioning
Dockerfile          nginx:1.27-alpine container
deploy.sh           One-step droplet deploy (pulls image, provisions SSL)
```

## Local Development

```bash
docker build -t vendiq-site .
docker run -p 8080:80 vendiq-site
# http://localhost:8080
```

## Deploy to Production

The site runs as a Docker container on a DigitalOcean droplet with Certbot SSL.

```bash
# On the droplet:
docker login ghcr.io -u curtispatrick84
sudo ./deploy.sh
```

The deploy script pulls `ghcr.io/curtispatrick84/vendiq-site` from GitHub Container Registry, provisions a Let's Encrypt certificate for `vendiqtech.com`, and sets up auto-renewal.

## Container Registry

Images are published to GitHub Container Registry:

```
ghcr.io/curtispatrick84/vendiq-site:latest
ghcr.io/curtispatrick84/vendiq-site:1.1.0
```

Build and push a new version:

```bash
docker buildx build --platform linux/amd64 \
  -t ghcr.io/curtispatrick84/vendiq-site:<version> \
  -t ghcr.io/curtispatrick84/vendiq-site:latest \
  --push .
```
