"""
Browser Manager for Selenium

This module provides a centralized browser management system for web scraping
with Selenium and ChromeDriver with proper resource cleanup and configuration.
"""

import asyncio
import logging
import time
import random
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Manages Selenium WebDriver instances with proper configuration and cleanup.
    
    This class handles browser initialization, page management, and anti-detection
    measures with proper resource cleanup.
    """
    
    def __init__(self):
        self.driver = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup"""
        await self.cleanup()
        
    async def start(self):
        """Initialize Selenium WebDriver"""
        try:
            # Configure Chrome options for anti-detection
            chrome_options = Options()
            
            # Anti-detection settings
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Window size
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Additional stealth settings
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')  # Faster loading
            chrome_options.add_argument('--disable-javascript')  # Disable JS for faster loading
            
            # Headless mode (set to False for debugging)
            chrome_options.add_argument('--headless')
            
            # Initialize ChromeDriver with automatic management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute stealth script
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            logger.info("Selenium browser manager started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start browser manager: {str(e)}")
            await self.cleanup()
            raise
            
    async def cleanup(self):
        """Clean up browser resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                
            logger.info("Browser manager cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            
    async def get_page(self, url: str, wait_for_element: Optional[str] = None, timeout: int = 30) -> bool:
        """
        Navigate to a URL and wait for page to load
        
        Args:
            url: URL to navigate to
            wait_for_element: CSS selector to wait for (optional)
            timeout: Timeout in seconds
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Add random delay to simulate human behavior
            await self.add_random_delay(2, 4)
            
            # Wait for specific element if provided
            if wait_for_element:
                try:
                    WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                    )
                    logger.info(f"Element {wait_for_element} found")
                except TimeoutException:
                    logger.warning(f"Element {wait_for_element} not found within timeout")
                    
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            return False
            
    async def find_elements(self, selector: str, timeout: int = 10) -> list:
        """
        Find elements on the page using CSS selector
        
        Args:
            selector: CSS selector
            timeout: Timeout in seconds
            
        Returns:
            List of WebElement objects
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            logger.info(f"Found {len(elements)} elements with selector: {selector}")
            return elements
            
        except TimeoutException:
            logger.warning(f"No elements found with selector: {selector}")
            return []
        except Exception as e:
            logger.error(f"Error finding elements: {str(e)}")
            return []
            
    async def get_element_text(self, element, selector: str) -> Optional[str]:
        """
        Get text from an element using CSS selector
        
        Args:
            element: WebElement object
            selector: CSS selector
            
        Returns:
            Text content or None
        """
        try:
            sub_element = element.find_element(By.CSS_SELECTOR, selector)
            text = sub_element.text.strip()
            return text if text else None
            
        except Exception:
            return None
            
    async def get_element_attribute(self, element, selector: str, attribute: str) -> Optional[str]:
        """
        Get attribute from an element using CSS selector
        
        Args:
            element: WebElement object
            selector: CSS selector
            attribute: Attribute name
            
        Returns:
            Attribute value or None
        """
        try:
            sub_element = element.find_element(By.CSS_SELECTOR, selector)
            value = sub_element.get_attribute(attribute)
            return value if value else None
            
        except Exception:
            return None
            
    async def scroll_page(self, scroll_pause_time: float = 1.0):
        """Scroll page to load dynamic content"""
        try:
            # Get scroll height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # Scroll down to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait to load page
                await asyncio.sleep(scroll_pause_time)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            await asyncio.sleep(scroll_pause_time)
            
        except Exception as e:
            logger.warning(f"Error during page scrolling: {str(e)}")
            
    async def add_random_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Add random delay to simulate human behavior"""
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
        
    async def handle_captcha(self) -> bool:
        """
        Basic CAPTCHA detection
        
        Returns:
            True if CAPTCHA was detected, False otherwise
        """
        try:
            # Check for common CAPTCHA indicators
            captcha_selectors = [
                'iframe[src*="captcha"]',
                'div[class*="captcha"]',
                'form[action*="captcha"]',
                'input[name*="captcha"]',
                'div[class*="recaptcha"]'
            ]
            
            for selector in captcha_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.warning("CAPTCHA detected on page")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error checking for CAPTCHA: {str(e)}")
            return False
            
    def get_page_source(self) -> str:
        """Get current page source"""
        return self.driver.page_source if self.driver else ""
        
    def get_current_url(self) -> str:
        """Get current URL"""
        return self.driver.current_url if self.driver else "" 