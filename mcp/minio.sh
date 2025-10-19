#!/bin/bash
# MinIO Docker Management Script

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

COMPOSE_FILE="docker-compose.minio.yml"
CONTAINER_NAME="kubric-minio"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

case "$1" in
    start)
        print_info "Starting MinIO..."
        docker compose -f $COMPOSE_FILE up -d
        print_info "Waiting for MinIO to be ready..."
        sleep 5
        docker compose -f $COMPOSE_FILE ps
        print_success "MinIO is running!"
        echo ""
        print_info "Access details:"
        echo "  ${BLUE}MinIO Console:${NC} http://localhost:9001"
        echo "  ${BLUE}MinIO API:${NC}     http://localhost:9000"
        echo "  ${BLUE}Username:${NC}      ${MINIO_ROOT_USER:-minioadmin}"
        echo "  ${BLUE}Password:${NC}      ${MINIO_ROOT_PASSWORD:-minioadmin}"
        echo ""
        print_info "Default buckets created:"
        echo "  - videos"
        echo "  - embeddings"
        echo "  - thumbnails"
        ;;

    stop)
        print_info "Stopping MinIO..."
        docker compose -f $COMPOSE_FILE down
        print_success "MinIO stopped."
        ;;

    restart)
        print_info "Restarting MinIO..."
        docker compose -f $COMPOSE_FILE restart
        print_success "MinIO restarted."
        ;;

    logs)
        docker compose -f $COMPOSE_FILE logs -f minio
        ;;

    status)
        docker compose -f $COMPOSE_FILE ps
        ;;

    console)
        print_info "Opening MinIO Console..."
        echo "Console URL: http://localhost:9001"
        echo "Username: ${MINIO_ROOT_USER:-minioadmin}"
        echo "Password: ${MINIO_ROOT_PASSWORD:-minioadmin}"
        if command -v open &> /dev/null; then
            open http://localhost:9001
        elif command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:9001
        else
            print_warning "Please open http://localhost:9001 in your browser"
        fi
        ;;

    bucket)
        if [ -z "$2" ]; then
            print_error "Please provide a bucket name"
            echo "Usage: ./minio.sh bucket <bucket-name>"
            exit 1
        fi
        print_info "Creating bucket: $2"
        docker exec $CONTAINER_NAME mc mb /data/$2 --ignore-existing
        print_success "Bucket '$2' created successfully"
        ;;

    list)
        print_info "Listing all buckets..."
        docker exec $CONTAINER_NAME mc ls /data/
        ;;

    clean)
        print_warning "This will remove all MinIO data. Are you sure? (y/N)"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            print_info "Stopping and removing MinIO container and volumes..."
            docker compose -f $COMPOSE_FILE down -v
            print_success "MinIO data removed."
        else
            print_info "Operation cancelled."
        fi
        ;;

    test)
        print_info "Testing MinIO connection..."
        if command -v poetry &> /dev/null; then
            poetry run python docker/minio/test_connection.py
        elif command -v python3 &> /dev/null; then
            python3 docker/minio/test_connection.py
        else
            print_error "Python3 not found. Please install Python to run the test."
            exit 1
        fi
        ;;

    upload)
        if [ -z "$2" ] || [ -z "$3" ]; then
            print_error "Please provide bucket name and file path"
            echo "Usage: ./minio.sh upload <bucket-name> <file-path>"
            exit 1
        fi
        print_info "Uploading $3 to bucket $2..."
        docker exec $CONTAINER_NAME mc cp $3 /data/$2/
        print_success "File uploaded successfully"
        ;;

    info)
        print_info "MinIO Server Information:"
        docker exec $CONTAINER_NAME mc admin info local
        ;;

    *)
        echo "MinIO Docker Management Script"
        echo ""
        echo "Usage: ./minio.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start              - Start MinIO container"
        echo "  stop               - Stop MinIO container"
        echo "  restart            - Restart MinIO container"
        echo "  logs               - View MinIO logs (follow mode)"
        echo "  status             - Show container status"
        echo "  console            - Open MinIO Console in browser"
        echo "  bucket <name>      - Create a new bucket"
        echo "  list               - List all buckets"
        echo "  clean              - Remove container and all data (WARNING: destructive)"
        echo "  test               - Test MinIO connection with Python"
        echo "  upload <bucket> <file> - Upload a file to a bucket"
        echo "  info               - Show MinIO server information"
        echo ""
        echo "Examples:"
        echo "  ./minio.sh start"
        echo "  ./minio.sh bucket my-videos"
        echo "  ./minio.sh upload videos /path/to/video.mp4"
        echo "  ./minio.sh console"
        echo ""
        exit 1
        ;;
esac
