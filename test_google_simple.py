"""
Simple test for Google Jobs scraper
"""

import asyncio
import logging
from scrapers.google_jobs_scraper import GoogleJobsScraper
from utils.browser_manager import BrowserManager

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce log output
logger = logging.getLogger(__name__)

async def test_google_jobs():
    """Test the Google Jobs scraper"""
    try:
        print("Starting Google Jobs scraper test...")
        
        # Test parameters
        job_title = "software engineer"
        location = "lagos"
        max_jobs = 2
        
        print(f"Testing with: {job_title} in {location}, max {max_jobs} jobs")
        
        # Use browser manager as async context manager
        async with BrowserManager() as browser_manager:
            # Create scraper instance
            scraper = GoogleJobsScraper(browser_manager)
            
            # Scrape jobs
            jobs = await scraper.scrape_jobs(job_title, location, max_jobs)
            
            print(f"Successfully scraped {len(jobs)} jobs")
            
            # Print job details
            for i, job in enumerate(jobs, 1):
                print(f"\nJob {i}:")
                print(f"  Title: {job.title}")
                print(f"  Company: {job.company}")
                print(f"  Location: {job.location}")
                print(f"  URL: {job.url}")
                print(f"  Date Posted: {job.date_posted}")
                if job.description:
                    print(f"  Description: {job.description[:100]}...")
            
            return jobs
            
    except Exception as e:
        print(f"Error during test: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_google_jobs())
