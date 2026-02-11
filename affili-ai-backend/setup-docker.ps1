# Docker Setup Script for AFFILI-AI Hub
# This script rebuilds and starts all services fresh

Write-Host "🐳 AFFILI-AI Docker Setup" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Clean everything
Write-Host "Step 1: Cleaning up old containers and images..." -ForegroundColor Yellow
docker-compose down -v
docker system prune -f

# Step 2: Build services
Write-Host ""
Write-Host "Step 2: Building images (this may take a few minutes)..." -ForegroundColor Yellow
docker-compose build --no-cache

# Step 3: Start services
Write-Host ""
Write-Host "Step 3: Starting all services..." -ForegroundColor Yellow
docker-compose up -d

# Step 4: Wait for services to be ready
Write-Host ""
Write-Host "Step 4: Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Step 5: Show status
Write-Host ""
Write-Host "Step 5: Service Status" -ForegroundColor Green
docker-compose ps

Write-Host ""
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next Steps:" -ForegroundColor Cyan
Write-Host "  • View worker logs:  docker logs -f affili-ai-worker" -ForegroundColor White
Write-Host "  • View backend logs: docker logs -f affili-ai-backend" -ForegroundColor White
Write-Host "  • Stop everything:   docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Services:" -ForegroundColor Cyan
Write-Host "  • Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "  • Frontend:    http://localhost:8080" -ForegroundColor White
Write-Host "  • PostgreSQL:  localhost:5432" -ForegroundColor White
Write-Host ""
