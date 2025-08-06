"""
Indeed Job Scraper

This module provides functionality to scrape job postings from Indeed.com
using Selenium browser automation.
"""

import asyncio
import logging
import urllib.parse
from typing import List, Optional

from utils.browser_manager import BrowserManager
from models import JobPosting

logger = logging.getLogger(__name__)

class IndeedScraper:
    """
    Scraper for Indeed.com job postings
    
    This class handles the scraping of job listings from Indeed with proper
    error handling, rate limiting, and data extraction using Selenium.
    """
    
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
        self.base_url = "https://www.indeed.com"
        
    async def scrape_jobs(self, job_title: str, location: str, max_jobs: int = 10) -> List[JobPosting]:
        """
        Scrape job postings from Indeed
        
        Args:
            job_title: Job title to search for
            location: Job location
            max_jobs: Maximum number of jobs to scrape
            
        Returns:
            List of JobPosting objects
        """
        try:
            # Build search URL
            search_url = self._build_search_url(job_title, location)
            logger.info(f"Navigating to Indeed search URL: {search_url}")
            
            # Navigate to search page
            success = await self.browser_manager.get_page(
                search_url, 
                wait_for_element='[data-jk]',  # Wait for job cards
                timeout=30
            )
            
            if not success:
                raise Exception("Failed to load Indeed search page")
            
            # Check for CAPTCHA
            if await self.browser_manager.handle_captcha():
                raise Exception("CAPTCHA detected on Indeed. Please try again later.")
            
            # Scroll to load more content
            await self.browser_manager.scroll_page()
            
            # Extract job listings
            jobs = await self._extract_job_listings(max_jobs)
            
            logger.info(f"Successfully scraped {len(jobs)} jobs from Indeed")
            return jobs
            
        except Exception as e:
            logger.error(f"Error scraping Indeed: {str(e)}")
            raise
            
    def _build_search_url(self, job_title: str, location: str) -> str:
        """
        Build Indeed search URL with query parameters
        
        Args:
            job_title: Job title to search for
            location: Job location
            
        Returns:
            Formatted search URL
        """
        # Encode parameters
        encoded_job = urllib.parse.quote(job_title)
        encoded_location = urllib.parse.quote(location)
        
        # Build URL
        url = f"{self.base_url}/jobs"
        params = f"q={encoded_job}&l={encoded_location}"
        
        return f"{url}?{params}"
        
    async def _extract_job_listings(self, max_jobs: int) -> List[JobPosting]:
        """
        Extract job listings from the page
        
        Args:
            max_jobs: Maximum number of jobs to extract
            
        Returns:
            List of JobPosting objects
        """
        jobs = []
        
        try:
            # Select job cards - Indeed uses various selectors
            job_selectors = [
                'div[data-jk]',  # Primary selector for job cards
                'div[class*="job_seen_beacon"]',  # Alternative selector
                'div[class*="css-"]'  # Generic CSS class selector
            ]
            
            job_elements = []
            for selector in job_selectors:
                job_elements = await self.browser_manager.find_elements(selector, timeout=10)
                if job_elements:
                    logger.info(f"Found {len(job_elements)} job elements using selector: {selector}")
                    break
                    
            if not job_elements:
                logger.warning("No job elements found with any selector")
                return jobs
                
            # Extract data from each job element
            for i, job_element in enumerate(job_elements[:max_jobs]):
                try:
                    job_data = await self._extract_job_data(job_element)
                    if job_data:
                        jobs.append(job_data)
                        logger.debug(f"Extracted job {i+1}: {job_data.title}")
                        
                except Exception as e:
                    logger.warning(f"Error extracting job {i+1}: {str(e)}")
                    continue
                    
                # Add small delay between extractions
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error extracting job listings: {str(e)}")
            
        return jobs
        
    async def _extract_job_data(self, job_element) -> Optional[JobPosting]:
        """
        Extract individual job data from a job element
        
        Args:
            job_element: Selenium WebElement object
            
        Returns:
            JobPosting object or None if extraction fails
        """
        try:
            # Extract job title
            title_selectors = [
                'h2[class*="jobTitle"] a',
                'h2 a',
                'a[class*="jobTitle"]',
                'span[class*="jobTitle"]',
                'h2 span',
                'a[data-jk]'
            ]
            
            title = None
            job_url = None
            
            for selector in title_selectors:
                try:
                    title = await self.browser_manager.get_element_text(job_element, selector)
                    if title:
                        # Get job URL
                        job_url = await self.browser_manager.get_element_attribute(job_element, selector, 'href')
                        if job_url and not job_url.startswith('http'):
                            job_url = f"{self.base_url}{job_url}"
                        break
                except:
                    continue
                    
            if not title:
                logger.debug("Could not extract job title")
                return None
                
            # Extract company name
            company_selectors = [
                'span[class*="companyName"]',
                'div[class*="companyName"]',
                'span[class*="company"]',
                'div[class*="company"]',
                'span[data-testid="company-name"]'
            ]
            
            company = None
            for selector in company_selectors:
                try:
                    company = await self.browser_manager.get_element_text(job_element, selector)
                    if company:
                        break
                except:
                    continue
                    
            if not company:
                company = "Unknown Company"
                
            # Extract location
            location_selectors = [
                'div[class*="companyLocation"]',
                'span[class*="companyLocation"]',
                'div[class*="location"]',
                'span[class*="location"]',
                'div[data-testid="job-location"]'
            ]
            
            location = None
            for selector in location_selectors:
                try:
                    location = await self.browser_manager.get_element_text(job_element, selector)
                    if location:
                        break
                except:
                    continue
                    
            if not location:
                location = "Unknown Location"
                
            return JobPosting(
                title=title,
                company=company,
                location=location,
                url=job_url
            )
            
        except Exception as e:
            logger.debug(f"Error extracting job data: {str(e)}")
            return None 