#!/usr/bin/env python3
"""
Test script for the reconnaissance-based company contact scraper
"""

import asyncio
import logging
from scrapers.company_recon_scraper import CompanyReconScraper

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_recon_scraper():
    """Test the reconnaissance-based company contact scraper"""
    try:
        scraper = CompanyReconScraper()
        
        # Test with Canonical
        print("🔍 Testing Reconnaissance Scraper with Canonical")
        print("=" * 80)
        
        contacts = await scraper.extract_company_contacts_recon("Canonical")
        
        print(f"\n📊 RECONNAISSANCE RESULTS:")
        print("=" * 80)
        
        if contacts:
            print(f"✅ Found contact information:")
            
            if contacts.get('domains'):
                print(f"   🌐 Domains ({len(contacts['domains'])}):")
                for domain in contacts['domains']:
                    print(f"      - {domain}")
            
            if contacts.get('emails'):
                print(f"   📧 Emails ({len(contacts['emails'])}):")
                for email in contacts['emails']:
                    print(f"      - {email}")
            
            if contacts.get('hiring_emails'):
                print(f"   🎯 Hiring Emails ({len(contacts['hiring_emails'])}):")
                for email in contacts['hiring_emails']:
                    print(f"      - {email}")
            
            if contacts.get('hr_emails'):
                print(f"   👥 HR Emails ({len(contacts['hr_emails'])}):")
                for email in contacts['hr_emails']:
                    print(f"      - {email}")
            
            if contacts.get('phone_numbers'):
                print(f"   📞 Phone Numbers ({len(contacts['phone_numbers'])}):")
                for phone in contacts['phone_numbers']:
                    print(f"      - {phone}")
            
            if contacts.get('social_media'):
                print(f"   📱 Social Media ({len(contacts['social_media'])}):")
                for profile in contacts['social_media'][:3]:  # Show first 3
                    print(f"      - {profile}")
            
            if contacts.get('contact_pages'):
                print(f"   🔗 Contact Pages ({len(contacts['contact_pages'])}):")
                for page in contacts['contact_pages'][:3]:  # Show first 3
                    print(f"      - {page}")
        else:
            print("❌ No contact information found")
            
    except Exception as e:
        logger.error(f"Error testing reconnaissance scraper: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_recon_scraper())
