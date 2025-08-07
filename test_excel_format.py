#!/usr/bin/env python3
"""
Test script to verify Excel file format
"""

import pandas as pd
import sys

def test_excel_format(filename):
    """Test the Excel file format"""
    try:
        # Read the Excel file
        df = pd.read_excel(filename)
        
        print(f"Excel file: {filename}")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print("\nFirst few rows:")
        print(df.head())
        
        # Check if required columns exist
        required_columns = [
            'ID', 'Job Title', 'Company', 'Location', 'Description',
            'Poster Name', 'Poster Position', 'Email', 'Apply Link', 'Date Posted'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"\n❌ Missing columns: {missing_columns}")
        else:
            print(f"\n✅ All required columns present")
            
        return True
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        test_excel_format(filename)
    else:
        print("Usage: python test_excel_format.py <excel_file>") 