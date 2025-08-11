#!/usr/bin/env python3

import asyncio
import logging
from scrapers.enhanced_linkedin_scraper import EnhancedLinkedInScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_job_count():
    """Test how many jobs are returned by the enhanced scraper"""
    try:
        scraper = EnhancedLinkedInScraper()
        
        # Test with a common job search
        job_title = "Software Engineer"
        location = "Lagos"
        max_jobs = 5
        
        logger.info(f"Testing enhanced LinkedIn scraper with max_jobs={max_jobs}")
        
        jobs = await scraper.scrape_jobs_with_contacts(job_title, location, max_jobs)
        
        logger.info(f"Total jobs returned: {len(jobs)}")
        
        for i, job in enumerate(jobs, 1):
            logger.info(f"Job {i}: {job.title} at {job.company}")
            logger.info(f"  - Email: {job.email}")
            logger.info(f"  - Poster: {job.poster_name}")
            logger.info(f"  - Position: {job.poster_position}")
            logger.info("---")
        
        return len(jobs)
        
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        return 0

if __name__ == "__main__":
    result = asyncio.run(test_job_count())
    print(f"\nFinal result: {result} jobs found")
