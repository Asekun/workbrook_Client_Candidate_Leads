"""
LinkedIn Job Scraper using Playwright

This module provides functionality to scrape job postings from LinkedIn.com
using Playwright instead of Selenium for better reliability and performance.
"""

import asyncio
import logging
import os
from typing import List, Optional
from datetime import datetime
import re
import random
import time

from models import JobPosting
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)

class LinkedInScraperPlaywright:
    """
    Scraper for LinkedIn.com job postings using Playwright
    
    This class uses Playwright for more reliable web scraping
    and better performance on server environments.
    """
    
    def __init__(self):
        """Initialize the LinkedIn scraper with Playwright"""
        self.browser = None
        self.page = None
        
    async def setup_browser(self):
        """Initialize Playwright browser with optimal settings for server"""
        playwright = await async_playwright().start()
        
        # Launch browser with server-optimized settings and anti-detection measures
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-software-rasterizer',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-field-trial-config',
                '--disable-ipc-flooding-protection',
                '--disable-default-apps',
                '--disable-sync',
                '--disable-translate',
                '--disable-background-networking',
                '--disable-component-extensions-with-background-pages',
                '--disable-client-side-phishing-detection',
                '--disable-hang-monitor',
                '--disable-prompt-on-repost',
                '--disable-domain-reliability',
                '--disable-features=TranslateUI',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--disable-javascript',
                '--disable-css',
                '--disable-background-networking',
                '--disable-sync',
                '--disable-translate',
                '--disable-default-apps',
                '--disable-extensions-file-access-check',
                '--disable-extensions-http-throttling',
                '--disable-ipc-flooding-protection',
                '--disable-renderer-backgrounding',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-features=TranslateUI',
                '--disable-features=VizDisplayCompositor',
                '--disable-software-rasterizer',
                '--disable-gpu-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-accelerated-jpeg-decoding',
                '--disable-accelerated-mjpeg-decode',
                '--disable-accelerated-video-decode',
                '--disable-gpu-memory-buffer-video-frames',
                '--remote-debugging-port=9222'
            ]
        )
        
        # Create context with optimized settings and anti-detection measures
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            },
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        self.page = await context.new_page()
        
        # Set page load timeout and add anti-detection measures
        self.page.set_default_timeout(60000)  # Increase timeout to 60 seconds
        
        # Add JavaScript to hide automation indicators
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            window.chrome = {
                runtime: {},
            };
        """)
        
        return playwright
        
    async def scrape_jobs_fallback(self, job_title: str, location: str, max_jobs: int = 5) -> List[JobPosting]:
        """
        Fallback scraping method using a different approach
        """
        try:
            logger.info("Using fallback scraping method...")
            
            # Try a different URL format
            search_url = f"https://www.linkedin.com/jobs/search?keywords={job_title}&location={location}&f_TPR=r86400"
            
            await self.page.goto(search_url, wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            # Try to find job cards with a different selector
            job_cards = await self.page.query_selector_all('[data-job-id]')
            
            if not job_cards:
                # Try another selector
                job_cards = await self.page.query_selector_all('.job-search-card')
            
            logger.info(f"Found {len(job_cards)} job cards with fallback method")
            
            jobs = []
            for i, job_card in enumerate(job_cards[:max_jobs]):
                try:
                    # Extract basic information
                    title_element = await job_card.query_selector('h3, .job-search-card__title')
                    company_element = await job_card.query_selector('h4, .job-search-card__subtitle')
                    location_element = await job_card.query_selector('.job-search-card__location')
                    
                    if title_element:
                        job_title = await title_element.inner_text()
                        company = await company_element.inner_text() if company_element else "Unknown Company"
                        location = await location_element.inner_text() if location_element else "Unknown Location"
                        
                        # Create basic job posting
                        job_posting = JobPosting(
                            title=job_title.strip(),
                            company=company.strip(),
                            location=location.strip(),
                            url="",
                            description="",
                            poster_name="",
                            poster_position="",
                            email="",
                            date_posted=""
                        )
                        
                        jobs.append(job_posting)
                        logger.info(f'Scraped "{job_title}" at {company} in {location}...')
                        
                except Exception as e:
                    logger.warning(f"Error processing job {i+1} in fallback: {str(e)}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Fallback method also failed: {str(e)}")
            return []

    async def scrape_jobs(self, job_title: str, location: str, max_jobs: int = 5) -> List[JobPosting]:
        """
        Scrape job postings from LinkedIn using Playwright
        
        Args:
            job_title: Job title to search for
            location: Job location
            max_jobs: Maximum number of jobs to scrape (default: 5)
            
        Returns:
            List of JobPosting objects
        """
        playwright = None
        try:
            logger.info(f"Starting LinkedIn scrape for: {job_title} in {location}")
            
            # Setup browser
            playwright = await self.setup_browser()
            
            # Navigate to LinkedIn jobs search with retry logic
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}"
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Attempting to load LinkedIn (attempt {attempt + 1}/{max_retries})")
                    
                    # Navigate to the page
                    await self.page.goto(search_url, wait_until='domcontentloaded')
                    
                    # Wait for page to load with different strategies
                    try:
                        await self.page.wait_for_load_state('networkidle', timeout=30000)
                    except:
                        # If networkidle fails, wait for specific elements
                        await self.page.wait_for_selector('.base-card', timeout=30000)
                    
                    # Check if page loaded successfully
                    page_title = await self.page.title()
                    if 'LinkedIn' in page_title or 'Jobs' in page_title:
                        logger.info("LinkedIn page loaded successfully")
                        break
                    else:
                        raise Exception("Page title doesn't match expected LinkedIn page")
                        
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        # Try fallback method
                        logger.info("Main method failed, trying fallback...")
                        return await self.scrape_jobs_fallback(job_title, location, max_jobs)
                    
                    # Wait before retry
                    await asyncio.sleep(5)
            
            # Scroll and load more jobs
            pages = max(2, (max_jobs + 24) // 25)  # Minimum 2 pages for better results
            
            for i in range(pages):
                logger.info(f"Loading page {i+1}...")
                
                # Scroll to bottom to load more jobs
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(random.uniform(2, 4))
                
                # Try to click "Show more" button if available
                try:
                    show_more_button = self.page.locator('button:has-text("Show more")')
                    if await show_more_button.is_visible():
                        await show_more_button.click()
                        await asyncio.sleep(random.uniform(3, 6))
                except Exception:
                    logger.info("Show more button not found or not clickable")
                
                # Wait for new content to load
                await asyncio.sleep(random.uniform(2, 4))
            
            # Extract job listings
            jobs = []
            job_cards = await self.page.query_selector_all('.base-card')
            
            logger.info(f"Found {len(job_cards)} job cards")
            
            for i, job_card in enumerate(job_cards[:max_jobs]):
                try:
                    # Extract basic job information
                    title_element = await job_card.query_selector('h3.base-search-card__title')
                    company_element = await job_card.query_selector('h4.base-search-card__subtitle')
                    location_element = await job_card.query_selector('.job-search-card__location')
                    link_element = await job_card.query_selector('a.base-card__full-link')
                    
                    if not all([title_element, company_element, location_element, link_element]):
                        continue
                    
                    job_title = await title_element.inner_text()
                    company = await company_element.inner_text()
                    location = await location_element.inner_text()
                    apply_link = await link_element.get_attribute('href')
                    
                    # Clean up text
                    job_title = job_title.strip()
                    company = company.strip()
                    location = location.strip()
                    
                    # Navigate to job details page
                    await self.page.goto(apply_link)
                    await self.page.wait_for_load_state('networkidle')
                    
                    # Extract detailed information
                    job_description = ""
                    poster_name = ""
                    poster_position = ""
                    email = ""
                    date_posted = ""
                    
                    # Get job description
                    try:
                        description_element = await self.page.query_selector('.description__text--rich')
                        if description_element:
                            job_description = await description_element.inner_text()
                    except Exception:
                        pass
                    
                    # Get poster information
                    try:
                        poster_section = await self.page.query_selector('.job-details-jobs-unified-top-card__job-insight')
                        if poster_section:
                            poster_text = await poster_section.inner_text()
                            if "Posted by" in poster_text:
                                poster_name = poster_text.replace("Posted by", "").strip()
                            else:
                                posted_match = re.search(r'Posted by (.+?)(?:\s+•|\s*$)', poster_text)
                                if posted_match:
                                    poster_name = posted_match.group(1).strip()
                    except Exception:
                        pass
                    
                    # Get position information
                    try:
                        position_element = await self.page.query_selector('.job-details-jobs-unified-top-card__job-insight')
                        if position_element:
                            poster_position = await position_element.inner_text()
                    except Exception:
                        pass
                    
                    # Extract email from description
                    if job_description:
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        email_match = re.search(email_pattern, job_description)
                        if email_match:
                            email = email_match.group(0)
                    
                    # Get date posted
                    try:
                        date_element = await self.page.query_selector('time')
                        if date_element:
                            date_posted = await date_element.get_attribute('datetime')
                            if not date_posted:
                                date_posted = await date_element.inner_text()
                    except Exception:
                        pass
                    
                    # Get updated apply link
                    try:
                        apply_button = await self.page.query_selector('a.jobs-apply-button')
                        if apply_button:
                            new_apply_link = await apply_button.get_attribute('href')
                            if new_apply_link:
                                apply_link = new_apply_link
                    except Exception:
                        pass
                    
                    # Create JobPosting object
                    job_posting = JobPosting(
                        title=job_title,
                        company=company,
                        location=location,
                        url=apply_link,
                        description=job_description,
                        poster_name=poster_name,
                        poster_position=poster_position,
                        email=email,
                        date_posted=date_posted
                    )
                    
                    jobs.append(job_posting)
                    logger.info(f'Scraped "{job_title}" at {company} in {location}...')
                    
                    # Random delay between jobs
                    await asyncio.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.warning(f"Error processing job {i+1}: {str(e)}")
                    continue
            
            logger.info(f"Successfully scraped {len(jobs)} jobs from LinkedIn")
            return jobs
            
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {str(e)}")
            raise
        finally:
            if self.browser:
                await self.browser.close()
            if playwright:
                await playwright.stop()


# Async wrapper for compatibility with existing code
async def scrape_linkedin_jobs_playwright(job_title: str, location: str, pages: int = None) -> list:
    """
    Async wrapper for the Playwright LinkedIn scraper
    """
    scraper = LinkedInScraperPlaywright()
    max_jobs = (pages or 1) * 25
    jobs = await scraper.scrape_jobs(job_title, location, max_jobs)
    
    # Convert to the format expected by the existing code
    job_data = []
    for job in jobs:
        job_data.append({
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "poster_name": job.poster_name,
            "poster_position": job.poster_position,
            "apply_link": job.url,
            "email": job.email,
            "date_posted": job.date_posted,
        })
    
    return job_data
