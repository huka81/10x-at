#!/bin/bash
# Setup script for Unix/Linux/macOS

echo "🏦 Banking Application Setup"
echo "================================"

# Check Python version
echo ""
echo "1. Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    if [[ $PYTHON_VERSION =~ Python\ 3\.1[1-9] ]]; then
        echo "   ✓ $PYTHON_VERSION"
    else
        echo "   ✗ Python 3.11+ required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    echo "   ✗ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check PostgreSQL
echo ""
echo "2. Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version 2>&1)
    echo "   ✓ $PSQL_VERSION"
else
    echo "   ✗ PostgreSQL not found. Please install PostgreSQL 14+"
    exit 1
fi

# Install Python dependencies
echo ""
echo "3. Installing Python dependencies..."
pip3 install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "   ✓ Dependencies installed"
else
    echo "   ✗ Failed to install dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
echo ""
echo "4. Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "   ✓ Created .env file from .env.example"
    echo "   ⚠ Please update .env with your PostgreSQL credentials"
else
    echo "   ✓ .env file already exists"
fi

# Instructions for database setup
echo ""
echo "5. Next steps:"
echo "   a. Update database credentials in .env file"
echo "   b. Create database: createdb banking_app"
echo "   c. Run migrations: yoyo apply --config yoyo.ini"
echo "   d. Run tests: pytest"
echo "   e. Start app: streamlit run app.py"

echo ""
echo "✓ Setup complete!"
echo "Read MIGRATION.md for details about the TypeScript to Python migration."
