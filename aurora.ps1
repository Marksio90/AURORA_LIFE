# AURORA LIFE - PowerShell Commands
# Windows-compatible alternative to Makefile

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "Usage: .\aurora.ps1 [command]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Yellow
    Write-Host "  help        " -NoNewline -ForegroundColor Green
    Write-Host "Show this help message"
    Write-Host "  install     " -NoNewline -ForegroundColor Green
    Write-Host "Install dependencies"
    Write-Host "  quickstart  " -NoNewline -ForegroundColor Green
    Write-Host "Quick start (build, run, migrate, seed)"
    Write-Host "  build       " -NoNewline -ForegroundColor Green
    Write-Host "Build Docker images"
    Write-Host "  up          " -NoNewline -ForegroundColor Green
    Write-Host "Start all services"
    Write-Host "  down        " -NoNewline -ForegroundColor Green
    Write-Host "Stop all services"
    Write-Host "  restart     " -NoNewline -ForegroundColor Green
    Write-Host "Restart services"
    Write-Host "  logs        " -NoNewline -ForegroundColor Green
    Write-Host "Show all logs"
    Write-Host "  migrate     " -NoNewline -ForegroundColor Green
    Write-Host "Run database migrations"
    Write-Host "  seed        " -NoNewline -ForegroundColor Green
    Write-Host "Seed database"
    Write-Host "  test        " -NoNewline -ForegroundColor Green
    Write-Host "Run tests"
    Write-Host "  shell       " -NoNewline -ForegroundColor Green
    Write-Host "Open backend shell"
    Write-Host "  clean       " -NoNewline -ForegroundColor Green
    Write-Host "Cleanup (remove containers and volumes)"
    Write-Host "  status      " -NoNewline -ForegroundColor Green
    Write-Host "Show service status"
}

function Install-Dependencies {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan

    # Copy .env.example to .env if it doesn't exist
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Host "✅ Created .env file from .env.example" -ForegroundColor Green
        }
    }

    # Install Python dependencies
    if (Test-Path "backend/requirements.txt") {
        Push-Location backend
        pip install -r requirements.txt
        Pop-Location
    }

    Write-Host "✅ Done!" -ForegroundColor Green
}

function Start-Quickstart {
    Write-Host "🚀 Starting AURORA LIFE quickstart..." -ForegroundColor Cyan

    # Copy .env if needed
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.example") {
            Copy-Item ".env.example" ".env"
            Write-Host "✅ Created .env file" -ForegroundColor Green
        }
    }

    # Build images
    Write-Host "🔨 Building Docker images..." -ForegroundColor Yellow
    docker-compose build

    # Start services
    Write-Host "🚀 Starting services..." -ForegroundColor Yellow
    docker-compose up -d

    # Wait for services to be ready
    Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10

    # Run migrations
    Write-Host "🔄 Running migrations..." -ForegroundColor Yellow
    docker-compose exec backend alembic upgrade head

    # Seed database
    Write-Host "🌱 Seeding database..." -ForegroundColor Yellow
    docker-compose exec backend python -m app.db.seed_gamification

    Write-Host ""
    Write-Host "✨ Ready! Visit http://localhost:8000/docs" -ForegroundColor Green
}

function Build-Images {
    Write-Host "🔨 Building Docker images..." -ForegroundColor Cyan
    docker-compose build
}

function Start-Services {
    Write-Host "🚀 Starting AURORA LIFE..." -ForegroundColor Cyan
    docker-compose up -d
    Write-Host "✅ Services started!" -ForegroundColor Green
}

function Stop-Services {
    Write-Host "🛑 Stopping services..." -ForegroundColor Yellow
    docker-compose down
}

function Restart-Services {
    Write-Host "🔄 Restarting services..." -ForegroundColor Yellow
    docker-compose restart
}

function Show-Logs {
    docker-compose logs -f
}

function Run-Migrations {
    Write-Host "🔄 Running migrations..." -ForegroundColor Cyan
    docker-compose exec backend alembic upgrade head
}

function Seed-Database {
    Write-Host "🌱 Seeding database..." -ForegroundColor Cyan
    docker-compose exec backend python -m app.db.seed_gamification
}

function Run-Tests {
    Write-Host "🧪 Running tests..." -ForegroundColor Cyan
    docker-compose exec backend pytest tests/ -v
}

function Open-Shell {
    Write-Host "🐚 Opening backend shell..." -ForegroundColor Cyan
    docker-compose exec backend /bin/bash
}

function Clean-All {
    Write-Host "🧹 Cleaning up..." -ForegroundColor Yellow
    docker-compose down -v

    # Clean Python cache
    Get-ChildItem -Path . -Recurse -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

    Write-Host "✅ Cleanup complete!" -ForegroundColor Green
}

function Show-Status {
    Write-Host "📊 Service Status:" -ForegroundColor Cyan
    docker-compose ps
}

# Main switch
switch ($Command.ToLower()) {
    "help"       { Show-Help }
    "install"    { Install-Dependencies }
    "quickstart" { Start-Quickstart }
    "build"      { Build-Images }
    "up"         { Start-Services }
    "down"       { Stop-Services }
    "restart"    { Restart-Services }
    "logs"       { Show-Logs }
    "migrate"    { Run-Migrations }
    "seed"       { Seed-Database }
    "test"       { Run-Tests }
    "shell"      { Open-Shell }
    "clean"      { Clean-All }
    "status"     { Show-Status }
    default      {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
    }
}
