"""
Enhanced LinkedIn Job Scraper with Company Contact Extraction

This module combines LinkedIn job scraping with company contact information extraction
to provide comprehensive job and contact data.
"""

import asyncio
import logging
from typing import List, Dict, Optional
from models import JobPosting
from scrapers.linkedin_scraper_playwright import LinkedInScraperPlaywright
from scrapers.company_recon_scraper import CompanyReconScraper

logger = logging.getLogger(__name__)

class EnhancedLinkedInScraper:
    """
    Enhanced LinkedIn scraper that also extracts company contact information
    """
    
    def __init__(self):
        """Initialize the enhanced LinkedIn scraper"""
        self.linkedin_scraper = LinkedInScraperPlaywright()
        self.company_scraper = CompanyReconScraper()
        
    async def scrape_jobs_with_contacts(
        self,
        job_title: str,
        location: str,
        max_jobs: int = 5,
        enrich_descriptions: bool = True,
        enrich_limit: int | None = None,
    ) -> List[JobPosting]:
        """
        Scrape jobs from LinkedIn and enhance with company contact information
        
        Args:
            job_title: Job title to search for
            location: Job location
            max_jobs: Maximum number of jobs to scrape
            
        Returns:
            List of enhanced JobPosting objects with contact information
        """
        try:
            logger.info(f"Starting enhanced LinkedIn scrape for: {job_title} in {location}")
            
            # Phase 1: fast scrape to collect job cards
            jobs = await self.linkedin_scraper.scrape_jobs_basic(job_title, location, max_jobs)
            
            if not jobs:
                logger.warning("No jobs found from LinkedIn")
                return []
            
            logger.info(f"Found {len(jobs)} jobs from LinkedIn, running bulk company reconnaissance...")

            # Optional: enrich actual job descriptions from LinkedIn detail pages
            if enrich_descriptions:
                try:
                    await self.linkedin_scraper.enrich_job_descriptions(jobs, limit=enrich_limit)
                except Exception as e:
                    logger.warning(f"Description enrichment failed: {e}")

            # Phase 2: bulk recon concurrently with limited concurrency
            semaphore = asyncio.Semaphore(4)

            async def enhance_one(job: JobPosting) -> JobPosting:
                async with semaphore:
                    try:
                        company_contacts = await self.company_scraper.extract_company_contacts_recon(job.company)
                        return self.enhance_job_with_contacts(job, company_contacts)
                    except Exception as e:
                        logger.warning(f"Recon failed for {job.company}: {e}")
                        return job

            enhanced_jobs = await asyncio.gather(*[enhance_one(job) for job in jobs])

            logger.info(f"Successfully enhanced {len(enhanced_jobs)} jobs with company contacts")
            return list(enhanced_jobs)
            
        except Exception as e:
            logger.error(f"Error in enhanced LinkedIn scraping: {str(e)}")
            raise
    
    def enhance_job_with_contacts(self, job: JobPosting, company_contacts: Dict) -> JobPosting:
        """
        Enhance a job posting with company contact information
        
        Args:
            job: Original job posting
            company_contacts: Company contact information from reconnaissance
            
        Returns:
            Enhanced job posting
        """
        # If we don't have a poster name from LinkedIn, try to find it in company contacts
        if not job.poster_name and company_contacts.get('emails'):
            # Look for hiring manager or HR emails
            hiring_emails = company_contacts.get('hiring_emails', [])
            hr_emails = company_contacts.get('hr_emails', [])
            
            if hiring_emails:
                # Extract name from hiring email (e.g., john.doe@company.com -> John Doe)
                email = hiring_emails[0]
                name_from_email = self.extract_name_from_email(email)
                if name_from_email:
                    job.poster_name = name_from_email
        
        # If we don't have an email from LinkedIn, use company contact emails
        if not job.email and company_contacts.get('emails'):
            # Prioritize hiring/HR emails
            hiring_emails = company_contacts.get('hiring_emails', [])
            hr_emails = company_contacts.get('hr_emails', [])
            
            if hiring_emails:
                job.email = hiring_emails[0]
            elif hr_emails:
                job.email = hr_emails[0]
            else:
                # Use any available email from reconnaissance
                job.email = company_contacts['emails'][0]
        
        # Do not modify job.description with recon data; keep description as the true job description
        
        return job
    
    def extract_name_from_email(self, email: str) -> Optional[str]:
        """
        Extract a person's name from an email address
        
        Args:
            email: Email address
            
        Returns:
            Extracted name or None
        """
        try:
            # Remove domain part
            local_part = email.split('@')[0]
            
            # Handle common patterns
            if '.' in local_part:
                # john.doe@company.com -> John Doe
                parts = local_part.split('.')
                if len(parts) >= 2:
                    return ' '.join(part.capitalize() for part in parts)
            elif '_' in local_part:
                # john_doe@company.com -> John Doe
                parts = local_part.split('_')
                if len(parts) >= 2:
                    return ' '.join(part.capitalize() for part in parts)
            elif '-' in local_part:
                # john-doe@company.com -> John Doe
                parts = local_part.split('-')
                if len(parts) >= 2:
                    return ' '.join(part.capitalize() for part in parts)
            
            # Single word - capitalize it
            return local_part.capitalize()
            
        except:
            return None

# Async wrapper for compatibility
async def scrape_linkedin_jobs_with_contacts(job_title: str, location: str, max_jobs: int = 5) -> List[JobPosting]:
    """
    Async wrapper for enhanced LinkedIn scraping with company contacts
    """
    scraper = EnhancedLinkedInScraper()
    return await scraper.scrape_jobs_with_contacts(job_title, location, max_jobs)
