# Import necessary packages for web scraping and logging
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import random
import time
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import re
import os
import platform
import shutil
import subprocess

# Configure logging settings
logging.basicConfig(filename="scraping.log", level=logging.INFO)


def get_chromium_version():
    """Get Chromium version to ensure ChromeDriver compatibility"""
    try:
        chromium_path = shutil.which(
            "chromium-browser") or shutil.which("chromium")
        if chromium_path:
            result = subprocess.run([chromium_path, "--version"],
                                    capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.strip()
                # Extract version number (e.g., "Chromium 120.0.6099.109")
                version_match = re.search(r'(\d+)\.(\d+)\.(\d+)', version_line)
                if version_match:
                    major_version = version_match.group(1)
                    logging.info(f"Chromium version: {major_version}")
                    return major_version
    except Exception as e:
        logging.warning(f"Could not determine Chromium version: {str(e)}")
    return None


def get_driver(options):
    """
    Initialize Chrome or Chromium driver depending on environment.
    """
    # Essential options for server environments
    # Use new headless mode for Chrome >= 109
    options.add_argument("--headless=new")
    # Required in Docker/low-permission environments
    options.add_argument("--no-sandbox")
    # Avoid limited /dev/shm space issues
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")  # GPU not available
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-field-trial-config")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-background-networking")
    options.add_argument(
        "--disable-component-extensions-with-background-pages")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-prompt-on-repost")
    options.add_argument("--disable-domain-reliability")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Needed in some headless environments
    options.add_argument("--remote-debugging-port=9222")

    system = platform.system().lower()

    logging.warning(
        "Chromium not found — falling back to webdriver_manager Chrome")
    try:
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)
    except Exception as e:
        logging.error(
            f"Failed to install ChromeDriver via webdriver_manager: {str(e)}")
        raise Exception("Could not initialize ChromeDriver")


def scrape_linkedin_jobs(job_title: str, location: str, pages: int = None) -> list:
    """
    Scrape job listings from LinkedIn based on job title and location.
    """
    logging.info(
        f'Starting LinkedIn job scrape for "{job_title}" in "{location}"...')

    pages = pages or 1

    # Set up Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-field-trial-config")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-background-networking")
    options.add_argument(
        "--disable-component-extensions-with-background-pages")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-prompt-on-repost")
    options.add_argument("--disable-domain-reliability")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Server-only optimisations
    if platform.system().lower() == "linux":
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.cookies": 2,
            "profile.managed_default_content_settings.javascript": 1
        }
        options.add_experimental_option("prefs", prefs)

    driver = None
    max_retries = 3

    for attempt in range(max_retries):
        try:
            os.environ['WDM_LOG_LEVEL'] = '0'
            driver = get_driver(options)

            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)

            logging.info(
                f"WebDriver initialized successfully on attempt {attempt + 1}")
            break

        except Exception as e:
            logging.warning(
                f"WebDriver initialization attempt {attempt + 1} failed: {str(e)}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None

            if attempt == max_retries - 1:
                logging.error("All WebDriver initialization attempts failed")
                return []

            time.sleep(2)

    if not driver:
        logging.error("Failed to initialize WebDriver")
        return []

    try:
        driver.get(
            f"https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}"
        )

        for i in range(pages):
            logging.info(f"Scrolling to bottom of page {i+1}...")
            driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")

            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH,
                         "/html/body/div[1]/div/main/section[2]/button")
                    )
                )
                element.click()
            except Exception:
                logging.info("Show more button not found, retrying...")

            time.sleep(random.choice(list(range(3, 7))))

        jobs = []
        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_listings = soup.find_all(
            "div",
            class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
        )

        try:
            for job in job_listings:
                job_title = job.find(
                    "h3", class_="base-search-card__title").text.strip()
                job_company = job.find(
                    "h4", class_="base-search-card__subtitle"
                ).text.strip()
                job_location = job.find(
                    "span", class_="job-search-card__location"
                ).text.strip()
                apply_link = job.find(
                    "a", class_="base-card__full-link")["href"]

                driver.get(apply_link)
                time.sleep(random.choice(list(range(5, 11))))

                try:
                    job_soup = BeautifulSoup(driver.page_source, "html.parser")

                    job_description = ""
                    description_element = job_soup.find(
                        "div", class_="description__text description__text--rich"
                    )
                    if description_element:
                        job_description = description_element.text.strip()

                    poster_name = ""
                    poster_position = ""
                    poster_section = job_soup.find(
                        "div", class_="job-details-jobs-unified-top-card__job-insight"
                    )
                    if poster_section:
                        poster_text = poster_section.get_text(strip=True)
                        if "Posted by" in poster_text:
                            poster_name = poster_text.replace(
                                "Posted by", "").strip()
                        else:
                            posted_match = re.search(
                                r'Posted by (.+?)(?:\s+•|\s*$)', poster_text)
                            if posted_match:
                                poster_name = posted_match.group(1).strip()

                    position_element = job_soup.find(
                        "span", class_="job-details-jobs-unified-top-card__job-insight"
                    )
                    if position_element:
                        poster_position = position_element.get_text(strip=True)

                    email = ""
                    if job_description:
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        email_match = re.search(email_pattern, job_description)
                        if email_match:
                            email = email_match.group(0)

                    date_posted = ""
                    date_element = job_soup.find("time")
                    if date_element:
                        date_posted = date_element.get("datetime", "")
                        if not date_posted:
                            date_posted = date_element.get_text(strip=True)

                    apply_button = job_soup.find(
                        "a", class_="jobs-apply-button")
                    if apply_button:
                        apply_link = apply_button.get("href", apply_link)

                except AttributeError as e:
                    logging.warning(
                        f"AttributeError occurred while retrieving job details: {str(e)}")

                jobs.append(
                    {
                        "title": job_title,
                        "company": job_company,
                        "location": job_location,
                        "description": job_description,
                        "poster_name": poster_name,
                        "poster_position": poster_position,
                        "apply_link": apply_link,
                        "email": email,
                        "date_posted": date_posted,
                    }
                )
                logging.info(
                    f'Scraped "{job_title}" at {job_company} in {job_location}...')

        except Exception as e:
            logging.error(f"An error occurred while scraping jobs: {str(e)}")
            return jobs

    except Exception as e:
        logging.error(f"An error occurred during job scraping: {str(e)}")
        return []

    finally:
        if driver:
            driver.quit()

    return jobs


def save_job_data(data: dict) -> None:
    """
    Save job data to a CSV file.
    """
    df = pd.DataFrame(data)
    df.to_csv(
        f"new_jobs_{datetime.now().strftime('%Y-%m-%d')}.csv", index=False)
    logging.info(f"Successfully scraped {len(data)} jobs and saved to CSV")


if __name__ == "__main__":
    data = scrape_linkedin_jobs("Software Developer", "Nigeria", 1)
    save_job_data(data)
