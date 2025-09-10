#!/bin/bash

# Flask App Local Server Startup Script
# This script starts a local instance of the Flask application for testing

echo "🚀 Starting Flask App Local Server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python3 is not installed or not in PATH"
    exit 1
fi

# Check if the app.py file exists
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found in current directory"
    echo "Please run this script from the flask_app directory"
    exit 1
fi

# Install requirements if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing/updating dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "⚠️  Warning: Some dependencies might not have installed correctly"
    fi
fi

echo ""
echo "🌐 Starting Flask development server..."
echo "📍 Server will be available at: http://localhost:8080"
echo "🛑 Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the Flask application
python3 app.py
