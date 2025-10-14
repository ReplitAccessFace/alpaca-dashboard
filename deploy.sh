#!/bin/bash

# Alpaca Dashboard Deployment Script
# This script automates the deployment process

set -e

echo "🚀 Starting Alpaca Dashboard Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
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
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f env.example ]; then
        cp env.example .env
        print_warning "Please edit .env file with your configuration before continuing."
        print_warning "At minimum, you need to set ALPACA_KEY and ALPACA_SECRET"
        exit 1
    else
        print_error "env.example file not found. Cannot create .env file."
        exit 1
    fi
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data logs ssl

# Set proper permissions
print_status "Setting directory permissions..."
chmod 755 data logs ssl

# Stop existing containers if running
print_status "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start services
print_status "Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 30

# Check if services are running
print_status "Checking service status..."
if docker-compose ps | grep -q "Up"; then
    print_status "✅ Services are running successfully!"
    
    # Display service URLs
    echo ""
    print_status "🌐 Dashboard URLs:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend API: http://localhost:8000"
    echo "  - API Documentation: http://localhost:8000/docs"
    
    # Check health endpoints
    print_status "Checking service health..."
    
    # Check backend health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_status "✅ Backend is healthy"
    else
        print_warning "⚠️  Backend health check failed"
    fi
    
    # Check frontend
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_status "✅ Frontend is accessible"
    else
        print_warning "⚠️  Frontend is not accessible"
    fi
    
    echo ""
    print_status "🎉 Deployment completed successfully!"
    print_status "You can now access your dashboard at http://localhost:3000"
    
else
    print_error "❌ Some services failed to start. Check logs with: docker-compose logs"
    exit 1
fi

# Display useful commands
echo ""
print_status "📋 Useful commands:"
echo "  - View logs: docker-compose logs -f"
echo "  - Stop services: docker-compose down"
echo "  - Restart services: docker-compose restart"
echo "  - Update services: docker-compose pull && docker-compose up -d"
echo "  - View service status: docker-compose ps"

echo ""
print_status "🔧 For production deployment:"
echo "  1. Configure your domain in nginx/conf.d/alpaca-dashboard.conf"
echo "  2. Obtain SSL certificates (Let's Encrypt recommended)"
echo "  3. Update CORS_ORIGINS in .env file"
echo "  4. Set up monitoring and backups"
