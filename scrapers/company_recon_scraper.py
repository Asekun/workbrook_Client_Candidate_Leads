"""
Company Reconnaissance Contact Scraper

This module uses reconnaissance techniques to find legitimate company contact information
including DNS lookups, WHOIS data, social media profiles, and targeted web scraping.
"""

import asyncio
import logging
import re
import socket
import whois
import dns.resolver
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)

class CompanyReconScraper:
    """
    Reconnaissance-based scraper for extracting legitimate company contact information
    """
    
    def __init__(self):
        """Initialize the reconnaissance scraper"""
        self.browser = None
        self.page = None
        
    async def setup_browser(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        
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
                #'--remote-debugging-port=9222'
            ]
        )
        
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
        self.page.set_default_timeout(30000)
        
        return playwright
        
    async def extract_company_contacts_recon(self, company_name: str) -> Dict[str, List[str]]:
        """
        Extract company contact information using reconnaissance techniques
        
        Args:
            company_name: Name of the company
            
        Returns:
            Dictionary with contact information
        """
        playwright = None
        try:
            logger.info(f"Starting reconnaissance for company: {company_name}")
            
            # Setup browser
            playwright = await self.setup_browser()
            
            contacts = {
                'emails': [],
                'phone_numbers': [],
                'domains': [],
                'social_media': [],
                'contact_pages': [],
                'hiring_emails': [],
                'hr_emails': [],
                'contact_emails': []
            }
            
            # Step 1: DNS and Domain Reconnaissance
            logger.info("Step 1: DNS and Domain Reconnaissance")
            domains = await self.find_company_domains(company_name)
            contacts['domains'] = domains
            
            # Step 2: WHOIS Information
            logger.info("Step 2: WHOIS Information")
            whois_contacts = await self.extract_whois_contacts(domains)
            contacts['emails'].extend(whois_contacts.get('emails', []))
            contacts['phone_numbers'].extend(whois_contacts.get('phones', []))
            
            # Step 3: Social Media Reconnaissance
            logger.info("Step 3: Social Media Reconnaissance")
            social_contacts = await self.extract_social_media_contacts(company_name)
            contacts['social_media'] = social_contacts.get('profiles', [])
            contacts['emails'].extend(social_contacts.get('emails', []))
            
            # Step 4: LinkedIn Company Page Reconnaissance
            logger.info("Step 4: LinkedIn Company Page Reconnaissance")
            linkedin_contacts = await self.extract_linkedin_company_contacts(company_name)
            contacts['emails'].extend(linkedin_contacts.get('emails', []))
            contacts['hiring_emails'].extend(linkedin_contacts.get('hiring_emails', []))
            contacts['hr_emails'].extend(linkedin_contacts.get('hr_emails', []))
            
            # Step 5: Company Website Reconnaissance
            logger.info("Step 5: Company Website Reconnaissance")
            for domain in domains[:1]:  # Check only the first .com domain
                try:
                    website_contacts = await self.extract_website_contacts(domain, company_name)
                    contacts['emails'].extend(website_contacts.get('emails', []))
                    contacts['phone_numbers'].extend(website_contacts.get('phones', []))
                    contacts['contact_pages'].extend(website_contacts.get('pages', []))
                    contacts['hiring_emails'].extend(website_contacts.get('hiring_emails', []))
                    contacts['hr_emails'].extend(website_contacts.get('hr_emails', []))
                except Exception as e:
                    logger.debug(f"Error extracting contacts from {domain}: {str(e)}")
                    continue
            
            # Step 6: Email Pattern Generation
            logger.info("Step 6: Email Pattern Generation")
            generated_emails = await self.generate_email_patterns(company_name, domains)
            contacts['emails'].extend(generated_emails)
            
            # Remove duplicates and filter
            contacts = self.clean_and_filter_contacts(contacts)
            
            return contacts
            
        except Exception as e:
            logger.error(f"Error in reconnaissance for {company_name}: {str(e)}")
            return {}
        finally:
            if self.browser:
                await self.browser.close()
            if playwright:
                await playwright.stop()
    
    async def find_company_domains(self, company_name: str) -> List[str]:
        """
        Find company domains using DNS reconnaissance with prioritization
        """
        domains = []
        
        try:
            # Only use .com domains (most common and legitimate)
            primary_patterns = [
                f"{company_name.lower().replace(' ', '')}.com",  # Most common
                f"{company_name.lower().replace(' ', '-')}.com",  # With hyphens
            ]
            
            # Secondary .com patterns
            secondary_patterns = [
                f"{company_name.lower().replace(' ', '').replace('.', '')}.com",
            ]
            
            # Add variations for common company suffixes (only .com)
            suffix_patterns = []
            if not company_name.lower().endswith(('inc', 'corp', 'llc', 'ltd')):
                for suffix in ['inc', 'corp', 'llc', 'ltd']:
                    base_name = company_name.lower().replace(' ', '')
                    suffix_patterns.extend([
                        f"{base_name}{suffix}.com",
                        f"{base_name}-{suffix}.com",
                    ])
            
            # Test primary domains first (highest priority)
            primary_domains = []
            for domain in primary_patterns:
                try:
                    socket.gethostbyname(domain)
                    primary_domains.append(domain)
                    logger.info(f"Found primary domain: {domain}")
                except:
                    continue
            
            # Test secondary domains
            secondary_domains = []
            for domain in secondary_patterns:
                try:
                    socket.gethostbyname(domain)
                    secondary_domains.append(domain)
                    logger.info(f"Found secondary domain: {domain}")
                except:
                    continue
            
            # Test suffix domains (lowest priority)
            suffix_domains = []
            for domain in suffix_patterns:
                try:
                    socket.gethostbyname(domain)
                    suffix_domains.append(domain)
                    logger.info(f"Found suffix domain: {domain}")
                except:
                    continue
            
            # Also try to find domains through search
            search_domains = await self.search_for_domains(company_name)
            
            # Prioritize domains: primary first, then secondary, then suffix, then search
            domains = primary_domains + secondary_domains + suffix_domains + search_domains
            
            # Remove duplicates while preserving order
            seen = set()
            unique_domains = []
            for domain in domains:
                if domain not in seen:
                    seen.add(domain)
                    unique_domains.append(domain)
            
            return unique_domains
            
        except Exception as e:
            logger.error(f"Error finding domains for {company_name}: {str(e)}")
            return domains
            
        except Exception as e:
            logger.error(f"Error finding domains for {company_name}: {str(e)}")
            return domains
    
    async def search_for_domains(self, company_name: str) -> List[str]:
        """
        Search for company domains using search engines
        """
        domains = []
        
        try:
            search_queries = [
                f'"{company_name}" official website .com',
                f'"{company_name}" company website .com',
                f'site:{company_name.lower().replace(" ", "")}.com'
            ]
            
            for query in search_queries:
                try:
                    search_url = f"https://www.google.com/search?q={query}"
                    await self.page.goto(search_url, wait_until='domcontentloaded')
                    await asyncio.sleep(2)
                    
                    # Extract domains from search results
                    links = await self.page.query_selector_all('a[href]')
                    for link in links[:10]:
                        href = await link.get_attribute('href')
                        if href and 'http' in href:
                            # Extract domain from URL
                            if '/url?q=' in href:
                                url_start = href.find('/url?q=') + 7
                                url_end = href.find('&', url_start)
                                if url_end == -1:
                                    url_end = len(href)
                                url = href[url_start:url_end]
                            else:
                                url = href
                            
                            try:
                                domain = urlparse(url).netloc
                                if domain and domain not in domains and domain.endswith('.com'):
                                    # Filter out search engine and common service domains
                                    if not any(service in domain for service in ['google', 'bing', 'yahoo', 'facebook', 'twitter', 'linkedin']):
                                        domains.append(domain)
                            except:
                                continue
                                
                except Exception as e:
                    logger.debug(f"Error searching for domains with query '{query}': {str(e)}")
                    continue
            
            return domains
            
        except Exception as e:
            logger.error(f"Error searching for domains: {str(e)}")
            return domains
    
    async def extract_whois_contacts(self, domains: List[str]) -> Dict[str, List[str]]:
        """
        Extract contact information from WHOIS data
        """
        contacts = {'emails': [], 'phones': []}
        
        for domain in domains[:3]:  # Limit to first 3 domains
            try:
                w = whois.whois(domain)
                
                # Extract emails
                if w.emails:
                    if isinstance(w.emails, list):
                        contacts['emails'].extend(w.emails)
                    else:
                        contacts['emails'].append(w.emails)
                
                # Extract phone numbers
                if w.phone:
                    if isinstance(w.phone, list):
                        contacts['phones'].extend(w.phone)
                    else:
                        contacts['phones'].append(w.phone)
                
                logger.info(f"Extracted WHOIS contacts from {domain}")
                
            except Exception as e:
                logger.debug(f"Error extracting WHOIS from {domain}: {str(e)}")
                continue
        
        return contacts
    
    async def extract_social_media_contacts(self, company_name: str) -> Dict[str, List[str]]:
        """
        Extract contact information from social media profiles
        """
        contacts = {'profiles': [], 'emails': []}
        
        try:
            # Common social media platforms
            platforms = [
                'linkedin.com/company',
                'twitter.com',
                'facebook.com',
                'instagram.com',
                'youtube.com'
            ]
            
            for platform in platforms:
                try:
                    search_url = f"https://www.google.com/search?q=\"{company_name}\" {platform}"
                    await self.page.goto(search_url, wait_until='domcontentloaded')
                    await asyncio.sleep(2)
                    
                    # Look for social media links
                    links = await self.page.query_selector_all('a[href]')
                    for link in links[:5]:
                        href = await link.get_attribute('href')
                        if href and platform in href:
                            if '/url?q=' in href:
                                url_start = href.find('/url?q=') + 7
                                url_end = href.find('&', url_start)
                                if url_end == -1:
                                    url_end = len(href)
                                url = href[url_start:url_end]
                            else:
                                url = href
                            
                            if url not in contacts['profiles']:
                                contacts['profiles'].append(url)
                                
                                # Try to extract contact info from social profile
                                try:
                                    await self.page.goto(url, wait_until='domcontentloaded')
                                    await asyncio.sleep(2)
                                    
                                    # Look for contact information
                                    page_content = await self.page.content()
                                    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_content)
                                    
                                    for email in emails:
                                        if email not in contacts['emails']:
                                            contacts['emails'].append(email)
                                            
                                except Exception as e:
                                    logger.debug(f"Error extracting from social profile {url}: {str(e)}")
                                    continue
                                    
                except Exception as e:
                    logger.debug(f"Error searching {platform}: {str(e)}")
                    continue
            
            return contacts
            
        except Exception as e:
            logger.error(f"Error extracting social media contacts: {str(e)}")
            return contacts
    
    async def extract_linkedin_company_contacts(self, company_name: str) -> Dict[str, List[str]]:
        """
        Extract contact information from LinkedIn company pages
        """
        contacts = {'emails': [], 'hiring_emails': [], 'hr_emails': []}
        
        try:
            # Search for LinkedIn company page
            search_url = f"https://www.google.com/search?q=\"{company_name}\" site:linkedin.com/company"
            await self.page.goto(search_url, wait_until='domcontentloaded')
            await asyncio.sleep(2)
            
            # Find LinkedIn company page
            links = await self.page.query_selector_all('a[href*="linkedin.com/company"]')
            
            for link in links[:3]:
                href = await link.get_attribute('href')
                if href:
                    if '/url?q=' in href:
                        url_start = href.find('/url?q=') + 7
                        url_end = href.find('&', url_start)
                        if url_end == -1:
                            url_end = len(href)
                        linkedin_url = href[url_start:url_end]
                    else:
                        linkedin_url = href
                    
                    try:
                        # Navigate to LinkedIn company page
                        await self.page.goto(linkedin_url, wait_until='domcontentloaded')
                        await asyncio.sleep(3)
                        
                        # Look for contact information
                        page_content = await self.page.content()
                        page_text = await self.page.inner_text('body')
                        
                        # Extract emails
                        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_content)
                        
                        for email in emails:
                            if email not in contacts['emails']:
                                contacts['emails'].append(email)
                                
                                # Categorize emails
                                email_lower = email.lower()
                                if any(word in email_lower for word in ['hiring', 'jobs', 'careers', 'recruit', 'talent']):
                                    contacts['hiring_emails'].append(email)
                                elif any(word in email_lower for word in ['hr', 'human', 'people']):
                                    contacts['hr_emails'].append(email)
                        
                        # Look for "About" section or contact details
                        about_sections = await self.page.query_selector_all('[data-section="about"], .about-section, .company-info')
                        
                        for section in about_sections:
                            section_text = await section.inner_text()
                            section_emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', section_text)
                            
                            for email in section_emails:
                                if email not in contacts['emails']:
                                    contacts['emails'].append(email)
                                    
                                    # Categorize emails
                                    email_lower = email.lower()
                                    if any(word in email_lower for word in ['hiring', 'jobs', 'careers', 'recruit', 'talent']):
                                        contacts['hiring_emails'].append(email)
                                    elif any(word in email_lower for word in ['hr', 'human', 'people']):
                                        contacts['hr_emails'].append(email)
                        
                    except Exception as e:
                        logger.debug(f"Error extracting from LinkedIn page {linkedin_url}: {str(e)}")
                        continue
            
            return contacts
            
        except Exception as e:
            logger.error(f"Error extracting LinkedIn contacts: {str(e)}")
            return contacts
    
    async def extract_website_contacts(self, domain: str, company_name: str = None) -> Dict[str, List[str]]:
        """
        Extract contact information from company website with validation
        """
        contacts = {'emails': [], 'phones': [], 'pages': [], 'hiring_emails': [], 'hr_emails': []}
        
        try:
            website_url = f"https://{domain}"
            
            # Navigate to website
            await self.page.goto(website_url, wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            # Validate this is the correct company website
            if company_name and not await self.validate_company_website(domain, company_name):
                logger.warning(f"Domain {domain} may not be the correct company website for {company_name}")
                return contacts
            
            # Get page content
            page_content = await self.page.content()
            page_text = await self.page.inner_text('body')
            
            # Extract emails
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', page_content)
            
            for email in emails:
                if email not in contacts['emails']:
                    # Only include emails from the company domain or legitimate business emails
                    if self.is_legitimate_company_email(email, domain, company_name):
                        contacts['emails'].append(email)
                        
                        # Categorize emails
                        email_lower = email.lower()
                        if any(word in email_lower for word in ['hiring', 'jobs', 'careers', 'recruit', 'talent']):
                            contacts['hiring_emails'].append(email)
                        elif any(word in email_lower for word in ['hr', 'human', 'people']):
                            contacts['hr_emails'].append(email)
            
            # Extract phone numbers
            phone_patterns = [
                r'\+?1?\s*\(?[0-9]{3}\)?[\s.-]?[0-9]{3}[\s.-]?[0-9]{4}',
                r'\+?[0-9]{1,4}[\s.-]?[0-9]{1,4}[\s.-]?[0-9]{1,4}[\s.-]?[0-9]{1,4}'
            ]
            
            for pattern in phone_patterns:
                phones = re.findall(pattern, page_text)
                for phone in phones:
                    if phone not in contacts['phones']:
                        contacts['phones'].append(phone)
            
            # Find contact pages
            contact_selectors = [
                'a[href*="contact"]',
                'a[href*="about"]',
                'a[href*="careers"]',
                'a[href*="jobs"]'
            ]
            
            for selector in contact_selectors:
                contact_links = await self.page.query_selector_all(selector)
                for link in contact_links:
                    href = await link.get_attribute('href')
                    if href:
                        full_url = urljoin(website_url, href)
                        if full_url not in contacts['pages']:
                            contacts['pages'].append(full_url)
            
            return contacts
            
        except Exception as e:
            logger.error(f"Error extracting website contacts from {domain}: {str(e)}")
            return contacts
    
    async def generate_email_patterns(self, company_name: str, domains: List[str]) -> List[str]:
        """
        Generate common email patterns for the company
        """
        emails = []
        
        try:
            # Common email patterns
            patterns = [
                'info', 'contact', 'hello', 'hello@', 'contact@', 'info@',
                'hr', 'hiring', 'careers', 'jobs', 'recruitment', 'talent',
                'support', 'help', 'sales', 'marketing', 'press', 'media'
            ]
            
            # Company name variations
            name_variations = [
                company_name.lower().replace(' ', ''),
                company_name.lower().replace(' ', '.'),
                company_name.lower().replace(' ', '-'),
                company_name.lower().split()[0],  # First word
                company_name.lower().split()[-1]  # Last word
            ]
            
            for domain in domains[:1]:  # Use only the first .com domain
                for pattern in patterns:
                    email = f"{pattern}@{domain}"
                    emails.append(email)
                
                for name_var in name_variations:
                    for pattern in patterns:
                        email = f"{name_var}.{pattern}@{domain}"
                        emails.append(email)
                        email = f"{pattern}.{name_var}@{domain}"
                        emails.append(email)
            
            return emails
            
        except Exception as e:
            logger.error(f"Error generating email patterns: {str(e)}")
            return emails
    
    def clean_and_filter_contacts(self, contacts: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Clean and filter contact information
        """
        # Remove duplicates
        for key in contacts:
            if isinstance(contacts[key], list):
                contacts[key] = list(set(contacts[key]))
        
        # Filter out invalid emails
        valid_emails = []
        for email in contacts['emails']:
            if self.is_valid_email(email):
                valid_emails.append(email)
        contacts['emails'] = valid_emails
        
        # Filter out invalid phone numbers
        valid_phones = []
        for phone in contacts['phone_numbers']:
            if self.is_valid_phone(phone):
                valid_phones.append(phone)
        contacts['phone_numbers'] = valid_phones
        
        return contacts
    
    def is_valid_email(self, email: str) -> bool:
        """
        Validate email format and filter out spam
        """
        try:
            # Basic email validation
            if not re.match(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email):
                return False
            
            # Filter out spam indicators
            spam_indicators = [
                'example', 'test', 'noreply', 'no-reply', 'donotreply',
                'mailer-daemon', 'postmaster', 'webmaster', 'admin',
                'asxvmprobertest', 'gmail', 'yahoo', 'hotmail', 'outlook'
            ]
            
            email_lower = email.lower()
            for indicator in spam_indicators:
                if indicator in email_lower:
                    return False
            
            return True
            
        except:
            return False
    
    def is_valid_phone(self, phone: str) -> bool:
        """
        Validate phone number format
        """
        try:
            # Remove all non-digit characters
            digits = re.sub(r'\D', '', phone)
            
            # Check if it has reasonable length (7-15 digits)
            if len(digits) < 7 or len(digits) > 15:
                return False
            
            return True
            
        except:
            return False
    
    async def validate_company_website(self, domain: str, company_name: str) -> bool:
        """
        Validate if a domain is the correct company website
        """
        try:
            # Check if company name appears in the page title or content
            page_title = await self.page.title()
            page_text = await self.page.inner_text('body')
            
            # Check if company name appears in title or prominent text
            company_words = company_name.lower().split()
            title_lower = page_title.lower()
            text_lower = page_text.lower()
            
            # Check if company name appears in title
            title_match = any(word in title_lower for word in company_words if len(word) > 2)
            
            # Check if company name appears prominently in text (first 1000 chars)
            text_match = any(word in text_lower[:1000] for word in company_words if len(word) > 2)
            
            # Check if domain matches company name
            domain_match = any(word in domain.lower() for word in company_words if len(word) > 2)
            
            # If at least 2 out of 3 checks pass, it's likely the correct website
            matches = sum([title_match, text_match, domain_match])
            
            if matches >= 2:
                logger.info(f"Domain {domain} validated as correct company website for {company_name}")
                return True
            else:
                logger.warning(f"Domain {domain} may not be the correct company website for {company_name}")
                return False
                
        except Exception as e:
            logger.debug(f"Error validating company website {domain}: {str(e)}")
            return False
    
    def is_legitimate_company_email(self, email: str, domain: str, company_name: str = None) -> bool:
        """
        Check if an email is legitimate for the company
        """
        try:
            email_lower = email.lower()
            
            # Filter out spam indicators
            spam_indicators = [
                'example', 'test', 'noreply', 'no-reply', 'donotreply',
                'mailer-daemon', 'postmaster', 'webmaster', 'admin',
                'asxvmprobertest', 'gmail', 'yahoo', 'hotmail', 'outlook'
            ]
            
            for indicator in spam_indicators:
                if indicator in email_lower:
                    return False
            
            # Check if email domain matches website domain
            email_domain = email.split('@')[1].lower()
            if email_domain == domain.lower():
                return True
            
            # Check if email domain contains company name
            if company_name:
                company_words = company_name.lower().split()
                for word in company_words:
                    if len(word) > 2 and word in email_domain:
                        return True
            
            # Check for common legitimate business email patterns
            legitimate_patterns = [
                'company.com', 'corp.com', 'inc.com', 'llc.com', 'ltd.com',
                'enterprise.com', 'business.com', 'org.com'
            ]
            
            for pattern in legitimate_patterns:
                if pattern in email_domain:
                    return True
            
            return False
            
        except:
            return False

# Async wrapper for compatibility
async def extract_company_contacts_recon_async(company_name: str) -> Dict[str, List[str]]:
    """
    Async wrapper for reconnaissance-based company contact extraction
    """
    scraper = CompanyReconScraper()
    return await scraper.extract_company_contacts_recon(company_name)
