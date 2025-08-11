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
                # Avoid fixed remote debugging port to allow concurrent Chromium instances
                # '--remote-debugging-port=9222'
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

            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );

            // Override user agent
            Object.defineProperty(navigator, 'userAgent', {
                get: () => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            });
        """)

        return playwright

    async def scrape_jobs_basic(self, job_title: str, location: str, max_jobs: int = 5) -> List[JobPosting]:
        """
        Quickly collect job cards without visiting detail pages. More resilient under login walls.
        Populates basic fields and the card link so we can do contact recon in bulk later.
        """
        playwright = None
        try:
            logger.info(
                f"Starting basic LinkedIn scrape for: {job_title} in {location}")
            playwright = await self.setup_browser()

            search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}"

            # Load results with retries
            for attempt in range(3):
                try:
                    await self.page.goto(search_url, wait_until='domcontentloaded')
                    try:
                        await self.page.wait_for_selector('.base-card, .job-search-card', timeout=20000)
                    except Exception:
                        pass

                    # Attempt to dismiss login prompts
                    for sel in [
                        'button:has-text("Skip")',
                        'a:has-text("Skip")',
                        'button:has-text("Continue without signing in")',
                        'a:has-text("Continue without signing in")',
                    ]:
                        try:
                            el = await self.page.query_selector(sel)
                            if el and await el.is_visible():
                                await el.click()
                                await asyncio.sleep(1.5)
                        except Exception:
                            continue

                    # If cards exist, continue
                    count = await self.page.locator('.base-card, .job-search-card').count()
                    if count > 0:
                        break
                except Exception as e:
                    logger.warning(
                        f"Basic load attempt {attempt+1} failed: {e}")
                    if attempt < 2:
                        await asyncio.sleep(3)

            # Scroll/load to collect enough cards (roughly 25 per page)
            for _ in range(max(2, (max_jobs + 24) // 25)):
                try:
                    await self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(2)
                except Exception:
                    break

            jobs: List[JobPosting] = []
            job_cards = await self.page.query_selector_all('.base-card, .job-search-card')
            logger.info(f"[basic] Found {len(job_cards)} cards")

            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    title_el = await card.query_selector('h3.base-search-card__title, .job-search-card__title, h3')
                    company_el = await card.query_selector('h4.base-search-card__subtitle, .job-search-card__subtitle, h4')
                    location_el = await card.query_selector('.job-search-card__location')
                    link_el = await card.query_selector('a.base-card__full-link, a[href*="/jobs/view/"]')
                    date_el = await card.query_selector('time, .job-search-card__listdate')

                    if not title_el or not company_el:
                        continue

                    title = (await title_el.inner_text()).strip()
                    company = (await company_el.inner_text()).strip()
                    location_text = (await location_el.inner_text()).strip() if location_el else ''
                    apply_link = await link_el.get_attribute('href') if link_el else ''
                    date_posted = ''
                    if date_el:
                        date_posted = (await date_el.get_attribute('datetime')) or (await date_el.inner_text()) or ''
                        date_posted = date_posted.strip()

                    jobs.append(JobPosting(
                        title=title,
                        company=company,
                        location=location_text,
                        url=apply_link or '',
                        description='',
                        poster_name='',
                        poster_position='',
                        email='',
                        date_posted=date_posted,
                    ))
                except Exception as e:
                    logger.debug(f"[basic] Error processing card {i+1}: {e}")
                    continue

            logger.info(f"[basic] Returning {len(jobs)} jobs")
            return jobs
        except Exception as e:
            logger.error(f"Error in scrape_jobs_basic: {e}")
            return []
        finally:
            try:
                if self.browser:
                    await self.browser.close()
                if playwright:
                    await playwright.stop()
            except Exception:
                pass

    async def enrich_job_descriptions(self, jobs: List[JobPosting], limit: int | None = None) -> None:
        """Visit job URLs to extract real job descriptions for a subset of jobs.
        Does not change any other fields.
        """
        if not jobs:
            return
        max_to_enrich = len(jobs) if limit is None else max(0, min(limit, len(jobs)))
        if max_to_enrich == 0:
            return

        playwright = None
        try:
            playwright = await self.setup_browser()
            for job in jobs[:max_to_enrich]:
                if not job.url:
                    continue
                try:
                    await self.page.goto(job.url, wait_until='domcontentloaded')
                    try:
                        await self.page.wait_for_load_state('networkidle', timeout=15000)
                    except Exception:
                        pass
                    await asyncio.sleep(2)

                    # Try to extract description using the robust selector set
                    description_selectors = [
                        '.description__text--rich',
                        '.job-description',
                        '.jobs-description__content',
                        '.jobs-box__html-content',
                        '[data-job-description]',
                        '.jobs-description-content__text',
                        '.jobs-description__content--rich',
                        '.jobs-description__content'
                    ]
                    description_text = ''
                    for selector in description_selectors:
                        element = await self.page.query_selector(selector)
                        if element:
                            description_text = (await element.inner_text() or '').strip()
                            if description_text:
                                break
                    # Only overwrite if we got something meaningful
                    if description_text and len(description_text) > 80:
                        job.description = description_text
                except Exception:
                    continue
        finally:
            try:
                if self.browser:
                    await self.browser.close()
                if playwright:
                    await playwright.stop()
            except Exception:
                pass

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

            if not job_cards:
                # Try more selectors
                job_cards = await self.page.query_selector_all('.base-card')

            logger.info(
                f"Found {len(job_cards)} job cards with fallback method")

            jobs = []
            for i, job_card in enumerate(job_cards[:max_jobs]):
                try:
                    logger.info(
                        f"Processing job card {i+1}/{len(job_cards[:max_jobs])}")

                    # Extract basic information with better error handling
                    try:
                        title_element = await job_card.query_selector('h3, .job-search-card__title, .base-search-card__title')
                        if not title_element:
                            logger.debug(
                                f"No title element found for job {i+1}")
                            continue
                        job_title = await title_element.inner_text()
                        if not job_title.strip():
                            logger.debug(f"Empty title for job {i+1}")
                            continue
                        logger.info(f"Found job title: {job_title}")
                    except Exception as e:
                        logger.debug(
                            f"Error extracting title for job {i+1}: {str(e)}")
                        continue

                    try:
                        company_element = await job_card.query_selector('h4, .job-search-card__subtitle, .base-search-card__subtitle')
                        company = await company_element.inner_text() if company_element else "Unknown Company"
                        logger.info(f"Found company: {company}")
                    except Exception as e:
                        logger.debug(
                            f"Error extracting company for job {i+1}: {str(e)}")
                        company = "Unknown Company"

                    try:
                        location_element = await job_card.query_selector('.job-search-card__location, .job-search-card__location')
                        location = await location_element.inner_text() if location_element else "Unknown Location"
                        logger.info(f"Found location: {location}")
                    except Exception as e:
                        logger.debug(
                            f"Error extracting location for job {i+1}: {str(e)}")
                        location = "Unknown Location"

                    try:
                        link_element = await job_card.query_selector('a[href*="/jobs/view/"]')
                        apply_link = await link_element.get_attribute('href') if link_element else ""
                        logger.info(f"Found apply link: {apply_link}")
                    except Exception as e:
                        logger.debug(
                            f"Error extracting link for job {i+1}: {str(e)}")
                        apply_link = ""

                        # Navigate to job details to get more information
                        job_description = ""
                        poster_name = ""
                        poster_position = ""
                        email = ""
                        date_posted = ""

                        if apply_link:
                            try:
                                # Navigate to job details page with better retry logic
                                max_detail_retries = 3
                                detail_page_loaded = False

                                for detail_attempt in range(max_detail_retries):
                                    try:
                                        await self.page.goto(apply_link, wait_until='domcontentloaded')
                                        await self.page.wait_for_load_state('networkidle', timeout=15000)
                                        # Wait for dynamic content to load
                                        await asyncio.sleep(3)

                                        # Check if page loaded properly
                                        page_content = await self.page.content()
                                        if 'job' in page_content.lower() and len(page_content) > 1000:
                                            detail_page_loaded = True
                                            break
                                        else:
                                            logger.warning(
                                                f"Job details page seems incomplete, retrying... (attempt {detail_attempt + 1})")
                                            await asyncio.sleep(3)
                                    except Exception as e:
                                        logger.warning(
                                            f"Error loading job details page (attempt {detail_attempt + 1}): {str(e)}")
                                        if detail_attempt < max_detail_retries - 1:
                                            await asyncio.sleep(3)

                                if not detail_page_loaded:
                                    logger.warning(
                                        f"Could not load job details page for {job_title}, using basic info only")

                                # Try to extract description with better error handling and more selectors
                                try:
                                    desc_selectors = [
                                        '.description__text--rich',
                                        '.job-description',
                                        '.jobs-description__content',
                                        '.jobs-box__html-content',
                                        '[data-job-description]',
                                        '.jobs-description-content__text',
                                        '.jobs-description__content--rich',
                                        '.jobs-box__html-content',
                                        '.jobs-description__content'
                                    ]
                                    for selector in desc_selectors:
                                        desc_element = await self.page.query_selector(selector)
                                        if desc_element:
                                            job_description = await desc_element.inner_text()
                                            if job_description.strip():
                                                break

                                    # If still no description, try to get it from the page content
                                    if not job_description.strip():
                                        # Look for job description in the page content
                                        page_text = await self.page.inner_text('body')
                                        # Try to find description between common markers
                                        desc_patterns = [
                                            r'About the role(.*?)(?=Requirements|Qualifications|Skills|Benefits|Apply|$)',
                                            r'Job Description(.*?)(?=Requirements|Qualifications|Skills|Benefits|Apply|$)',
                                            r'About this role(.*?)(?=Requirements|Qualifications|Skills|Benefits|Apply|$)',
                                            r'Position Overview(.*?)(?=Requirements|Qualifications|Skills|Benefits|Apply|$)'
                                        ]

                                        for pattern in desc_patterns:
                                            match = re.search(
                                                pattern, page_text, re.IGNORECASE | re.DOTALL)
                                            if match:
                                                job_description = match.group(
                                                    1).strip()
                                                # Only use if it's substantial
                                                if len(job_description) > 100:
                                                    break
                                except Exception as e:
                                    logger.debug(
                                        f"Error extracting description: {str(e)}")
                                    job_description = ""

                                # Try to extract poster info with better error handling
                                try:
                                    poster_selectors = [
                                        '.jobs-poster__name',
                                        '.jobs-unified-top-card__job-insight',
                                        '.jobs-poster__title',
                                        '.jobs-unified-top-card__subtitle'
                                    ]
                                    for selector in poster_selectors:
                                        poster_element = await self.page.query_selector(selector)
                                        if poster_element:
                                            poster_text = await poster_element.inner_text()
                                            if "Posted by" in poster_text:
                                                # Extract name after "Posted by"
                                                posted_match = re.search(
                                                    r'Posted by\s+(.+?)(?:\s+•|\s*$)', poster_text, re.IGNORECASE)
                                                if posted_match:
                                                    poster_name = posted_match.group(
                                                        1).strip()
                                                else:
                                                    poster_name = poster_text.replace(
                                                        "Posted by", "").strip()
                                                break
                                            elif poster_text.strip() and poster_text.strip() != job_title:
                                                # This might be a position or name
                                                if not poster_position:
                                                    poster_position = poster_text.strip()
                                                else:
                                                    poster_name = poster_text.strip()
                                                break
                                except Exception as e:
                                    logger.debug(
                                        f"Error extracting poster info: {str(e)}")

                                # Try to extract email from description and page content with better patterns
                                try:
                                    email_patterns = [
                                        # Standard email
                                        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                                        # Email with spaces
                                        r'[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Z|a-z]{2,}',
                                        # Obfuscated email
                                        r'[A-Za-z0-9._%+-]+\s*\[at\]\s*[A-Za-z0-9.-]+\s*\[dot\]\s*[A-Z|a-z]{2,}',
                                        # Another obfuscated format
                                        r'[A-Za-z0-9._%+-]+\s*\(at\)\s*[A-Za-z0-9.-]+\s*\(dot\)\s*[A-Z|a-z]{2,}'
                                    ]

                                    # First try from job description
                                    if job_description:
                                        for pattern in email_patterns:
                                            email_matches = re.findall(
                                                pattern, job_description, re.IGNORECASE)
                                            if email_matches:
                                                # Clean up the email (remove spaces, convert obfuscated formats)
                                                raw_email = email_matches[0]
                                                clean_email = raw_email.replace(' ', '').replace(
                                                    '[at]', '@').replace('[dot]', '.').replace('(at)', '@').replace('(dot)', '.')

                                                # Validate it's a proper email and filter out spam
                                                if re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', clean_email):
                                                    if not any(x in clean_email.lower() for x in ['example', 'test', 'noreply', 'no-reply', 'linkedin', 'support']):
                                                        email = clean_email
                                                        break

                                    # If no email found in description, search the entire page
                                    if not email:
                                        page_content = await self.page.content()
                                        for pattern in email_patterns:
                                            email_matches = re.findall(
                                                pattern, page_content, re.IGNORECASE)
                                            if email_matches:
                                                # Filter out common false positives
                                                filtered_emails = [e for e in email_matches if not any(x in e.lower(
                                                ) for x in ['example', 'test', 'noreply', 'no-reply', 'linkedin', 'support'])]
                                                if filtered_emails:
                                                    raw_email = filtered_emails[0]
                                                    clean_email = raw_email.replace(' ', '').replace(
                                                        '[at]', '@').replace('[dot]', '.').replace('(at)', '@').replace('(dot)', '.')
                                                    if re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', clean_email):
                                                        email = clean_email
                                                        break
                                except Exception as e:
                                    logger.debug(
                                        f"Error extracting email: {str(e)}")

                                # Try to extract date with better error handling
                                try:
                                    date_selectors = [
                                        'time[datetime]',
                                        '.jobs-unified-top-card__job-insight time',
                                        '.job-details-jobs-unified-top-card__job-insight time',
                                        '.jobs-unified-top-card__job-insight',
                                        '.job-details-jobs-unified-top-card__job-insight'
                                    ]

                                    for selector in date_selectors:
                                        date_element = await self.page.query_selector(selector)
                                        if date_element:
                                            # Try to get datetime attribute first
                                            date_posted = await date_element.get_attribute('datetime')
                                            if not date_posted:
                                                # Fallback to text content
                                                date_text = await date_element.inner_text()
                                                if date_text and any(word in date_text.lower() for word in ['ago', 'day', 'week', 'month', 'year']):
                                                    date_posted = date_text.strip()
                                                    break
                                            else:
                                                break
                                except Exception as e:
                                    logger.debug(
                                        f"Error extracting date: {str(e)}")

                                # Try to get updated apply link
                                try:
                                    # Method 1: Look for apply button
                                    apply_selectors = [
                                        'a.jobs-apply-button',
                                        'button.jobs-apply-button',
                                        'a[data-control-name="jobdetails_topcard_inapply"]',
                                        'a[href*="apply"]',
                                        '.jobs-apply-button--top-card'
                                    ]

                                    for selector in apply_selectors:
                                        apply_button = await self.page.query_selector(selector)
                                        if apply_button:
                                            new_apply_link = await apply_button.get_attribute('href')
                                            if new_apply_link and new_apply_link.startswith('http'):
                                                apply_link = new_apply_link
                                                break

                                    # Method 2: Look for external apply link
                                    if not apply_link.startswith('http'):
                                        external_apply = await self.page.query_selector('a[href*="external"]')
                                        if external_apply:
                                            external_link = await external_apply.get_attribute('href')
                                            if external_link:
                                                apply_link = external_link
                                except Exception as e:
                                    logger.debug(
                                        f"Error extracting apply link: {str(e)}")

                            except Exception as e:
                                logger.debug(
                                    f"Error extracting details from job page: {str(e)}")

                        # Create job posting
                        job_posting = JobPosting(
                            title=job_title.strip(),
                            company=company.strip(),
                            location=location.strip(),
                            url=apply_link,
                            description=job_description.strip(),
                            poster_name=poster_name.strip(),
                            poster_position=poster_position.strip(),
                            email=email.strip(),
                            date_posted=date_posted.strip()
                        )

                        jobs.append(job_posting)
                        logger.info(
                            f'Scraped "{job_title}" at {company} in {location}...')

                        # Add delay between jobs to avoid overwhelming the page
                        # Don't delay after the last job
                        if i < len(job_cards[:max_jobs]) - 1:
                            await asyncio.sleep(random.uniform(2, 4))

                except Exception as e:
                    logger.warning(
                        f"Error processing job {i+1} in fallback: {str(e)}")
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
            logger.info(
                f"Starting LinkedIn scrape for: {job_title} in {location}")

            # Setup browser
            playwright = await self.setup_browser()

            # Navigate to LinkedIn jobs search with retry logic
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}"

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(
                        f"Attempting to load LinkedIn (attempt {attempt + 1}/{max_retries})")

                    # Navigate to the page
                    await self.page.goto(search_url, wait_until='domcontentloaded')

                    # Wait for page to load with different strategies
                    try:
                        await self.page.wait_for_load_state('networkidle', timeout=30000)
                    except:
                        # If networkidle fails, wait for specific elements
                        await self.page.wait_for_selector('.base-card', timeout=30000)

                    # Check if we hit a login wall
                    login_wall = await self.page.query_selector('input[name="session_key"]')
                    if login_wall:
                        logger.warning(
                            "LinkedIn login wall detected, trying to bypass...")
                        # Try multiple strategies to bypass login wall
                        try:
                            # Strategy 1: Try to click "Skip" or "Continue without signing in"
                            skip_selectors = [
                                'button:has-text("Skip")',
                                'a:has-text("Skip")',
                                'button:has-text("Continue")',
                                'button:has-text("Continue without signing in")',
                                'a:has-text("Continue without signing in")',
                                'button:has-text("Skip for now")',
                                'a:has-text("Skip for now")'
                            ]

                            for selector in skip_selectors:
                                try:
                                    skip_button = await self.page.query_selector(selector)
                                    if skip_button and await skip_button.is_visible():
                                        await skip_button.click()
                                        await asyncio.sleep(3)
                                        logger.info(
                                            "Successfully clicked skip button")
                                        break
                                except:
                                    continue

                            # Strategy 2: Try to navigate directly to jobs search
                            if not await self.page.query_selector('.base-card'):
                                logger.info("Trying direct jobs URL...")
                                direct_jobs_url = f"https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}&f_TPR=r86400"
                                await self.page.goto(direct_jobs_url, wait_until='domcontentloaded')
                                await asyncio.sleep(3)

                        except Exception as e:
                            logger.warning(
                                f"Error bypassing login wall: {str(e)}")

                    # Check if page loaded successfully
                    page_title = await self.page.title()
                    if 'LinkedIn' in page_title or 'Jobs' in page_title:
                        logger.info("LinkedIn page loaded successfully")
                        break
                    else:
                        raise Exception(
                            "Page title doesn't match expected LinkedIn page")

                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        # Try fallback method
                        logger.info("Main method failed, trying fallback...")
                        return await self.scrape_jobs_fallback(job_title, location, max_jobs)

                    # Wait before retry
                    await asyncio.sleep(5)

            # Scroll and load more jobs
            # Minimum 2 pages for better results
            pages = max(2, (max_jobs + 24) // 25)

            for i in range(pages):
                logger.info(f"Loading page {i+1}...")

                # Scroll to bottom to load more jobs
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(random.uniform(2, 4))

                # Try to click "Show more" button if available
                try:
                    show_more_button = self.page.locator(
                        'button:has-text("Show more")')
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

                    # Navigate to job details page with retry logic
                    max_detail_retries = 2
                    detail_page_loaded = False

                    for detail_attempt in range(max_detail_retries):
                        try:
                            await self.page.goto(apply_link, wait_until='domcontentloaded')
                            await self.page.wait_for_load_state('networkidle', timeout=15000)
                            # Wait for dynamic content to load
                            await asyncio.sleep(2)

                            # Check if page loaded properly
                            page_content = await self.page.content()
                            if 'job' in page_content.lower() and len(page_content) > 1000:
                                detail_page_loaded = True
                                break
                            else:
                                logger.warning(
                                    f"Job details page seems incomplete, retrying... (attempt {detail_attempt + 1})")
                                await asyncio.sleep(3)
                        except Exception as e:
                            logger.warning(
                                f"Error loading job details page (attempt {detail_attempt + 1}): {str(e)}")
                            if detail_attempt < max_detail_retries - 1:
                                await asyncio.sleep(3)

                    if not detail_page_loaded:
                        logger.warning(
                            f"Could not load job details page for {job_title}, using basic info only")

                    # Extract detailed information
                    job_description = ""
                    poster_name = ""
                    poster_position = ""
                    email = ""
                    date_posted = ""

                    # Get job description - try multiple selectors
                    try:
                        description_selectors = [
                            '.description__text--rich',
                            '.job-description',
                            '.jobs-description__content',
                            '.jobs-box__html-content',
                            '[data-job-description]',
                            '.jobs-description-content__text'
                        ]

                        for selector in description_selectors:
                            description_element = await self.page.query_selector(selector)
                        if description_element:
                            job_description = await description_element.inner_text()
                            if job_description.strip():
                                break
                    except Exception as e:
                        logger.debug(f"Error extracting description: {str(e)}")

                    # Get poster information - try multiple approaches
                    try:
                        # Method 1: Look for "Posted by" text
                        poster_selectors = [
                            '.job-details-jobs-unified-top-card__job-insight',
                            '.jobs-unified-top-card__job-insight',
                            '.jobs-unified-top-card__subtitle',
                            '.jobs-unified-top-card__company-name',
                            '.jobs-unified-top-card__primary-description'
                        ]

                        for selector in poster_selectors:
                            poster_element = await self.page.query_selector(selector)
                            if poster_element:
                                poster_text = await poster_element.inner_text()
                            if "Posted by" in poster_text:
                                    # Extract name after "Posted by"
                                    posted_match = re.search(r'Posted by\s+(.+?)(?:\s+•|\s*$)', poster_text, re.IGNORECASE)
                            if posted_match:
                                poster_name = posted_match.group(1).strip()
                                break
                            else:
                                # Fallback: take everything after "Posted by"
                                poster_name = poster_text.replace("Posted by", "").strip()
                                break
                        
                        # Method 2: Look for recruiter/hiring manager information
                        if not poster_name:
                            recruiter_selectors = [
                                '.jobs-poster__name',
                                '.jobs-poster__title',
                                '.jobs-unified-top-card__job-insight a',
                                '.jobs-unified-top-card__subtitle a'
                            ]
                            
                            for selector in recruiter_selectors:
                                recruiter_element = await self.page.query_selector(selector)
                                if recruiter_element:
                                    poster_name = await recruiter_element.inner_text()
                                    if poster_name.strip():
                                        break
                        
                        # Method 2b: Look for poster position separately
                        if not poster_position:
                            position_selectors = [
                                '.jobs-poster__title',
                                '.jobs-poster__position',
                                '.jobs-unified-top-card__job-insight span',
                                '.jobs-unified-top-card__subtitle span'
                            ]
                            
                            for selector in position_selectors:
                                position_element = await self.page.query_selector(selector)
                                if position_element:
                                    position_text = await position_element.inner_text()
                                    if position_text.strip() and position_text.strip() != job_title:
                                        poster_position = position_text.strip()
                                        break
                        
                        # Method 3: Look for contact information section
                        if not poster_name:
                            contact_section = await self.page.query_selector('.jobs-poster')
                            if contact_section:
                                name_element = await contact_section.query_selector('.jobs-poster__name')
                                if name_element:
                                    poster_name = await name_element.inner_text()
                                
                                position_element = await contact_section.query_selector('.jobs-poster__title')
                                if position_element:
                                    poster_position = await position_element.inner_text()
                        
                        # Method 4: Look for hiring manager or recruiter information
                        if not poster_name:
                            hiring_manager_selectors = [
                                '.jobs-unified-top-card__job-insight a[href*="/in/"]',
                                '.jobs-unified-top-card__subtitle a[href*="/in/"]',
                                '.jobs-poster a[href*="/in/"]'
                            ]
                            
                            for selector in hiring_manager_selectors:
                                manager_link = await self.page.query_selector(selector)
                                if manager_link:
                                    poster_name = await manager_link.inner_text()
                                    if poster_name.strip():
                                        break
                        
                        # Method 5: Look for any text that might indicate who posted the job
                        if not poster_name:
                            # Look for patterns like "Posted by [Name]" or "Hiring Manager: [Name]"
                            page_text = await self.page.inner_text('body')
                            poster_patterns = [
                                r'Posted by\s+([A-Za-z\s]+?)(?:\s+•|\s*$)',
                                r'Hiring Manager:\s*([A-Za-z\s]+?)(?:\s+•|\s*$)',
                                r'Recruiter:\s*([A-Za-z\s]+?)(?:\s+•|\s*$)',
                                r'Contact:\s*([A-Za-z\s]+?)(?:\s+•|\s*$)'
                            ]
                            
                            for pattern in poster_patterns:
                                match = re.search(pattern, page_text, re.IGNORECASE)
                                if match:
                                    poster_name = match.group(1).strip()
                                    break
                                    
                    except Exception as e:
                        logger.debug(f"Error extracting poster info: {str(e)}")
                    
                    # Extract email - try multiple sources
                    try:
                        # Method 1: Extract from job description with better patterns
                        if job_description:
                            # Multiple email patterns to catch different formats
                            email_patterns = [
                                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Standard email
                                r'[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Z|a-z]{2,}',  # Email with spaces
                                r'[A-Za-z0-9._%+-]+\s*\[at\]\s*[A-Za-z0-9.-]+\s*\[dot\]\s*[A-Z|a-z]{2,}',  # Obfuscated email
                                r'[A-Za-z0-9._%+-]+\s*\(at\)\s*[A-Za-z0-9.-]+\s*\(dot\)\s*[A-Z|a-z]{2,}'  # Another obfuscated format
                            ]
                            
                            for pattern in email_patterns:
                                email_matches = re.findall(pattern, job_description, re.IGNORECASE)
                                if email_matches:
                                    # Clean up the email (remove spaces, convert obfuscated formats)
                                    raw_email = email_matches[0]
                                    clean_email = raw_email.replace(' ', '').replace('[at]', '@').replace('[dot]', '.').replace('(at)', '@').replace('(dot)', '.')
                                    
                                    # Validate it's a proper email
                                    if re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', clean_email):
                                        email = clean_email
                                        break
                        
                        # Method 2: Look for contact information section
                        if not email:
                            contact_section = await self.page.query_selector('.jobs-poster')
                            if contact_section:
                                contact_text = await contact_section.inner_text()
                                email_matches = re.findall(email_pattern, contact_text)
                                if email_matches:
                                    email = email_matches[0]
                        
                        # Method 3: Look for contact information in specific sections
                        if not email:
                            contact_sections = [
                                '.jobs-poster',
                                '.jobs-unified-top-card__job-insight',
                                '.jobs-unified-top-card__subtitle',
                                '.jobs-unified-top-card__primary-description'
                            ]
                            
                            for section_selector in contact_sections:
                                section = await self.page.query_selector(section_selector)
                                if section:
                                    section_text = await section.inner_text()
                                    email_matches = re.findall(email_pattern, section_text)
                                    if email_matches:
                                        # Filter out common false positives
                                        filtered_emails = [e for e in email_matches if not any(x in e.lower() for x in ['example', 'test', 'noreply', 'no-reply', 'linkedin'])]
                                        if filtered_emails:
                                            email = filtered_emails[0]
                                            break
                        
                        # Method 4: Look for email in any text content as last resort
                        if not email:
                            page_content = await self.page.content()
                            email_matches = re.findall(email_pattern, page_content)
                            if email_matches:
                                # Filter out common false positives
                                filtered_emails = [e for e in email_matches if not any(x in e.lower() for x in ['example', 'test', 'noreply', 'no-reply', 'linkedin', 'support'])]
                                if filtered_emails:
                                    email = filtered_emails[0]
                                    
                    except Exception as e:
                        logger.debug(f"Error extracting email: {str(e)}")
                    
                    # Get date posted - try multiple selectors
                    try:
                        date_selectors = [
                            'time[datetime]',
                            '.jobs-unified-top-card__job-insight time',
                            '.job-details-jobs-unified-top-card__job-insight time',
                            '.jobs-unified-top-card__job-insight',
                            '.job-details-jobs-unified-top-card__job-insight'
                        ]
                        
                        for selector in date_selectors:
                            date_element = await self.page.query_selector(selector)
                        if date_element:
                                # Try to get datetime attribute first
                            date_posted = await date_element.get_attribute('datetime')
                            if not date_posted:
                                    # Fallback to text content
                                date_text = await date_element.inner_text()
                                if date_text and any(word in date_text.lower() for word in ['ago', 'day', 'week', 'month', 'year']):
                                    date_posted = date_text.strip()
                                # Break out after first matching element
                                break
                                    
                    except Exception as e:
                        logger.debug(f"Error extracting date: {str(e)}")
                    
                    # Get updated apply link - try multiple approaches
                    try:
                        # Method 1: Look for apply button
                        apply_selectors = [
                            'a.jobs-apply-button',
                            'button.jobs-apply-button',
                            'a[data-control-name="jobdetails_topcard_inapply"]',
                            'a[href*="apply"]',
                            '.jobs-apply-button--top-card'
                        ]
                        
                        for selector in apply_selectors:
                            apply_button = await self.page.query_selector(selector)
                            if apply_button:
                                new_apply_link = await apply_button.get_attribute('href')
                            if new_apply_link and new_apply_link.startswith('http'):
                                apply_link = new_apply_link
                            break
                        
                        # Method 2: Look for external apply link
                        if not apply_link.startswith('http'):
                            external_apply = await self.page.query_selector('a[href*="external"]')
                            if external_apply:
                                external_link = await external_apply.get_attribute('href')
                                if external_link:
                                    apply_link = external_link
                                    
                    except Exception as e:
                        logger.debug(f"Error extracting apply link: {str(e)}")
                    
                    # Clean up the extracted data
                    job_description = job_description.strip() if job_description else ""
                    poster_name = poster_name.strip() if poster_name else ""
                    poster_position = poster_position.strip() if poster_position else ""
                    email = email.strip() if email else ""
                    date_posted = date_posted.strip() if date_posted else ""
                    
                    # Log what we found for debugging
                    logger.info(f"Extracted details for {job_title}:")
                    logger.info(f"  - Poster: {poster_name}")
                    logger.info(f"  - Position: {poster_position}")
                    logger.info(f"  - Email: {email}")
                    logger.info(f"  - Date: {date_posted}")
                    logger.info(f"  - Description length: {len(job_description)} chars")
                    logger.info(f"  - Apply link: {apply_link}")
                    
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
                    
                    # Random delay between jobs with longer delays to avoid rate limiting
                    delay = random.uniform(3, 7)
                    logger.info(f"Waiting {delay:.1f} seconds before next job...")
                    await asyncio.sleep(delay)
                    
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
