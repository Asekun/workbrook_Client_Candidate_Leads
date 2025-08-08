#!/usr/bin/env python3
"""
Test script to verify ChromeDriver and Chromium installation
"""

import logging
import platform
import shutil
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chromedriver_setup():
    """Test ChromeDriver and Chromium setup"""
    
    print("Testing ChromeDriver and Chromium setup...")
    
    # Check system
    system = platform.system().lower()
    print(f"System: {system}")
    
    # Check Chromium installation
    chromium_path = shutil.which("chromium-browser") or shutil.which("chromium")
    if chromium_path:
        print(f"✓ Chromium found at: {chromium_path}")
    else:
        print("✗ Chromium not found")
    
    # Check ChromeDriver installation
    chromedriver_path = shutil.which("chromedriver")
    if chromedriver_path:
        print(f"✓ ChromeDriver found at: {chromedriver_path}")
    else:
        print("✗ ChromeDriver not found in PATH")
        
        # Check common paths
        common_paths = [
            "/usr/bin/chromedriver",
            "/usr/local/bin/chromedriver",
            "/snap/bin/chromedriver"
        ]
        for path in common_paths:
            if os.path.exists(path):
                print(f"✓ ChromeDriver found at: {path}")
                chromedriver_path = path
                break
        else:
            print("✗ ChromeDriver not found in common paths")
    
    # Test WebDriver initialization
    print("\nTesting WebDriver initialization...")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    
    try:
        if system == "linux" and chromium_path:
            print("Attempting to use Chromium with ChromeDriver...")
            options.binary_location = chromium_path
            
            if chromedriver_path:
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
                print("✓ Successfully initialized WebDriver with Chromium and ChromeDriver")
            else:
                print("ChromeDriver not found, trying webdriver_manager...")
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                print("✓ Successfully initialized WebDriver with webdriver_manager")
        else:
            print("Using webdriver_manager for Chrome...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            print("✓ Successfully initialized WebDriver with webdriver_manager")
        
        # Test basic functionality
        print("Testing basic WebDriver functionality...")
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✓ Successfully loaded page with title: {title}")
        
        driver.quit()
        print("✓ WebDriver test completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ WebDriver test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_chromedriver_setup()
    if success:
        print("\n🎉 All tests passed! Your setup is working correctly.")
    else:
        print("\n❌ Tests failed. Please check your installation.")
        exit(1)
