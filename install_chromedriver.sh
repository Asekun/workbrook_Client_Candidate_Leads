#!/bin/bash

# Script to install ChromeDriver on Linux server
# This script will install ChromeDriver and ensure it's compatible with Chromium

echo "Installing ChromeDriver for Linux server..."

# Update package list
sudo apt-get update

# Install wget if not already installed
sudo apt-get install -y wget unzip

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

# Verify installation
if command -v chromedriver &> /dev/null; then
    echo "ChromeDriver installed successfully!"
    chromedriver --version
else
    echo "ChromeDriver installation failed!"
    exit 1
fi

echo "ChromeDriver installation complete!"
