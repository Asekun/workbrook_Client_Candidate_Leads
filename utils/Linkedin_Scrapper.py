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

# Configure logging settings
logging.basicConfig(filename="scraping.log", level=logging.INFO)


def scrape_linkedin_jobs(job_title: str, location: str, pages: int = None) -> list:
    """
    Scrape job listings from LinkedIn based on job title and location.

    Parameters
    ----------
    job_title : str
        The job title to search for on LinkedIn.
    location : str
        The location to search for jobs in on LinkedIn.
    pages : int, optional
        The number of pages of job listings to scrape. If None, all available pages will be scraped.

    Returns
    -------
    list of dict
        A list of dictionaries, where each dictionary represents a job listing
        with the following keys: 'title', 'company', 'location', 'description',
        'poster_name', 'poster_position', 'apply_link', 'email', 'date_posted'
    """

    # Log a message indicating that we're starting a LinkedIn job search
    logging.info(f'Starting LinkedIn job scrape for "{job_title}" in "{location}"...')

    # Sets the pages to scrape if not provided
    pages = pages or 1

    # Set up Chrome options to maximize the window
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run headless for better compatibility
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # Initialize the web driver with automatic ChromeDriver management
            # Force download of latest ChromeDriver
            os.environ['WDM_LOG_LEVEL'] = '0'  # Suppress webdriver-manager logs
            
            if attempt == 0:
                # First attempt: try with default (latest) version
                service = Service(ChromeDriverManager().install())
            elif attempt == 1:
                # Second attempt: try clearing cache and retrying
                import shutil
                cache_dir = os.path.expanduser("~/.wdm")
                if os.path.exists(cache_dir):
                    shutil.rmtree(cache_dir)
                service = Service(ChromeDriverManager().install())
            else:
                # Third attempt: try with specific version
                service = Service(ChromeDriverManager().install())
            
            # Set longer timeout for driver initialization
            driver = webdriver.Chrome(service=service, options=options)
            
            # Set page load timeout
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            logging.info(f"ChromeDriver initialized successfully on attempt {attempt + 1}")
            break  # Success, exit retry loop
            
        except Exception as e:
            logging.warning(f"ChromeDriver initialization attempt {attempt + 1} failed: {str(e)}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                driver = None
            
            if attempt == max_retries - 1:
                logging.error("All ChromeDriver initialization attempts failed")
                return []
            
            # Wait before retry
            time.sleep(2)
    
    if not driver:
        logging.error("Failed to initialize ChromeDriver after all retries")
        return []

    try:
        # Navigate to the LinkedIn job search page with the given job title and location
        driver.get(
            f"https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}"
        )

        # Scroll through the pages of search results on LinkedIn
        for i in range(pages):

            # Log the current page number
            logging.info(f"Scrolling to bottom of page {i+1}...")

            # Scroll to the bottom of the page using JavaScript
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            try:
                # Wait for the "Show more" button to be present on the page
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "/html/body/div[1]/div/main/section[2]/button")
                    )
                )
                # Click on the "Show more" button
                element.click()

            # Handle any exception that may occur when locating or clicking on the button
            except Exception:
                # Log a message indicating that the button was not found and we're retrying
                logging.info("Show more button not found, retrying...")

            # Wait for a random amount of time before scrolling to the next page
            time.sleep(random.choice(list(range(3, 7))))

        # Scrape the job postings
        jobs = []
        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_listings = soup.find_all(
            "div",
            class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card",
        )

        try:
            for job in job_listings:
                # Extract basic job details from the listing card

                # job title
                job_title = job.find("h3", class_="base-search-card__title").text.strip()
                # job company
                job_company = job.find(
                    "h4", class_="base-search-card__subtitle"
                ).text.strip()
                # job location
                job_location = job.find(
                    "span", class_="job-search-card__location"
                ).text.strip()
                # job link
                apply_link = job.find("a", class_="base-card__full-link")["href"]

                # Navigate to the job posting page and scrape detailed information
                driver.get(apply_link)

                # Sleeping randomly
                time.sleep(random.choice(list(range(5, 11))))

                # Use try-except block to handle exceptions when retrieving job details
                try:
                    # Create a BeautifulSoup object from the webpage source
                    job_soup = BeautifulSoup(driver.page_source, "html.parser")

                    # Extract job description
                    job_description = ""
                    description_element = job_soup.find(
                        "div", class_="description__text description__text--rich"
                    )
                    if description_element:
                        job_description = description_element.text.strip()

                    # Extract poster information
                    poster_name = ""
                    poster_position = ""
                    
                    # Try to find poster information in the job details
                    poster_section = job_soup.find("div", class_="job-details-jobs-unified-top-card__job-insight")
                    if poster_section:
                        poster_text = poster_section.get_text(strip=True)
                        # Look for patterns that might indicate poster information
                        if "Posted by" in poster_text:
                            poster_name = poster_text.replace("Posted by", "").strip()
                        elif "Posted" in poster_text:
                            # Extract name from posted text
                            posted_match = re.search(r'Posted by (.+?)(?:\s+•|\s*$)', poster_text)
                            if posted_match:
                                poster_name = posted_match.group(1).strip()

                    # Try to find poster position
                    position_element = job_soup.find("span", class_="job-details-jobs-unified-top-card__job-insight")
                    if position_element:
                        poster_position = position_element.get_text(strip=True)

                    # Extract email from description (common pattern)
                    email = ""
                    if job_description:
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        email_match = re.search(email_pattern, job_description)
                        if email_match:
                            email = email_match.group(0)

                    # Extract date posted
                    date_posted = ""
                    date_element = job_soup.find("time")
                    if date_element:
                        date_posted = date_element.get("datetime", "")
                        if not date_posted:
                            date_posted = date_element.get_text(strip=True)

                    # Try to find the actual apply button/link
                    apply_button = job_soup.find("a", class_="jobs-apply-button")
                    if apply_button:
                        apply_link = apply_button.get("href", apply_link)

                # Handle the AttributeError exception that may occur if elements are not found
                except AttributeError as e:
                    # Log a warning message
                    logging.warning(f"AttributeError occurred while retrieving job details: {str(e)}")
                    # Set default values
                    job_description = job_description or ""
                    poster_name = poster_name or ""
                    poster_position = poster_position or ""
                    email = email or ""
                    date_posted = date_posted or ""

                # Add job details to the jobs list
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
                # Logging scraped job with company and location information
                logging.info(f'Scraped "{job_title}" at {job_company} in {job_location}...')

        # Catching any exception that occurs in the scraping process
        except Exception as e:
            # Log an error message with the exception details
            logging.error(f"An error occurred while scraping jobs: {str(e)}")

            # Return the jobs list that has been collected so far
            # This ensures that even if the scraping process is interrupted due to an error, we still have some data
            return jobs

    except Exception as e:
        logging.error(f"An error occurred during ChromeDriver initialization: {str(e)}")
        return []

    finally:
        if driver:
            # Close the Selenium web driver
            driver.quit()

    # Return the jobs list
    return jobs


def save_job_data(data: dict) -> None:
    """
    Save job data to a CSV file.

    Args:
        data: A dictionary containing job data.

    Returns:
        None
    """

    # Create a pandas DataFrame from the job data dictionary
    df = pd.DataFrame(data)

    # Save the DataFrame to a CSV file without including the index column
    df.to_csv(f"new_jobs_{datetime.now().strftime('%Y-%m-%d')}.csv", index=False)

    # Log a message indicating how many jobs were successfully scraped and saved to the CSV file
    logging.info(f"Successfully scraped {len(data)} jobs and saved to jobs.csv")


# Only run if this file is executed directly (not when imported)
if __name__ == "__main__":
    data = scrape_linkedin_jobs("Software Developer", "Nigeria", 1)
    save_job_data(data)
