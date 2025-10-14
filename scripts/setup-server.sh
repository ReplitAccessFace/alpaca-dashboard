#!/bin/bash

# Server Setup Script for Alpaca Dashboard
# Run this script on your server to prepare it for deployment

set -e

echo "🖥️  Setting up server for Alpaca Dashboard..."

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

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install essential packages
print_status "Installing essential packages..."
apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Add current user to docker group
    usermod -aG docker $SUDO_USER
    print_warning "User $SUDO_USER added to docker group. Please logout and login again."
else
    print_status "Docker is already installed"
fi

# Install Docker Compose
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    print_status "Docker Compose is already installed"
fi

# Install Nginx (for reverse proxy)
print_status "Installing Nginx..."
apt install -y nginx

# Configure firewall
print_status "Configuring firewall..."
ufw --force enable
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8000/tcp  # Backend (temporary, will be proxied through Nginx)

# Create application directory
print_status "Creating application directory..."
mkdir -p /opt/alpaca-dashboard
chown $SUDO_USER:$SUDO_USER /opt/alpaca-dashboard

# Install Certbot for SSL certificates
print_status "Installing Certbot for SSL certificates..."
apt install -y certbot python3-certbot-nginx

# Create systemd service for auto-start
print_status "Creating systemd service..."
cat > /etc/systemd/system/alpaca-dashboard.service << EOF
[Unit]
Description=Alpaca Dashboard
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/alpaca-dashboard
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=$SUDO_USER
Group=$SUDO_USER

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
systemctl enable alpaca-dashboard.service

# Create backup script
print_status "Creating backup script..."
cat > /opt/alpaca-dashboard/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/alpaca-dashboard/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup databases
if [ -f "/opt/alpaca-dashboard/data/trades.db" ]; then
    cp /opt/alpaca-dashboard/data/trades.db $BACKUP_DIR/trades_$DATE.db
fi

if [ -f "/opt/alpaca-dashboard/data/market_data.db" ]; then
    cp /opt/alpaca-dashboard/data/market_data.db $BACKUP_DIR/market_data_$DATE.db
fi

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.db" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/alpaca-dashboard/backup.sh
chown $SUDO_USER:$SUDO_USER /opt/alpaca-dashboard/backup.sh

# Setup cron job for daily backups
print_status "Setting up daily backups..."
(crontab -u $SUDO_USER -l 2>/dev/null; echo "0 2 * * * /opt/alpaca-dashboard/backup.sh") | crontab -u $SUDO_USER -

# Create log rotation configuration
print_status "Setting up log rotation..."
cat > /etc/logrotate.d/alpaca-dashboard << EOF
/opt/alpaca-dashboard/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $SUDO_USER $SUDO_USER
}
EOF

print_status "✅ Server setup completed successfully!"
echo ""
print_status "📋 Next steps:"
echo "  1. Logout and login again to apply docker group changes"
echo "  2. Upload your project files to /opt/alpaca-dashboard/"
echo "  3. Configure your .env file with API credentials"
echo "  4. Run the deployment script: ./deploy.sh"
echo "  5. Configure your domain and SSL certificates"
echo ""
print_status "🔧 Useful commands:"
echo "  - Start dashboard: sudo systemctl start alpaca-dashboard"
echo "  - Stop dashboard: sudo systemctl stop alpaca-dashboard"
echo "  - View logs: docker-compose logs -f"
echo "  - Manual backup: /opt/alpaca-dashboard/backup.sh"
