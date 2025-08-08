#!/bin/bash

# Script to fix ChromeDriver version compatibility with Chromium
echo "Fixing ChromeDriver version compatibility..."

# Get Chromium version
CHROMIUM_VERSION=$(chromium-browser --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 | cut -d. -f1)
echo "Chromium major version: $CHROMIUM_VERSION"

if [ -z "$CHROMIUM_VERSION" ]; then
    echo "Could not determine Chromium version"
    exit 1
fi

# Remove existing ChromeDriver
echo "Removing existing ChromeDriver..."
sudo rm -f /usr/bin/chromedriver

# Download the correct ChromeDriver version
echo "Downloading ChromeDriver version $CHROMIUM_VERSION..."
wget -N "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROMIUM_VERSION"

if [ ! -f "LATEST_RELEASE_$CHROMIUM_VERSION" ]; then
    echo "Could not find ChromeDriver for version $CHROMIUM_VERSION, trying latest..."
    wget -N "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
    CHROMEDRIVER_VERSION=$(cat LATEST_RELEASE)
else
    CHROMEDRIVER_VERSION=$(cat "LATEST_RELEASE_$CHROMIUM_VERSION")
fi

echo "ChromeDriver version: $CHROMEDRIVER_VERSION"

# Download and install ChromeDriver
wget -N "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip -o chromedriver_linux64.zip
sudo mv chromedriver /usr/bin/chromedriver
sudo chown root:root /usr/bin/chromedriver
sudo chmod +x /usr/bin/chromedriver

# Clean up
rm -f chromedriver_linux64.zip LATEST_RELEASE*

# Test the installation
echo "Testing ChromeDriver installation..."
if command -v chromedriver &> /dev/null; then
    echo "✓ ChromeDriver installed successfully!"
    chromedriver --version
else
    echo "✗ ChromeDriver installation failed!"
    exit 1
fi

echo "ChromeDriver version compatibility fix complete!"
