#!/bin/bash

# Build script for Render deployment
echo "Building TeamQuiz for production..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install and build frontend
echo "Building frontend..."
cd frontend

# Install dependencies
echo "Installing frontend dependencies..."
npm install

# Build frontend with legacy OpenSSL
echo "Building React app..."
NODE_OPTIONS=--openssl-legacy-provider npm run build

# Check if build was successful
if [ -d "build" ]; then
    echo "Frontend build successful!"
    ls -la build/
else
    echo "Frontend build failed!"
    exit 1
fi

cd ..

echo "Build completed successfully!"