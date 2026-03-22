FROM nginx:1.27-alpine

# Remove default nginx config and content
RUN rm /etc/nginx/conf.d/default.conf
RUN rm -rf /usr/share/nginx/html/*

# Create certbot webroot directory
RUN mkdir -p /var/www/certbot

# Copy site files
COPY index.html /usr/share/nginx/html/index.html
COPY beta/ /usr/share/nginx/html/beta/

# Copy both nginx configs (deploy script swaps between them)
COPY nginx.conf /etc/nginx/conf.d/vendiq.conf
COPY nginx-init.conf /etc/nginx/conf.d/vendiq-init.conf.disabled

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
