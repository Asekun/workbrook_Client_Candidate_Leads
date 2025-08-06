"""
LinkedIn Job Scraper

This module provides functionality to scrape job postings from LinkedIn.com
using the existing working scraper implementation.
"""

import asyncio
import logging
import os
from typing import List, Optional
from datetime import datetime

from models import JobPosting

logger = logging.getLogger(__name__)

class LinkedInScraper:
    """
    Scraper for LinkedIn.com job postings
    
    This class uses the existing working LinkedIn scraper implementation
    and adapts it to work with the API structure.
    """
    
    def __init__(self, browser_manager=None):
        """
        Initialize the LinkedIn scraper
        
        Args:
            browser_manager: Not used in this implementation as we use the existing scraper
        """
        # Import the existing working scraper
        from utils.Linkedin_Scrapper import scrape_linkedin_jobs
        self.scrape_linkedin_jobs = scrape_linkedin_jobs
        
    async def scrape_jobs(self, job_title: str, location: str, max_jobs: int = 5) -> List[JobPosting]:
        """
        Scrape job postings from LinkedIn using the existing working implementation
        
        Args:
            job_title: Job title to search for
            location: Job location
            max_jobs: Maximum number of jobs to scrape (default: 5)
            
        Returns:
            List of JobPosting objects
        """
        try:
            logger.info(f"Starting LinkedIn scrape for: {job_title} in {location}")
            
            # Calculate pages based on max_jobs (roughly 25 jobs per page)
            # For better results, we'll scrape more pages to get more jobs
            # The original scraper can handle up to 50 pages, so we'll use more pages
            pages = max(2, (max_jobs + 24) // 25)  # Minimum 2 pages for better results
            
            # Run the existing scraper in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            jobs_data = await loop.run_in_executor(
                None, 
                self.scrape_linkedin_jobs, 
                job_title, 
                location, 
                pages
            )
            
            # Convert the scraped data to JobPosting objects
            job_postings = []
            logger.info(f"Raw jobs data received: {len(jobs_data)} jobs")
            
            # Debug: Check the structure of the first job
            if jobs_data:
                logger.info(f"First job data type: {type(jobs_data[0])}")
                logger.info(f"First job data: {jobs_data[0]}")
            
            for i, job_data in enumerate(jobs_data[:max_jobs]):
                try:
                    logger.debug(f"Processing job {i+1}: {job_data.get('title', 'Unknown')}")
                    
                    # Ensure job_data is a dictionary
                    if not isinstance(job_data, dict):
                        logger.warning(f"Job data is not a dictionary: {type(job_data)} - {job_data}")
                        continue
                    
                    job_posting = JobPosting(
                        title=job_data.get('title', 'Unknown Title'),
                        company=job_data.get('company', 'Unknown Company'),
                        location=job_data.get('location', 'Unknown Location'),
                        url=job_data.get('link', ''),
                        description=job_data.get('description', '')
                    )
                    job_postings.append(job_posting)
                    
                except Exception as e:
                    logger.warning(f"Error converting job data to JobPosting: {str(e)}")
                    continue
            
            logger.info(f"Successfully scraped {len(job_postings)} jobs from LinkedIn")
            return job_postings
            
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {str(e)}")
            raise 