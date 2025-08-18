#!/bin/bash
# Setup script for the Automotive Ticket Classifier

# Exit on error
set -e

# Function to display messages
log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required commands
log "Checking for required commands..."
REQUIRED_COMMANDS=("python3" "pip" "docker" "docker-compose")
for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command_exists "$cmd"; then
        log "Error: $cmd is not installed. Please install it and try again."
        exit 1
    fi
done
log "All required commands are installed."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    log "Creating .env file from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log ".env file created. Please edit it with your credentials."
    else
        log "Error: .env.example file not found."
        exit 1
    fi
else
    log ".env file already exists."
fi

# Create data directory
log "Creating data directory..."
mkdir -p data
log "Data directory created."

# Check if CSV files exist
if [ ! -f "data/syndicators.csv" ] || [ ! -f "data/rep_dealer_mapping.csv" ]; then
    log "Warning: CSV files not found in data directory."
    log "Please make sure syndicators.csv and rep_dealer_mapping.csv are in the data directory."
fi

# Create schema directory
log "Creating schema directory..."
mkdir -p data/schema
log "Schema directory created."

# Create JSON schema file
if [ ! -f "data/schema/classification.json" ]; then
    log "Creating classification schema file..."
    cat > data/schema/classification.json << 'EOF'
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Classification",
  "type": "object",
  "properties": {
    "contact": {
      "type": "string"
    },
    "dealer_name": {
      "type": "string"
    },
    "dealer_id": {
      "type": "string"
    },
    "rep": {
      "type": "string"
    },
    "category": {
      "type": "string"
    },
    "sub_category": {
      "type": "string"
    },
    "syndicator": {
      "type": "string"
    },
    "inventory_type": {
      "type": "string"
    }
  },
  "required": ["contact", "dealer_name", "dealer_id", "rep", "category", "sub_category", "syndicator", "inventory_type"]
}
EOF
    log "Classification schema file created."
fi

# Setup Python virtual environment
if [ ! -d "venv" ]; then
    log "Creating Python virtual environment..."
    python3 -m venv venv
    log "Virtual environment created."
fi

# Activate virtual environment
log "Activating virtual environment..."
source venv/bin/activate
log "Virtual environment activated."

# Install dependencies
log "Installing Python dependencies..."
pip install -r api/requirements.txt
pip install -r ui/requirements.txt
log "Dependencies installed."

# Setup database with Alembic
log "Setting up database..."
cd api
if command_exists alembic; then
    alembic upgrade head
    log "Database setup complete."
else
    log "Error: alembic command not found. Please check your installation."
    exit 1
fi
cd ..

# Create logs directory
log "Creating logs directory..."
mkdir -p api/logs
log "Logs directory created."

log "Setup complete! You can now start the services with:"
log "docker-compose up -d"
log ""
log "Or run them separately:"
log "cd api && uvicorn main:app --reload --port 8088"
log "cd ui && streamlit run main.py"