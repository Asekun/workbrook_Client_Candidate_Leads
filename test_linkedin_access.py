#!/usr/bin/env python3
"""
Test LinkedIn accessibility from the server
"""

import asyncio
import requests
from playwright.async_api import async_playwright

async def test_linkedin_access():
    """Test if LinkedIn is accessible from the server"""
    
    print("Testing LinkedIn accessibility...")
    
    # Test 1: Basic HTTP request
    try:
        response = requests.get('https://www.linkedin.com', timeout=10)
        print(f"✓ HTTP request successful: Status {response.status_code}")
    except Exception as e:
        print(f"✗ HTTP request failed: {str(e)}")
    
    # Test 2: Playwright basic access
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Set a shorter timeout for testing
            page.set_default_timeout(15000)
            
            print("Attempting to load LinkedIn with Playwright...")
            await page.goto('https://www.linkedin.com', wait_until='domcontentloaded')
            
            title = await page.title()
            print(f"✓ Playwright access successful: {title}")
            
            # Check if we can access jobs page
            await page.goto('https://www.linkedin.com/jobs/', wait_until='domcontentloaded')
            jobs_title = await page.title()
            print(f"✓ Jobs page access successful: {jobs_title}")
            
            await browser.close()
            
    except Exception as e:
        print(f"✗ Playwright access failed: {str(e)}")
    
    # Test 3: Check network connectivity
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('www.linkedin.com', 443))
        sock.close()
        
        if result == 0:
            print("✓ Network connectivity to LinkedIn: OK")
        else:
            print("✗ Network connectivity to LinkedIn: FAILED")
            
    except Exception as e:
        print(f"✗ Network test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_linkedin_access())

