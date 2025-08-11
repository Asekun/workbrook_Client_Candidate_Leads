#!/usr/bin/env python3
"""
Test script for the enhanced LinkedIn scraper with company contact extraction
"""

import asyncio
import logging
from scrapers.enhanced_linkedin_scraper import EnhancedLinkedInScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_scraper():
    """Test the enhanced LinkedIn scraper with company contact extraction"""
    try:
        scraper = EnhancedLinkedInScraper()
        jobs = await scraper.scrape_jobs_with_contacts('Software Engineer', 'Lagos', 2)
        
        print(f"\nFound {len(jobs)} enhanced jobs:")
        print("=" * 80)
        
        for i, job in enumerate(jobs, 1):
            print(f"\n{i}. {job.title}")
            print(f"   Company: {job.company}")
            print(f"   Location: {job.location}")
            print(f"   Poster: {job.poster_name or 'Not found'}")
            print(f"   Position: {job.poster_position or 'Not found'}")
            print(f"   Email: {job.email or 'Not found'}")
            print(f"   Date Posted: {job.date_posted or 'Not found'}")
            print(f"   Description Length: {len(job.description or '')} chars")
            print(f"   Apply Link: {job.url or 'Not found'}")
            
            # Show if description contains additional contact info
            if job.description and "--- Company Contact Information ---" in job.description:
                print("   ✅ Enhanced with company contact information")
            
            print("-" * 40)
            
    except Exception as e:
        logger.error(f"Error testing enhanced scraper: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_enhanced_scraper())
