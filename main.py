"""
FastAPI Job Scraper Application

This application provides endpoints to scrape job postings from Indeed and LinkedIn
using browser automation with Playwright.

Setup Instructions:
1. Install dependencies: pip install -r requirements.txt
2. Install Playwright browsers: playwright install chromium
3. Set up environment variables (optional):
   - LINKEDIN_EMAIL: Your LinkedIn email
   - LINKEDIN_PASSWORD: Your LinkedIn password
4. Run the application: uvicorn main:app --reload

Usage:
- GET /scrape/indeed?job=python+developer&location=remote
- GET /scrape/linkedin?job=python+developer&location=remote
"""

import asyncio
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os

from scrapers.indeed_scraper import IndeedScraper
from scrapers.linkedin_scraper import LinkedInScraper
from utils.browser_manager import BrowserManager
from utils.excel_exporter import ExcelExporter
from models import JobPosting, ScrapingResponse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Job Scraper API",
    description="API for scraping job postings from Indeed and LinkedIn",
    version="1.0.0"
)

# Add CORS middleware to allow any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Job Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "indeed_json": "/scrape/indeed?job=<job_title>&location=<location>&max_jobs=5",
            "indeed_excel": "/scrape/indeed/excel?job=<job_title>&location=<location>&max_jobs=5",
            "linkedin_excel": "/scrape/linkedin?job=<job_title>&location=<location>&max_jobs=5",
            "list_exports": "/exports",
            "download_export": "/exports/{filename}"
        },
        "default_max_jobs": 5,
        "max_jobs_limit": 20
    }

@app.get("/scrape/indeed", response_model=ScrapingResponse)
async def scrape_indeed(
    job: str = Query(..., description="Job title to search for"),
    location: str = Query(..., description="Job location"),
    max_jobs: int = Query(5, description="Maximum number of jobs to scrape", ge=1, le=20)
):
    """
    Scrape job postings from Indeed
    
    Args:
        job: Job title to search for
        location: Job location
        max_jobs: Maximum number of jobs to scrape (default: 5, max: 20)
    
    Returns:
        ScrapingResponse with job listings
    """
    try:
        logger.info(f"Starting Indeed scrape for: {job} in {location}")
        
        # Use browser manager as async context manager
        async with BrowserManager() as browser_manager:
            # Create scraper instance
            scraper = IndeedScraper(browser_manager)
            
            # Scrape jobs
            jobs = await scraper.scrape_jobs(job, location, max_jobs)
            
            return ScrapingResponse(
                success=True,
                message=f"Successfully scraped {len(jobs)} jobs from Indeed",
                jobs=jobs,
                total_count=len(jobs)
            )
        
    except Exception as e:
        logger.error(f"Error scraping Indeed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scrape Indeed: {str(e)}"
        )

@app.get("/scrape/linkedin")
async def scrape_linkedin(
    job: str = Query(..., description="Job title to search for"),
    location: str = Query(..., description="Job location"),
    max_jobs: int = Query(5, description="Maximum number of jobs to scrape", ge=1, le=20)
):
    """
    Scrape job postings from LinkedIn and return as Excel file download
    
    Args:
        job: Job title to search for
        location: Job location
        max_jobs: Maximum number of jobs to scrape (default: 5, max: 20)
    
    Returns:
        Excel file download
    """
    try:
        logger.info(f"Starting LinkedIn scrape for: {job} in {location}")
        
        # Create scraper instance (no browser manager needed for LinkedIn)
        scraper = LinkedInScraper()
        
        # Scrape jobs (limited to 5 for now)
        jobs = await scraper.scrape_jobs(job, location, max_jobs)
        
        if not jobs:
            raise HTTPException(
                status_code=404,
                detail="No jobs found for the given criteria"
            )
        
        # Export to Excel and return directly as download
        exporter = ExcelExporter()
        excel_path = exporter.export_jobs_to_excel(jobs, "linkedin", job, location)
        
        # Return the Excel file as download
        return FileResponse(
            path=str(excel_path),
            filename=os.path.basename(excel_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    except Exception as e:
        logger.error(f"Error scraping LinkedIn: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scrape LinkedIn: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Job Scraper API is running"}

@app.get("/scrape/indeed/excel")
async def scrape_indeed_excel(
    job: str = Query(..., description="Job title to search for"),
    location: str = Query(..., description="Job location"),
    max_jobs: int = Query(5, description="Maximum number of jobs to scrape", ge=1, le=20)
):
    """
    Scrape job postings from Indeed and download as Excel file
    
    Args:
        job: Job title to search for
        location: Job location
        max_jobs: Maximum number of jobs to scrape (default: 5, max: 20)
    
    Returns:
        Excel file download
    """
    try:
        logger.info(f"Starting Indeed scrape for Excel: {job} in {location}")
        
        # Use browser manager as async context manager
        async with BrowserManager() as browser_manager:
            # Create scraper instance
            scraper = IndeedScraper(browser_manager)
            
            # Scrape jobs
            jobs = await scraper.scrape_jobs(job, location, max_jobs)
            
            if not jobs:
                raise HTTPException(
                    status_code=404,
                    detail="No jobs found for the given criteria"
                )
            
            # Export to Excel
            exporter = ExcelExporter()
            excel_path = exporter.export_jobs_to_excel(jobs, "indeed", job, location)
            
            # Return the Excel file
            return FileResponse(
                path=excel_path,
                filename=os.path.basename(excel_path),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
    except Exception as e:
        logger.error(f"Error scraping Indeed for Excel: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scrape Indeed: {str(e)}"
        )



@app.get("/exports")
async def list_exports():
    """List all exported Excel files"""
    try:
        exporter = ExcelExporter()
        exports = exporter.list_exports()
        return {
            "exports": exports,
            "total_files": len(exports),
            "export_directory": exporter.get_export_directory()
        }
    except Exception as e:
        logger.error(f"Error listing exports: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list exports: {str(e)}"
        )

@app.get("/exports/{filename}")
async def download_export(filename: str):
    """Download a specific exported Excel file"""
    try:
        exporter = ExcelExporter()
        file_path = exporter.output_dir / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File {filename} not found"
            )
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export {filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download file: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 