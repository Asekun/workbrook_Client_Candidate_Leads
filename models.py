"""
Pydantic models for the FastAPI Job Scraper

This module contains the data models used throughout the application.
"""

from typing import List, Optional
from pydantic import BaseModel

class JobPosting(BaseModel):
    """Model for job posting data"""
    title: str
    company: str
    location: str
    url: Optional[str] = None
    description: Optional[str] = None

class ScrapingResponse(BaseModel):
    """Model for scraping response"""
    success: bool
    message: str
    jobs: List[JobPosting]
    total_count: int 