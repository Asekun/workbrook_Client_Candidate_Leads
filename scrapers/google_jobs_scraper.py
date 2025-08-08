"""
Google Jobs Scraper

This module provides functionality to scrape job postings from Google Jobs
using Selenium WebDriver with anti-detection measures.
"""

import asyncio
import logging
import re
from typing import List, Optional
from datetime import datetime
from urllib.parse import quote_plus
from selenium.webdriver.common.by import By

from models import JobPosting
from utils.browser_manager import BrowserManager

logger = logging.getLogger(__name__)

class GoogleJobsScraper:
    """
    Scraper for Google Jobs search results
    
    This class scrapes job postings from Google Jobs using Selenium
    with proper anti-detection measures and error handling.
    """
    
    def __init__(self, browser_manager: Optional[BrowserManager] = None):
        """
        Initialize the Google Jobs scraper
        
        Args:
            browser_manager: Browser manager instance (optional)
        """
        self.browser_manager = browser_manager
        
    async def scrape_jobs(self, job_title: str, location: str, max_jobs: int = 5) -> List[JobPosting]:
        """
        Scrape job postings from Google Jobs
        
        Args:
            job_title: Job title to search for
            location: Job location
            max_jobs: Maximum number of jobs to scrape (default: 5)
            
        Returns:
            List of JobPosting objects
        """
        browser_manager = self.browser_manager or BrowserManager()
        
        try:
            logger.info(f"Starting Google Jobs scrape for: {job_title} in {location}")
            
            async with browser_manager:
                # Construct Google Jobs search URL
                search_query = f"{job_title} jobs in {location}"
                encoded_query = quote_plus(search_query)
                search_url = f"https://www.google.com/search?q={encoded_query}&ibp=htl;jobs"
                
                logger.info(f"Search URL: {search_url}")
                
                # Navigate to Google Jobs
                success = await browser_manager.get_page(
                    search_url, 
                    wait_for_element='[data-ved]',  # Wait for job results
                    timeout=30
                )
                
                if not success:
                    raise Exception("Failed to load Google Jobs page")
                
                # Check for CAPTCHA
                if await browser_manager.handle_captcha():
                    logger.warning("CAPTCHA detected, attempting to continue...")
                    await asyncio.sleep(5)
                
                # Scroll to load more jobs
                await browser_manager.scroll_page()
                
                # Extract job listings
                job_postings = await self._extract_job_listings(
                    browser_manager, 
                    max_jobs
                )
                
                logger.info(f"Successfully scraped {len(job_postings)} jobs from Google Jobs")
                return job_postings
                
        except Exception as e:
            logger.error(f"Error scraping Google Jobs: {str(e)}")
            raise
            
    async def _extract_job_listings(self, browser_manager: BrowserManager, max_jobs: int) -> List[JobPosting]:
        """
        Extract job listings from the Google Jobs page
        
        Args:
            browser_manager: Browser manager instance
            max_jobs: Maximum number of jobs to extract
            
        Returns:
            List of JobPosting objects
        """
        job_postings = []
        
        try:
            # Find job listing containers - Google Jobs uses specific selectors
            job_selectors = [
                'a[class="MQUd2b"]',  # Job card links
                'div[data-ved]',  # Main job container
                'div[jscontroller]',  # Alternative container
                'div[role="article"]',  # Article role
                'div[class*="job"]',  # Class containing "job"
                'div[class*="listing"]',  # Class containing "listing"
                'div[class*="result"]',  # Class containing "result"
                'div[class*="card"]',  # Class containing "card"
                'div[class*="item"]'  # Class containing "item"
            ]
            
            job_elements = []
            for selector in job_selectors:
                elements = await browser_manager.find_elements(selector, timeout=5)
                if elements:
                    # Filter elements that are likely job listings
                    filtered_elements = []
                    for element in elements:
                        try:
                            # Check if element contains job-related content and is clickable
                            text = element.text.lower()
                            if (any(keyword in text for keyword in ['software', 'engineer', 'developer', 'job', 'position', 'role']) and
                                element.is_displayed() and element.is_enabled()):
                                
                                # Additional check: make sure it's not a header or navigation element
                                element_class = element.get_attribute('class') or ''
                                if not any(exclude in element_class.lower() for exclude in ['header', 'nav', 'menu', 'filter', 'search']):
                                    filtered_elements.append(element)
                        except:
                            continue
                    
                    if filtered_elements:
                        job_elements = filtered_elements
                        logger.info(f"Found {len(filtered_elements)} potential job elements using selector: {selector}")
                        break
            
            if not job_elements:
                logger.warning("No job elements found with any selector")
                return job_postings
            
            # Process each job element by extracting data directly from the card
            for i, job_element in enumerate(job_elements[:max_jobs]):
                try:
                    job_posting = await self._extract_job_from_card(job_element, browser_manager, i+1)
                    if job_posting:
                        job_postings.append(job_posting)
                        logger.info(f"Extracted job {i+1}: {job_posting.title}")
                        
                except Exception as e:
                    logger.warning(f"Error extracting job {i+1}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error extracting job listings: {str(e)}")
            
        return job_postings
        
    async def _extract_single_job(self, job_element, browser_manager: BrowserManager) -> Optional[JobPosting]:
        """
        Extract data from a single job element
        
        Args:
            job_element: WebElement representing a job listing
            browser_manager: Browser manager instance
            
        Returns:
            JobPosting object or None if extraction fails
        """
        try:
            # Get the full text of the element for debugging
            element_text = job_element.text
            logger.debug(f"Processing element with text: {element_text[:200]}...")
            
            # Extract job title - try multiple approaches
            title_selectors = [
                'h3',
                'h2',
                'h1',
                '[class*="title"]',
                '[class*="job-title"]',
                '[class*="position"]',
                'div[role="heading"]',
                'span[class*="title"]',
                'a[class*="title"]'
            ]
            
            title = None
            for selector in title_selectors:
                title = await browser_manager.get_element_text(job_element, selector)
                if title and len(title.strip()) > 3:  # Ensure meaningful title
                    break
            
            # If no title found with selectors, try to extract from text
            if not title:
                lines = element_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 3 and any(keyword in line.lower() for keyword in ['engineer', 'developer', 'manager', 'specialist', 'analyst']):
                        title = line
                        break
            
            if not title:
                logger.debug("Could not extract job title")
                return None
            
            # Extract company name
            company_selectors = [
                '[class*="company"]',
                '[class*="employer"]',
                '[class*="organization"]',
                'span[class*="company"]',
                'div[class*="company"]',
                'a[class*="company"]'
            ]
            
            company = None
            for selector in company_selectors:
                company = await browser_manager.get_element_text(job_element, selector)
                if company and len(company.strip()) > 1:
                    break
            
            # If no company found, try to extract from text
            if not company:
                lines = element_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 1 and not any(keyword in line.lower() for keyword in ['engineer', 'developer', 'manager', 'lagos', 'remote', 'full-time', 'part-time']):
                        # This might be a company name
                        company = line
                        break
            
            if not company:
                company = "Unknown Company"
            
            # Extract location
            location_selectors = [
                '[class*="location"]',
                '[class*="address"]',
                '[class*="place"]',
                'span[class*="location"]',
                'div[class*="location"]'
            ]
            
            location = None
            for selector in location_selectors:
                location = await browser_manager.get_element_text(job_element, selector)
                if location and len(location.strip()) > 1:
                    break
            
            # If no location found, try to extract from text
            if not location:
                lines = element_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and any(keyword in line.lower() for keyword in ['lagos', 'remote', 'nigeria', 'abuja', 'kano']):
                        location = line
                        break
            
            if not location:
                location = "Unknown Location"
            
            # Extract job URL
            url_selectors = [
                'a[href]',
                '[class*="link"] a',
                '[class*="title"] a',
                'a[class*="apply"]',
                'a[class*="job"]'
            ]
            
            url = None
            for selector in url_selectors:
                url = await browser_manager.get_element_attribute(job_element, selector, 'href')
                if url:
                    # Ensure it's a valid job URL
                    if any(domain in url for domain in ['google.com', 'jobs', 'indeed', 'linkedin']):
                        break
                    else:
                        url = None
            
            # Extract job description (if available)
            description_selectors = [
                '[class*="description"]',
                '[class*="summary"]',
                '[class*="snippet"]',
                'p',
                'div[class*="details"]',
                'span[class*="description"]'
            ]
            
            description = None
            for selector in description_selectors:
                description = await browser_manager.get_element_text(job_element, selector)
                if description and len(description.strip()) > 20:  # Ensure meaningful description
                    break
            
            # Extract posting date
            date_selectors = [
                '[class*="date"]',
                '[class*="time"]',
                '[class*="posted"]',
                'span[class*="date"]',
                'div[class*="date"]',
                'span[class*="time"]'
            ]
            
            date_posted = None
            for selector in date_selectors:
                date_posted = await browser_manager.get_element_text(job_element, selector)
                if date_posted and any(keyword in date_posted.lower() for keyword in ['ago', 'day', 'hour', 'week']):
                    break
            
            # Create JobPosting object
            job_posting = JobPosting(
                title=title.strip(),
                company=company.strip(),
                location=location.strip(),
                url=url,
                description=description.strip() if description else None,
                date_posted=date_posted.strip() if date_posted else None
            )
            
            logger.info(f"Successfully extracted job: {title} at {company} in {location}")
            return job_posting
            
        except Exception as e:
            logger.debug(f"Error extracting single job: {str(e)}")
            return None
            
    async def _extract_job_with_details(self, job_element, browser_manager: BrowserManager, job_index: int) -> Optional[JobPosting]:
        """
        Extract job details by clicking on the job listing to open the detail panel
        
        Args:
            job_element: WebElement representing a job listing
            browser_manager: Browser manager instance
            job_index: Index of the job being processed
            
        Returns:
            JobPosting object or None if extraction fails
        """
        try:
            logger.info(f"Clicking on job {job_index} to get details")
            
            # Try to click on the job element with better error handling
            try:
                # Scroll the element into view first
                browser_manager.driver.execute_script("arguments[0].scrollIntoView(true);", job_element)
                await asyncio.sleep(1)
                
                # Try to click using JavaScript if regular click fails
                try:
                    job_element.click()
                except Exception as click_error:
                    logger.warning(f"Regular click failed for job {job_index}, trying JavaScript click")
                    browser_manager.driver.execute_script("arguments[0].click();", job_element)
                
            except Exception as e:
                logger.warning(f"Could not click on job {job_index}: {str(e)}")
                return None
            
            # Wait for the job details panel to load
            await asyncio.sleep(3)
            
            # Try to close any overlays or popups that might interfere
            try:
                close_selectors = [
                    'button[aria-label*="Close"]',
                    'button[class*="close"]',
                    'div[class*="close"]',
                    'button[jsname*="close"]'
                ]
                
                for close_selector in close_selectors:
                    try:
                        close_elements = browser_manager.driver.find_elements(By.CSS_SELECTOR, close_selector)
                        for close_element in close_elements:
                            if close_element.is_displayed():
                                close_element.click()
                                await asyncio.sleep(1)
                                break
                    except:
                        continue
            except:
                pass
            
            # Wait for the job details to appear
            detail_selectors = [
                'c-wiz[data-title]',  # Main job detail container
                'div[class*="JmvMcb"]',  # Job details container
                'div[class*="detail"]',  # Detail container
                'div[role="dialog"]'  # Dialog role
            ]
            
            detail_element = None
            for selector in detail_selectors:
                try:
                    elements = browser_manager.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        detail_element = elements[0]
                        logger.info(f"Found job details using selector: {selector}")
                        break
                except:
                    continue
            
            if not detail_element:
                logger.warning(f"Could not find job details for job {job_index}")
                return None
            
            # Debug: Log the detail element content
            try:
                detail_text = detail_element.text[:500]  # First 500 chars
                logger.debug(f"Detail element text for job {job_index}: {detail_text}...")
            except:
                pass
            
            # Extract job title from the detail panel
            title_selectors = [
                'h1[class*="LZAQDf"]',  # Main job title
                'h1[class*="cS4Vcb-pGL6qe-IRrXtf"]',  # Alternative title class
                'h1[class*="title"]',
                'h1',
                'div[class*="title"] h1',
                'span[class*="title"]',
                'div[data-title]'  # Data attribute
            ]
            
            title = None
            for selector in title_selectors:
                try:
                    title_element = detail_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    if title and len(title) > 3:
                        break
                except:
                    continue
            
            # If still no title, try to get it from the data attribute
            if not title:
                try:
                    title = detail_element.get_attribute('data-title')
                    if title and len(title.strip()) > 3:
                        title = title.strip()
                except:
                    pass
            
            if not title:
                logger.warning(f"Could not extract title for job {job_index}")
                return None
            
            # Extract company name
            company_selectors = [
                'div[class*="BK5CCe"] div',  # Company name in detail panel
                'div[class*="UxTHrf"]',  # Company name class
                'div[class*="company"]',
                'span[class*="company"]',
                'div[class*="employer"]',
                'div[class*="organization"]'
            ]
            
            company = None
            for selector in company_selectors:
                try:
                    company_element = detail_element.find_element(By.CSS_SELECTOR, selector)
                    company = company_element.text.strip()
                    if company and len(company) > 1:
                        break
                except:
                    continue
            
            if not company:
                company = "Unknown Company"
            
            # Extract location
            location_selectors = [
                'div[class*="waQ7qe"]',  # Location in detail panel
                'div[class*="cS4Vcb-pGL6qe-ysgGef"]',  # Alternative location class
                'div[class*="location"]',
                'span[class*="location"]'
            ]
            
            location = None
            for selector in location_selectors:
                try:
                    location_element = detail_element.find_element(By.CSS_SELECTOR, selector)
                    location_text = location_element.text.strip()
                    # Extract location from text like "EventPark • Lagos • via Indeed"
                    if '•' in location_text:
                        parts = location_text.split('•')
                        if len(parts) >= 2:
                            location = parts[1].strip()
                    else:
                        location = location_text
                    if location and len(location) > 1:
                        break
                except:
                    continue
            
            if not location:
                location = "Unknown Location"
            
            # Extract job URL from apply buttons
            url_selectors = [
                'a[class*="Ueh9jd"]',  # Apply button
                'a[href*="indeed"]',
                'a[href*="linkedin"]',
                'a[href*="jobs"]'
            ]
            
            url = None
            for selector in url_selectors:
                try:
                    url_elements = detail_element.find_elements(By.CSS_SELECTOR, selector)
                    for url_element in url_elements:
                        href = url_element.get_attribute('href')
                        if href and any(domain in href for domain in ['indeed', 'linkedin', 'jobs']):
                            url = href
                            break
                    if url:
                        break
                except:
                    continue
            
            # Extract job description
            description_selectors = [
                'span[jsname="QAWWu"]',  # Job description text
                'div[class*="description"]',
                'div[class*="summary"]',
                'span[class*="description"]'
            ]
            
            description = None
            for selector in description_selectors:
                try:
                    desc_element = detail_element.find_element(By.CSS_SELECTOR, selector)
                    description = desc_element.text.strip()
                    if description and len(description) > 20:
                        break
                except:
                    continue
            
            # Extract posting date
            date_selectors = [
                'span[class*="RcZtZb"]',  # Date posted
                'div[class*="nYym1e"] span',
                'span[class*="date"]'
            ]
            
            date_posted = None
            for selector in date_selectors:
                try:
                    date_elements = detail_element.find_elements(By.CSS_SELECTOR, selector)
                    for date_element in date_elements:
                        date_text = date_element.text.strip()
                        if date_text and any(keyword in date_text.lower() for keyword in ['ago', 'day', 'hour', 'week']):
                            date_posted = date_text
                            break
                    if date_posted:
                        break
                except:
                    continue
            
            # Create JobPosting object
            job_posting = JobPosting(
                title=title.strip(),
                company=company.strip(),
                location=location.strip(),
                url=url,
                description=description.strip() if description else None,
                date_posted=date_posted.strip() if date_posted else None
            )
            
            logger.info(f"Successfully extracted job details: {title} at {company} in {location}")
            return job_posting
            
        except Exception as e:
            logger.error(f"Error extracting job details for job {job_index}: {str(e)}")
            return None
            
    async def _extract_job_from_card(self, job_element, browser_manager: BrowserManager, job_index: int) -> Optional[JobPosting]:
        """
        Extract job data directly from the job card without clicking
        
        Args:
            job_element: WebElement representing a job card
            browser_manager: Browser manager instance
            job_index: Index of the job being processed
            
        Returns:
            JobPosting object or None if extraction fails
        """
        try:
            logger.info(f"Extracting job {job_index} from card")
            
            # Extract job title
            title_selectors = [
                'div[class="tNxQIb PUpOsf"]',  # Job title class
                'div[class*="tNxQIb"]',  # Alternative title class
                'div[class*="PUpOsf"]',  # Another title class
                'div[class*="title"]',
                'h3',
                'h2'
            ]
            
            title = None
            for selector in title_selectors:
                try:
                    title_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    if title and len(title) > 3:
                        break
                except:
                    continue
            
            if not title:
                logger.warning(f"Could not extract title for job {job_index}")
                return None
            
            # Extract company name
            company_selectors = [
                'div[class="wHYlTd MKCbgd a3jPc"]',  # Company class
                'div[class*="wHYlTd"]',  # Alternative company class
                'div[class*="MKCbgd"]',  # Another company class
                'div[class*="company"]',
                'span[class*="company"]'
            ]
            
            company = None
            for selector in company_selectors:
                try:
                    company_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    company = company_element.text.strip()
                    if company and len(company) > 1:
                        break
                except:
                    continue
            
            if not company:
                company = "Unknown Company"
            
            # Extract location
            location_selectors = [
                'div[class="wHYlTd FqK3wc MKCbgd"]',  # Location class
                'div[class*="FqK3wc"]',  # Alternative location class
                'div[class*="location"]',
                'span[class*="location"]'
            ]
            
            location = None
            for selector in location_selectors:
                try:
                    location_element = job_element.find_element(By.CSS_SELECTOR, selector)
                    location_text = location_element.text.strip()
                    # Extract location from text like "Lagos • via Indeed"
                    if '•' in location_text:
                        parts = location_text.split('•')
                        if len(parts) >= 1:
                            location = parts[0].strip()
                    else:
                        location = location_text
                    if location and len(location) > 1:
                        break
                except:
                    continue
            
            if not location:
                location = "Unknown Location"
            
            # Extract job URL
            url = None
            try:
                # Get the href from the job card link
                url = job_element.get_attribute('href')
                if not url:
                    # Try to find a link within the card
                    link_elements = job_element.find_elements(By.CSS_SELECTOR, 'a[href]')
                    for link in link_elements:
                        href = link.get_attribute('href')
                        if href and any(domain in href for domain in ['google.com', 'jobs', 'indeed', 'linkedin']):
                            url = href
                            break
            except:
                pass
            
            # Extract posting date
            date_selectors = [
                'span[class="Yf9oye"]',  # Date class
                'span[class*="Yf9oye"]',  # Alternative date class
                'div[class*="K3eUK"] span',  # Date in time section
                'span[class*="date"]',
                'span[class*="time"]'
            ]
            
            date_posted = None
            for selector in date_selectors:
                try:
                    date_elements = job_element.find_elements(By.CSS_SELECTOR, selector)
                    for date_element in date_elements:
                        date_text = date_element.text.strip()
                        if date_text and any(keyword in date_text.lower() for keyword in ['ago', 'day', 'hour', 'week']):
                            date_posted = date_text
                            break
                    if date_posted:
                        break
                except:
                    continue
            
            # Extract job description (limited from card)
            description = None
            try:
                # Job cards usually don't have full descriptions, but we can try to get a snippet
                desc_selectors = [
                    'div[class*="description"]',
                    'div[class*="summary"]',
                    'p',
                    'span[class*="snippet"]'
                ]
                
                for selector in desc_selectors:
                    try:
                        desc_element = job_element.find_element(By.CSS_SELECTOR, selector)
                        description = desc_element.text.strip()
                        if description and len(description) > 10:
                            break
                    except:
                        continue
            except:
                pass
            
            # Create JobPosting object
            job_posting = JobPosting(
                title=title.strip(),
                company=company.strip(),
                location=location.strip(),
                url=url,
                description=description.strip() if description else None,
                date_posted=date_posted.strip() if date_posted else None
            )
            
            logger.info(f"Successfully extracted job from card: {title} at {company} in {location}")
            return job_posting
            
        except Exception as e:
            logger.error(f"Error extracting job from card {job_index}: {str(e)}")
            return None
            
    async def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text content
        
        Args:
            text: Raw text content
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted characters
        cleaned = re.sub(r'[^\w\s\-.,!?()]', '', cleaned)
        
        return cleaned
