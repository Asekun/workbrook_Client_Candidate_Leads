#!/usr/bin/env python3
"""
Test script for the FastAPI Job Scraper

This script demonstrates how to use the job scraper API endpoints.
Run this after starting the FastAPI server.
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, Any

async def test_indeed_scraper():
    """Test Indeed scraping endpoint"""
    print("Testing Indeed scraper...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://localhost:8000/scrape/indeed",
                params={
                    "job": "python developer",
                    "location": "remote",
                    "max_jobs": 5
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Indeed scraper successful!")
                print(f"   Found {data['total_count']} jobs")
                print(f"   Message: {data['message']}")
                
                # Display first 3 jobs
                for i, job in enumerate(data['jobs'][:3], 1):
                    print(f"   {i}. {job['title']}")
                    print(f"      Company: {job['company']}")
                    print(f"      Location: {job['location']}")
                    if job.get('url'):
                        print(f"      URL: {job['url']}")
                    print()
            else:
                print(f"❌ Indeed scraper failed with status {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing Indeed scraper: {str(e)}")

async def test_linkedin_scraper():
    """Test LinkedIn scraping endpoint"""
    print("Testing LinkedIn scraper...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://localhost:8000/scrape/linkedin",
                params={
                    "job": "python developer",
                    "location": "remote",
                    "max_jobs": 5
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ LinkedIn scraper successful!")
                print(f"   Found {data['total_count']} jobs")
                print(f"   Message: {data['message']}")
                
                # Display first 3 jobs
                for i, job in enumerate(data['jobs'][:3], 1):
                    print(f"   {i}. {job['title']}")
                    print(f"      Company: {job['company']}")
                    print(f"      Location: {job['location']}")
                    if job.get('url'):
                        print(f"      URL: {job['url']}")
                    print()
            else:
                print(f"❌ LinkedIn scraper failed with status {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing LinkedIn scraper: {str(e)}")

async def test_excel_export():
    """Test Excel export functionality"""
    print("Testing Excel export...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test LinkedIn Excel export
            response = await client.get(
                "http://localhost:8000/scrape/linkedin/excel",
                params={
                    "job": "python",
                    "location": "remote",
                    "max_jobs": 3
                },
                timeout=120.0
            )
            
            if response.status_code == 200:
                print(f"✅ LinkedIn Excel export successful!")
                print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")
                print(f"   Content-Length: {response.headers.get('content-length', 'Unknown')} bytes")
                
                # Save the file locally for testing
                filename = f"test_linkedin_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"   File saved as: {filename}")
                
            elif response.status_code == 404:
                print(f"⚠️  LinkedIn Excel export: No jobs found (this is normal without login)")
            else:
                print(f"❌ LinkedIn Excel export failed with status {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing Excel export: {str(e)}")

async def test_exports_list():
    """Test exports listing endpoint"""
    print("Testing exports list...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/exports")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Exports list successful!")
                print(f"   Total files: {data['total_files']}")
                print(f"   Export directory: {data['export_directory']}")
                
                if data['exports']:
                    print("   Recent exports:")
                    for export in data['exports'][:3]:  # Show first 3
                        print(f"     - {export['filename']} ({export['size_bytes']} bytes)")
                else:
                    print("   No exports found yet")
                    
            else:
                print(f"❌ Exports list failed with status {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing exports list: {str(e)}")

async def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check successful!")
                print(f"   Status: {data['status']}")
                print(f"   Message: {data['message']}")
            else:
                print(f"❌ Health check failed with status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing health check: {str(e)}")

async def test_root_endpoint():
    """Test root endpoint"""
    print("Testing root endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Root endpoint successful!")
                print(f"   Message: {data['message']}")
                print(f"   Version: {data['version']}")
                print("   Available endpoints:")
                for name, endpoint in data['endpoints'].items():
                    print(f"     {name}: {endpoint}")
            else:
                print(f"❌ Root endpoint failed with status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error testing root endpoint: {str(e)}")

async def main():
    """Run all tests"""
    print("🚀 Starting FastAPI Job Scraper Tests")
    print("=" * 50)
    
    # Test basic endpoints first
    await test_health_check()
    print()
    
    await test_root_endpoint()
    print()
    
    # Test scrapers
    await test_indeed_scraper()
    print()
    
    await test_linkedin_scraper()
    print()
    
    # Test Excel export functionality
    await test_excel_export()
    print()
    
    await test_exports_list()
    print()
    
    print("=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    print("Make sure the FastAPI server is running on http://localhost:8000")
    print("Run: uvicorn main:app --reload")
    print()
    
    # Run the tests
    asyncio.run(main()) 