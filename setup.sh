#!/bin/bash

# EcoTide Project Setup Script
# This script sets up the complete EcoTide development environment

set -e  # Exit on any error

echo "🌱 Setting up EcoTide - Sustainable Shopping Assistant"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if script is run from project root
if [ ! -f "README.md" ] || [ ! -d "ecotide-extension" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    local missing_deps=()
    
    if ! command_exists node; then
        missing_deps+=("Node.js (version 16 or higher)")
    elif [ "$(node -v | cut -d'v' -f2 | cut -d'.' -f1)" -lt 16 ]; then
        print_warning "Node.js version is lower than 16. Some features may not work."
    fi
    
    if ! command_exists npm; then
        missing_deps+=("npm")
    fi
    
    if ! command_exists python3; then
        missing_deps+=("Python 3.8+")
    elif ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        missing_deps+=("Python 3.8+ (current version is too old)")
    fi
    
    if ! command_exists pip3; then
        missing_deps+=("pip3")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        echo ""
        echo "Please install the missing dependencies and run this script again."
        echo ""
        echo "Installation guides:"
        echo "  - Node.js: https://nodejs.org/"
        echo "  - Python: https://python.org/"
        exit 1
    fi
    
    print_success "All dependencies found!"
}

# Setup Chrome Extension
setup_extension() {
    print_status "Setting up Chrome Extension..."
    
    cd ecotide-extension
    
    # Check if package.json exists, if not create it
    if [ ! -f "package.json" ]; then
        print_status "Creating package.json for Chrome Extension..."
        cat > package.json << EOF
{
  "name": "ecotide-extension",
  "version": "1.0.0",
  "description": "EcoTide Chrome Extension for Sustainable Shopping",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "build:extension": "vite build --mode production"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@vitejs/plugin-react": "^4.0.3",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.27",
    "tailwindcss": "^3.3.3",
    "vite": "^4.4.5"
  }
}
EOF
    fi
    
    # Install dependencies
    print_status "Installing Chrome Extension dependencies..."
    npm install
    
    # Build the extension
    print_status "Building Chrome Extension..."
    npm run build
    
    cd ..
    print_success "Chrome Extension setup complete!"
}

# Setup Backend
setup_backend() {
    print_status "Setting up Backend API..."
    
    cd ecotide-backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    print_status "Installing Backend dependencies..."
    pip install -r requirements.txt
    
    cd ..
    print_success "Backend setup complete!"
}

# Setup ML Pipeline
setup_ml() {
    print_status "Setting up ML Pipeline..."
    
    cd ecotide-ml
    
    # Use the same virtual environment as backend
    source ../ecotide-backend/venv/bin/activate
    
    # Install additional ML dependencies if needed
    print_status "Installing ML dependencies..."
    pip install scikit-learn pandas numpy joblib
    
    # Train the initial model
    print_status "Training initial sustainability model..."
    python3 train_model.py --verbose
    
    cd ..
    print_success "ML Pipeline setup complete!"
}

# Create development scripts
create_dev_scripts() {
    print_status "Creating development scripts..."
    
    # Create start script
    cat > start-dev.sh << 'EOF'
#!/bin/bash

# EcoTide Development Start Script

echo "🌱 Starting EcoTide Development Environment"

# Function to run commands in background and track PIDs
run_background() {
    local name=$1
    local command=$2
    local dir=$3
    
    echo "Starting $name..."
    if [ -n "$dir" ]; then
        cd "$dir"
    fi
    $command &
    local pid=$!
    echo "$pid" >> .dev_pids
    echo "$name started with PID $pid"
    if [ -n "$dir" ]; then
        cd - >/dev/null
    fi
}

# Clean up any existing PIDs file
rm -f .dev_pids

# Start Backend API
echo "🚀 Starting Backend API..."
cd ecotide-backend
source venv/bin/activate
python app.py &
echo $! >> ../.dev_pids
echo "Backend API started with PID $!"
cd ..

# Start Chrome Extension Development Server
echo "🎯 Starting Chrome Extension Dev Server..."
cd ecotide-extension
npm run dev &
echo $! >> ../.dev_pids
echo "Extension dev server started with PID $!"
cd ..

echo ""
echo "✅ Development environment started!"
echo ""
echo "🌐 Backend API: http://localhost:8000"
echo "🎨 Extension Dev: http://localhost:5000"
echo ""
echo "📝 To stop all services, run: ./stop-dev.sh"
echo ""
echo "🔧 Chrome Extension Installation:"
echo "   1. Open Chrome and go to chrome://extensions/"
echo "   2. Enable 'Developer mode'"
echo "   3. Click 'Load unpacked' and select the 'ecotide-extension/dist' folder"
echo ""

# Keep script running and wait for user input
echo "Press Ctrl+C to stop all services..."
wait
EOF

    # Create stop script
    cat > stop-dev.sh << 'EOF'
#!/bin/bash

# EcoTide Development Stop Script

echo "🛑 Stopping EcoTide Development Environment"

if [ -f ".dev_pids" ]; then
    while read -r pid; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping process $pid..."
            kill "$pid"
        fi
    done < .dev_pids
    rm -f .dev_pids
    echo "✅ All development services stopped!"
else
    echo "No running services found."
fi
EOF

    # Create ML training script
    cat > train-model.sh << 'EOF'
#!/bin/bash

# EcoTide ML Model Training Script

echo "🧠 Training EcoTide ML Model"

cd ecotide-backend
source venv/bin/activate
cd ../ecotide-ml

echo "Starting model training..."
python3 train_model.py --verbose --tune

if [ $? -eq 0 ]; then
    echo "✅ Model training completed successfully!"
    echo "📊 Model files saved to ecotide-backend/"
else
    echo "❌ Model training failed!"
    exit 1
fi
EOF

    # Create Chrome Extension build script
    cat > build-extension.sh << 'EOF'
#!/bin/bash

# EcoTide Chrome Extension Build Script

echo "📦 Building EcoTide Chrome Extension"

cd ecotide-extension

echo "Installing dependencies..."
npm install

echo "Building extension..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Chrome Extension built successfully!"
    echo "📁 Extension files are in: ecotide-extension/dist/"
    echo ""
    echo "🔧 To install in Chrome:"
    echo "   1. Open Chrome and go to chrome://extensions/"
    echo "   2. Enable 'Developer mode'"
    echo "   3. Click 'Load unpacked' and select the 'ecotide-extension/dist' folder"
else
    echo "❌ Extension build failed!"
    exit 1
fi
EOF

    # Make scripts executable
    chmod +x start-dev.sh stop-dev.sh train-model.sh build-extension.sh
    
    print_success "Development scripts created!"
}

# Create environment file template
create_env_template() {
    print_status "Creating environment configuration..."
    
    cat > .env.example << 'EOF'
# EcoTide Environment Configuration

# Backend Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# ML Model Configuration
MODEL_PATH=ecotide-backend/sustain_model.pkl
VECTORIZER_PATH=ecotide-backend/vectorizer.pkl
ENCODER_PATH=ecotide-backend/label_encoder.pkl

# API Configuration
API_TIMEOUT=30
MAX_RETRIES=3

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=ecotide.log

# External APIs (if needed)
# EXTERNAL_API_KEY=your_api_key_here
# EXTERNAL_API_URL=https://api.example.com

# Development Configuration
ENABLE_CORS=true
DEVELOPMENT_MODE=true
EOF

    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "Environment file created! Edit .env as needed."
    else
        print_warning "Environment file already exists. Check .env.example for updates."
    fi
}

# Main setup process
main() {
    print_status "Starting EcoTide setup process..."
    
    # Check dependencies first
    check_dependencies
    
    # Setup components
    setup_extension
    setup_backend
    setup_ml
    
    # Create development tools
    create_dev_scripts
    create_env_template
    
    echo ""
    echo "🎉 EcoTide setup completed successfully!"
    echo "=================================================="
    echo ""
    echo "📚 Quick Start Guide:"
    echo ""
    echo "1. 🚀 Start development environment:"
    echo "   ./start-dev.sh"
    echo ""
    echo "2. 🔧 Install Chrome Extension:"
    echo "   - Open Chrome → chrome://extensions/"
    echo "   - Enable 'Developer mode'"
    echo "   - Click 'Load unpacked' → select 'ecotide-extension/dist'"
    echo ""
    echo "3. 🧠 Retrain ML model (optional):"
    echo "   ./train-model.sh"
    echo ""
    echo "4. 📦 Rebuild extension:"
    echo "   ./build-extension.sh"
    echo ""
    echo "5. 🛑 Stop development:"
    echo "   ./stop-dev.sh"
    echo ""
    echo "📖 For detailed documentation, see README.md"
    echo ""
    echo "🌱 Happy sustainable shopping with EcoTide!"
}

# Run main setup
main "$@"
