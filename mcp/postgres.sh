#!/bin/bash
# PostgreSQL Docker Management Script

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

COMPOSE_FILE="docker-compose.db.yml"
CONTAINER_NAME="postgres-pgvector"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

case "$1" in
    start)
        print_info "Starting PostgreSQL with pgvector..."
        docker compose -f $COMPOSE_FILE up -d
        print_info "Waiting for PostgreSQL to be ready..."
        sleep 5
        docker compose -f $COMPOSE_FILE ps
        print_info "PostgreSQL is running!"
        print_info "Connection details:"
        echo "  Host: ${POSTGRES_HOST:-localhost}"
        echo "  Port: ${POSTGRES_PORT:-5432}"
        echo "  Database: ${POSTGRES_DB:-kubric_db}"
        echo "  User: ${POSTGRES_USER:-postgres}"
        echo "  Password: ${POSTGRES_PASSWORD:-postgres}"
        ;;

    stop)
        print_info "Stopping PostgreSQL..."
        docker compose -f $COMPOSE_FILE down
        print_info "PostgreSQL stopped."
        ;;

    restart)
        print_info "Restarting PostgreSQL..."
        docker compose -f $COMPOSE_FILE restart
        print_info "PostgreSQL restarted."
        ;;

    logs)
        docker compose -f $COMPOSE_FILE logs -f
        ;;

    status)
        docker compose -f $COMPOSE_FILE ps
        ;;

    shell)
        print_info "Connecting to PostgreSQL shell..."
        docker exec -it $CONTAINER_NAME psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-kubric_db}
        ;;

    clean)
        print_warning "This will remove all PostgreSQL data. Are you sure? (y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            print_info "Stopping and removing PostgreSQL container and volumes..."
            docker compose -f $COMPOSE_FILE down -v
            print_info "PostgreSQL data removed."
        else
            print_info "Operation cancelled."
        fi
        ;;

    test)
        print_info "Testing PostgreSQL connection..."
        if command -v poetry &> /dev/null; then
            poetry run python docker/postgres/test_connection.py
        elif command -v python3 &> /dev/null; then
            python3 docker/postgres/test_connection.py
        else
            print_error "Python3 not found. Please install Python to run the test."
            exit 1
        fi
        ;;

    *)
        echo "PostgreSQL Docker Management Script"
        echo ""
        echo "Usage: ./postgres.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start    - Start PostgreSQL container"
        echo "  stop     - Stop PostgreSQL container"
        echo "  restart  - Restart PostgreSQL container"
        echo "  logs     - View PostgreSQL logs (follow mode)"
        echo "  status   - Show container status"
        echo "  shell    - Connect to PostgreSQL shell (psql)"
        echo "  clean    - Remove container and all data (WARNING: destructive)"
        echo "  test     - Test PostgreSQL connection with Python"
        echo ""
        exit 1
        ;;
esac
