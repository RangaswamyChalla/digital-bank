#!/bin/bash

# ===== BANKING PLATFORM - INTEGRATED DEPLOYMENT SCRIPT =====
# Quick start for running the complete integrated system
# Usage: bash deploy.sh [start|stop|logs|clean]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ===== FUNCTIONS =====

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_requirements() {
    print_header "Checking Requirements"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker not found. Please install Docker."
        exit 1
    fi
    print_success "Docker is installed"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose not found. Please install Docker Compose."
        exit 1
    fi
    print_success "Docker Compose is installed"
    
    # Check .env file
    if [ ! -f ".env" ]; then
        print_info ".env file not found. Creating from .env.example"
        cp .env.example .env
        print_success ".env created (update with your values)"
    fi
}

start_system() {
    print_header "Starting Banking Platform"
    
    print_info "Building containers..."
    docker-compose build
    print_success "Containers built"
    
    print_info "Starting services..."
    docker-compose up -d
    print_success "Services started"
    
    # Wait for services to be ready
    print_info "Waiting for services to be ready..."
    sleep 10
    
    # Check health
    echo ""
    print_header "Service Health Status"
    
    # Check backend
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Backend is healthy (http://localhost:8000)"
    else
        print_error "Backend is not responding"
    fi
    
    # Check frontend
    if curl -s http://localhost:5173 > /dev/null 2>&1 || netstat -tuln | grep 5173 > /dev/null; then
        print_success "Frontend is running (http://localhost:5173)"
    else
        print_error "Frontend is not responding"
    fi
    
    # Check database
    if docker exec bank-db pg_isready -U bankuser > /dev/null 2>&1; then
        print_success "Database is ready"
    else
        print_error "Database is not responding"
    fi
    
    echo ""
    print_header "System Started Successfully"
    echo ""
    echo "Access Points:"
    echo "  - Frontend:      http://localhost:5173"
    echo "  - Backend API:   http://localhost:8000"
    echo "  - API Docs:      http://localhost:8000/docs"
    echo "  - Database:      localhost:5432"
    echo ""
    echo "Default Credentials:"
    echo "  - Admin Email:   admin@digitalbank.com"
    echo "  - Admin Pass:    Admin@123456"
    echo ""
}

stop_system() {
    print_header "Stopping Banking Platform"
    
    docker-compose down
    print_success "Services stopped"
}

show_logs() {
    print_header "Service Logs"
    
    if [ "$1" == "backend" ]; then
        docker-compose logs -f backend
    elif [ "$1" == "frontend" ]; then
        docker-compose logs -f frontend
    elif [ "$1" == "db" ]; then
        docker-compose logs -f db
    else
        docker-compose logs -f
    fi
}

clean_system() {
    print_header "Cleaning System"
    
    docker-compose down -v
    print_success "Containers and volumes removed"
    
    echo ""
    print_info "Note: Source code and configuration files preserved"
}

show_status() {
    print_header "System Status"
    docker-compose ps
}

test_integration() {
    print_header "Running Integration Tests"
    
    # Run backend integration tests
    docker-compose exec backend python integration_tests.py
    
    print_success "Integration tests completed"
}

# ===== MAIN MENU =====

print_header "Banking Platform - Integrated System"

case "${1:-start}" in
    start)
        check_requirements
        start_system
        ;;
    stop)
        stop_system
        ;;
    restart)
        stop_system
        sleep 2
        start_system
        ;;
    logs)
        show_logs "$2"
        ;;
    status)
        show_status
        ;;
    clean)
        clean_system
        ;;
    test)
        test_integration
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|clean|test} [service]"
        echo ""
        echo "Commands:"
        echo "  start       - Start all services"
        echo "  stop        - Stop all services"
        echo "  restart     - Restart all services"
        echo "  logs        - Show service logs (optionally specify: backend|frontend|db)"
        echo "  status      - Show services status"
        echo "  clean       - Stop and remove containers/volumes"
        echo "  test        - Run integration tests"
        exit 1
        ;;
esac
