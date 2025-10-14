#!/bin/bash

# SSL Certificate Setup Script
# This script helps you obtain and configure SSL certificates

set -e

echo "🔒 Setting up SSL certificates for Alpaca Dashboard..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Get domain name from user
read -p "Enter your domain name (e.g., yourdomain.com): " DOMAIN

if [ -z "$DOMAIN" ]; then
    print_error "Domain name is required"
    exit 1
fi

print_status "Setting up SSL certificate for $DOMAIN..."

# Check if domain points to this server
print_status "Checking if domain $DOMAIN points to this server..."
SERVER_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)

if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
    print_warning "Domain $DOMAIN does not point to this server ($SERVER_IP)"
    print_warning "Domain currently points to: $DOMAIN_IP"
    print_warning "Please update your DNS records before continuing"
    read -p "Continue anyway? (y/N): " CONTINUE
    if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install Certbot if not already installed
if ! command -v certbot &> /dev/null; then
    print_status "Installing Certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
fi

# Stop any running services that might conflict
print_status "Stopping services temporarily..."
systemctl stop nginx 2>/dev/null || true
docker-compose -f /opt/alpaca-dashboard/docker-compose.yml down 2>/dev/null || true

# Obtain SSL certificate
print_status "Obtaining SSL certificate from Let's Encrypt..."
certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

# Create SSL directory and copy certificates
print_status "Setting up SSL certificates..."
mkdir -p /opt/alpaca-dashboard/ssl
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/alpaca-dashboard/ssl/cert.pem
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/alpaca-dashboard/ssl/key.pem
chown -R $SUDO_USER:$SUDO_USER /opt/alpaca-dashboard/ssl

# Update Nginx configuration with domain
print_status "Updating Nginx configuration..."
sed -i "s/yourdomain.com/$DOMAIN/g" /opt/alpaca-dashboard/nginx/conf.d/alpaca-dashboard.conf

# Setup auto-renewal
print_status "Setting up certificate auto-renewal..."
(crontab -u root -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -u root -

# Create renewal script
cat > /opt/alpaca-dashboard/renew-ssl.sh << EOF
#!/bin/bash
# Renew SSL certificates and update Docker containers

certbot renew --quiet

if [ \$? -eq 0 ]; then
    # Copy new certificates
    cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/alpaca-dashboard/ssl/cert.pem
    cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/alpaca-dashboard/ssl/key.pem
    
    # Restart services
    cd /opt/alpaca-dashboard
    docker-compose restart nginx
    
    echo "SSL certificates renewed successfully"
else
    echo "SSL certificate renewal failed"
    exit 1
fi
EOF

chmod +x /opt/alpaca-dashboard/renew-ssl.sh
chown $SUDO_USER:$SUDO_USER /opt/alpaca-dashboard/renew-ssl.sh

# Update .env file with domain
if [ -f "/opt/alpaca-dashboard/.env" ]; then
    print_status "Updating .env file with domain configuration..."
    sed -i "s|REACT_APP_API_URL=http://localhost:8000|REACT_APP_API_URL=https://$DOMAIN|g" /opt/alpaca-dashboard/.env
    sed -i "s|CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com|CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN|g" /opt/alpaca-dashboard/.env
fi

print_status "✅ SSL setup completed successfully!"
echo ""
print_status "📋 SSL Configuration Summary:"
echo "  - Domain: $DOMAIN"
echo "  - Certificate: /opt/alpaca-dashboard/ssl/cert.pem"
echo "  - Private Key: /opt/alpaca-dashboard/ssl/key.pem"
echo "  - Auto-renewal: Enabled (runs daily at 12:00)"
echo ""
print_status "🚀 Next steps:"
echo "  1. Start your services: cd /opt/alpaca-dashboard && docker-compose up -d"
echo "  2. Test SSL: https://$DOMAIN"
echo "  3. Monitor certificate expiry: certbot certificates"
echo ""
print_status "🔧 Useful commands:"
echo "  - Check certificate status: certbot certificates"
echo "  - Test renewal: certbot renew --dry-run"
echo "  - Manual renewal: /opt/alpaca-dashboard/renew-ssl.sh"
