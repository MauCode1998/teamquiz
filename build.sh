#!/bin/bash

# Build script for Render deployment
echo "Building TeamQuiz for production..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install and build frontend
echo "Building frontend..."
cd frontend
npm install
NODE_OPTIONS=--openssl-legacy-provider npm run build
cd ..

echo "Build completed successfully!"