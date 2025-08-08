#!/bin/bash

# Setup script for Playwright
echo "Setting up Playwright for web scraping..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements_playwright.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

# Install system dependencies for Playwright
echo "Installing system dependencies for Playwright..."
sudo apt-get update
sudo apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcb-dri3-0

# Test Playwright installation
echo "Testing Playwright installation..."
python -c "
import asyncio
from playwright.async_api import async_playwright

async def test_playwright():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://www.google.com')
        title = await page.title()
        print(f'✓ Playwright test successful! Page title: {title}')
        await browser.close()

asyncio.run(test_playwright())
"

if [ $? -eq 0 ]; then
    echo "✅ Playwright setup completed successfully!"
    echo "You can now use the Playwright-based scraper."
else
    echo "❌ Playwright setup failed. Please check the error messages above."
    exit 1
fi
