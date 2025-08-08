#!/bin/bash

# Comprehensive setup script for Linux server
# This script installs Chromium, ChromeDriver, and all necessary dependencies

echo "Setting up scraping environment on Linux server..."

# Update package list
sudo apt-get update

# Install system dependencies
sudo apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    software-properties-common \
    apt-transport-https \
    ca-certificates

# Install Chromium
echo "Installing Chromium..."
sudo apt-get install -y chromium-browser

# Verify Chromium installation
if command -v chromium-browser &> /dev/null; then
    echo "Chromium installed successfully!"
    chromium-browser --version
else
    echo "Chromium installation failed!"
    exit 1
fi

# Install ChromeDriver
echo "Installing ChromeDriver..."

# Get the latest ChromeDriver version
CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
echo "Latest ChromeDriver version: $CHROMEDRIVER_VERSION"

# Download ChromeDriver
wget -N "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"

# Unzip and move to /usr/bin
unzip -o chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/chromedriver
sudo chown root:root /usr/bin/chromedriver
sudo chmod +x /usr/bin/chromedriver

# Clean up
rm chromedriver_linux64.zip

# Verify ChromeDriver installation
if command -v chromedriver &> /dev/null; then
    echo "ChromeDriver installed successfully!"
    chromedriver --version
else
    echo "ChromeDriver installation failed!"
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p exports
mkdir -p logs

# Set proper permissions
chmod +x *.sh

echo "Server setup complete!"
echo "You can now run your scraping application."
