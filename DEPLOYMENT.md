# Alpaca Dashboard Deployment Guide

This guide will help you deploy your Alpaca Trading Dashboard to a server for browser access.

## 🚀 Deployment Options

### Option 1: Docker Deployment (Recommended)
The easiest way to deploy with minimal server setup.

### Option 2: Manual Server Deployment
For more control over the deployment process.

### Option 3: Cloud Platform Deployment
Deploy to platforms like AWS, DigitalOcean, or Heroku.

---

## 📋 Prerequisites

- Server with Ubuntu 20.04+ or similar Linux distribution
- Domain name (optional but recommended)
- SSL certificate (Let's Encrypt recommended)
- Alpaca API credentials

---

## 🐳 Option 1: Docker Deployment

### Step 1: Prepare Your Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again to apply docker group changes
```

### Step 2: Upload Your Project

```bash
# Create project directory
mkdir -p /opt/alpaca-dashboard
cd /opt/alpaca-dashboard

# Upload your project files (use scp, rsync, or git clone)
# Example with git:
git clone <your-repo-url> .
# Or upload via SCP:
# scp -r /path/to/local/dashboard user@server:/opt/alpaca-dashboard/
```

### Step 3: Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
nano .env
```

### Step 4: Deploy with Docker

```bash
# Build and start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## 🖥️ Option 2: Manual Server Deployment

### Step 1: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python 3.9+
sudo apt install python3 python3-pip python3-venv

# Install Nginx
sudo apt install nginx

# Install SQLite (if not already installed)
sudo apt install sqlite3
```

### Step 2: Setup Backend

```bash
# Create backend directory
sudo mkdir -p /opt/alpaca-dashboard/backend
cd /opt/alpaca-dashboard/backend

# Upload backend files
# Copy your backend files here

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/alpaca-backend.service
```

### Step 3: Setup Frontend

```bash
# Create frontend directory
sudo mkdir -p /opt/alpaca-dashboard/frontend
cd /opt/alpaca-dashboard/frontend

# Upload frontend files
# Copy your frontend files here

# Install dependencies
npm install

# Build for production
npm run build

# Create systemd service
sudo nano /etc/systemd/system/alpaca-frontend.service
```

### Step 4: Configure Nginx

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/alpaca-dashboard

# Enable site
sudo ln -s /etc/nginx/sites-available/alpaca-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 5: Start Services

```bash
# Enable and start services
sudo systemctl enable alpaca-backend
sudo systemctl enable alpaca-frontend
sudo systemctl start alpaca-backend
sudo systemctl start alpaca-frontend

# Check status
sudo systemctl status alpaca-backend
sudo systemctl status alpaca-frontend
```

---

## ☁️ Option 3: Cloud Platform Deployment

### AWS EC2 Deployment

1. **Launch EC2 Instance**
   - Choose Ubuntu 20.04 LTS
   - Select appropriate instance size (t3.medium recommended)
   - Configure security groups (ports 22, 80, 443, 8000)

2. **Setup Domain (Optional)**
   - Point your domain to EC2 public IP
   - Use Route 53 for DNS management

3. **Follow Manual Deployment Steps**
   - Use the manual deployment guide above

### DigitalOcean Droplet

1. **Create Droplet**
   - Choose Ubuntu 20.04
   - Select appropriate size ($10-20/month recommended)
   - Add SSH keys

2. **Follow Docker Deployment**
   - Use the Docker deployment guide above

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your configuration:

```bash
# Alpaca API Configuration
ALPACA_KEY=your_api_key_here
ALPACA_SECRET=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Server Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000
NODE_ENV=production

# Database Configuration
DATABASE_PATH=/opt/alpaca-dashboard/data/trades.db
MARKET_DATA_DB_PATH=/opt/alpaca-dashboard/data/market_data.db

# Security
JWT_SECRET=your_jwt_secret_here
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 📊 Monitoring & Maintenance

### Log Management

```bash
# View backend logs
sudo journalctl -u alpaca-backend -f

# View frontend logs
sudo journalctl -u alpaca-frontend -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database Backup

```bash
# Create backup script
sudo nano /opt/alpaca-dashboard/backup.sh

# Make executable
sudo chmod +x /opt/alpaca-dashboard/backup.sh

# Add to crontab for daily backups
sudo crontab -e
# Add: 0 2 * * * /opt/alpaca-dashboard/backup.sh
```

### Updates

```bash
# Update application
cd /opt/alpaca-dashboard
git pull origin main

# Restart services
sudo systemctl restart alpaca-backend
sudo systemctl restart alpaca-frontend

# Or with Docker
docker-compose down
docker-compose up -d --build
```

---

## 🔒 Security Considerations

1. **Firewall Configuration**
   ```bash
   sudo ufw enable
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   ```

2. **API Key Security**
   - Never commit API keys to version control
   - Use environment variables
   - Rotate keys regularly

3. **Database Security**
   - Regular backups
   - Access restrictions
   - Encryption at rest

4. **SSL/TLS**
   - Always use HTTPS in production
   - Regular certificate renewal
   - Strong cipher suites

---

## 🚨 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   sudo lsof -i :8000
   sudo kill -9 <PID>
   ```

2. **Permission Issues**
   ```bash
   sudo chown -R www-data:www-data /opt/alpaca-dashboard
   sudo chmod -R 755 /opt/alpaca-dashboard
   ```

3. **Service Won't Start**
   ```bash
   sudo systemctl status alpaca-backend
   sudo journalctl -u alpaca-backend --no-pager
   ```

4. **Database Issues**
   ```bash
   sqlite3 /opt/alpaca-dashboard/data/trades.db ".tables"
   sqlite3 /opt/alpaca-dashboard/data/trades.db "SELECT COUNT(*) FROM orders;"
   ```

---

## 📈 Performance Optimization

1. **Enable Gzip Compression**
2. **Use CDN for Static Assets**
3. **Database Indexing**
4. **Caching Strategies**
5. **Load Balancing (for high traffic)**

---

## 🆘 Support

If you encounter issues:

1. Check the logs first
2. Verify configuration files
3. Test API connectivity
4. Check firewall settings
5. Review this troubleshooting guide

For additional help, check the project documentation or create an issue in the repository.
