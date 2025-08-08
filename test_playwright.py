#!/usr/bin/env python3
"""
Test script to verify Playwright installation and functionality
"""

import asyncio
import sys
from playwright.async_api import async_playwright

async def test_playwright():
    """Test Playwright installation and basic functionality"""
    
    print("Testing Playwright installation...")
    
    try:
        async with async_playwright() as p:
            print("✓ Playwright started successfully")
            
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            print("✓ Browser launched successfully")
            
            # Create page
            page = await browser.new_page()
            print("✓ Page created successfully")
            
            # Navigate to a test page
            await page.goto('https://www.google.com')
            print("✓ Navigation successful")
            
            # Get page title
            title = await page.title()
            print(f"✓ Page title: {title}")
            
            # Test basic interaction
            await page.fill('input[name="q"]', 'test')
            print("✓ Form interaction successful")
            
            # Close browser
            await browser.close()
            print("✓ Browser closed successfully")
            
            print("\n🎉 All Playwright tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Playwright test failed: {str(e)}")
        return False

async def test_linkedin_scraper():
    """Test the LinkedIn scraper with Playwright"""
    
    print("\nTesting LinkedIn scraper with Playwright...")
    
    try:
        from scrapers.linkedin_scraper_playwright import scrape_linkedin_jobs_playwright
        
        # Test with a simple search
        jobs = await scrape_linkedin_jobs_playwright("Software Engineer", "Lagos", 1)
        
        print(f"✓ LinkedIn scraper test successful!")
        print(f"✓ Found {len(jobs)} jobs")
        
        if jobs:
            print(f"✓ First job: {jobs[0].get('title', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ LinkedIn scraper test failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    
    print("=" * 50)
    print("PLAYWRIGHT TEST SUITE")
    print("=" * 50)
    
    # Test basic Playwright functionality
    basic_test = await test_playwright()
    
    # Test LinkedIn scraper
    scraper_test = await test_linkedin_scraper()
    
    print("\n" + "=" * 50)
    if basic_test and scraper_test:
        print("✅ ALL TESTS PASSED!")
        print("Playwright is ready to use for web scraping.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the error messages above.")
        sys.exit(1)
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
