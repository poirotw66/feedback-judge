set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_HOST=${API_HOST:-"0.0.0.0"}
API_PORT=${API_PORT:-8003}
CONDA_ENV_NAME=${CONDA_ENV_NAME:-"crawl4ai"}

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}"
    echo "============================================================"
    echo "身心障礙手冊AI測試結果準確度評分系統"
    echo "Disability Certificate AI Accuracy Evaluator API"
    echo "============================================================"
    echo -e "${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check conda installation
check_conda() {
    if ! command_exists "conda"; then
        print_error "Conda not found. Please install Anaconda or Miniconda."
        exit 1
    fi
    print_success "Conda found"
}

# Function to activate conda environment
activate_conda_env() {
    print_info "Activating conda environment: $CONDA_ENV_NAME"
    
    # Check if conda environment exists
    if ! conda env list | grep -q "^$CONDA_ENV_NAME "; then
        print_error "Conda environment '$CONDA_ENV_NAME' not found."
        print_info "Available environments:"
        conda env list
        exit 1
    fi
    
    # Initialize conda for bash (if not already done)
    eval "$(conda shell.bash hook)"
    
    # Activate the environment
    conda activate "$CONDA_ENV_NAME"
    print_success "Conda environment '$CONDA_ENV_NAME' activated"
    
    # Show Python version in the environment
    python_version=$(python --version 2>&1)
    print_info "Using $python_version in conda environment"
}

# Function to check required files
check_required_files() {
    print_info "Checking required files..."
    
    required_files=(
        "api/app.py"
        "api/evaluator_core.py"
        "api/evaluator_service.py"
        "api/excel_generator.py"
        "api/models.py"
        "api/exceptions.py"
        "requirements.txt"
    )
    
    missing_files=()
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -ne 0 ]; then
        print_error "Missing required files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi
    
    print_success "All required files are present"
}

# Function to start the API
start_api() {
    print_info "Starting API server..."
    print_info "Conda Environment: $CONDA_ENV_NAME"
    print_info "Host: $API_HOST"
    print_info "Port: $API_PORT"
    print_info "API Documentation: http://localhost:$API_PORT/feedback-service/docs"
    print_info "ReDoc Documentation: http://localhost:$API_PORT/feedback-service/redoc"
    echo ""
    print_success "服務端點 (Service Endpoints):"
    print_info "  - 主服務: http://localhost:$API_PORT/feedback-service/"
    print_info "  - 健康檢查: http://localhost:$API_PORT/feedback-service/health"
    print_info "  - 身心障礙評估: http://localhost:$API_PORT/feedback-service/evaluate"
    print_info "  - 外來函文評估: http://localhost:$API_PORT/feedback-service/evaluate-document"
    echo ""
    print_info "Press Ctrl+C to stop the server"
    echo ""
    
    # Determine if we should use reload mode
    RELOAD_MODE="--reload"
    if [ "$1" = "--prod" ] || [ "$1" = "--production" ]; then
        RELOAD_MODE=""
        print_info "Running in production mode (no auto-reload)"
    else
        print_info "Running in development mode (auto-reload enabled)"
    fi
    
    # Start the API using uvicorn
    uvicorn api.app:app \
        --host "$API_HOST" \
        --port "$API_PORT" \
        --log-level info \
        $RELOAD_MODE
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help, -h          Show this help message"
    echo "  --prod, --production Run in production mode (no auto-reload)"
    echo ""
    echo "Environment Variables:"
    echo "  API_HOST            API host (default: 0.0.0.0)"
    echo "  API_PORT            API port (default: 8000)"
    echo "  CONDA_ENV_NAME      Conda environment name (default: crawl4ai)"
    echo ""
    echo "Examples:"
    echo "  $0                           # Start in development mode"
    echo "  $0 --prod                    # Start in production mode"
    echo "  API_PORT=8080 $0             # Start on port 8080"
    echo "  CONDA_ENV_NAME=myenv $0      # Use different conda environment"
    echo ""
}

# Function to cleanup on exit
cleanup() {
    print_info "Shutting down API server..."
    print_success "API server stopped"
}

# Trap cleanup function on script exit
trap cleanup EXIT

# Main execution
main() {
    print_header
    
    # Parse command line arguments
    PROD_MODE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                exit 0
                ;;
            --prod|--production)
                PROD_MODE=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Check conda installation
    check_conda
    
    # Activate conda environment
    activate_conda_env
    
    # Check required files
    check_required_files
    
    # Start the API
    if [ "$PROD_MODE" = true ]; then
        start_api --prod
    else
        start_api
    fi
}

# Run main function with all arguments
main "$@"