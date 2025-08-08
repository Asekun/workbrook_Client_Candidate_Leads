"""
Test script for Google Jobs scraper

This script tests the Google Jobs scraper functionality.
"""

import asyncio
import logging
from scrapers.google_jobs_scraper import GoogleJobsScraper
from utils.browser_manager import BrowserManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_google_jobs_scraper():
    """Test the Google Jobs scraper"""
    try:
        logger.info("Starting Google Jobs scraper test")
        
        # Test parameters
        job_title = "software engineer"
        location = "lagos"
        max_jobs = 3
        
        logger.info(f"Testing with: {job_title} in {location}, max {max_jobs} jobs")
        
        # Use browser manager as async context manager
        async with BrowserManager() as browser_manager:
            # Create scraper instance
            scraper = GoogleJobsScraper(browser_manager)
            
            # Scrape jobs
            jobs = await scraper.scrape_jobs(job_title, location, max_jobs)
            
            logger.info(f"Successfully scraped {len(jobs)} jobs")
            
            # Print job details
            for i, job in enumerate(jobs, 1):
                logger.info(f"Job {i}:")
                logger.info(f"  Title: {job.title}")
                logger.info(f"  Company: {job.company}")
                logger.info(f"  Location: {job.location}")
                logger.info(f"  URL: {job.url}")
                logger.info(f"  Date Posted: {job.date_posted}")
                if job.description:
                    logger.info(f"  Description: {job.description[:100]}...")
                logger.info("---")
            
            return jobs
            
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        raise

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_google_jobs_scraper())
