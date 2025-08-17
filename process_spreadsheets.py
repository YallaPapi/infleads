#!/usr/bin/env python3
"""
Script to process raw.csv and verified.csv spreadsheets:
1. Keep only entries from raw.csv that have verified emails (status='ok' in verified.csv)
2. Remove duplicates
3. Output cleaned data
"""

import pandas as pd
import sys
import os

def process_spreadsheets():
    """Process the raw and verified spreadsheets"""
    
    print("Loading spreadsheets...")
    
    # Load the raw CSV
    try:
        raw_df = pd.read_csv('raw.csv')
        print(f"✅ Loaded raw.csv: {len(raw_df)} entries")
    except Exception as e:
        print(f"❌ Error loading raw.csv: {e}")
        return
    
    # Load the verified CSV
    try:
        verified_df = pd.read_csv('verified.csv', skiprows=4)  # Skip the header info
        print(f"✅ Loaded verified.csv: {len(verified_df)} entries")
    except Exception as e:
        print(f"❌ Error loading verified.csv: {e}")
        return
    
    print("\nAnalyzing data structure...")
    print("Raw CSV columns:", raw_df.columns.tolist())
    print("Verified CSV columns:", verified_df.columns.tolist())
    
    # The verified CSV appears to have: email, name, domain, mx, status, result
    # We need to extract emails with status='ok'
    verified_emails = set()
    
    if len(verified_df.columns) >= 5:
        # Extract emails where status (column 5, index 4) is 'ok'
        ok_emails = verified_df[verified_df.iloc[:, 4] == 'ok'].iloc[:, 0]
        verified_emails = set(ok_emails.dropna())
        print(f"✅ Found {len(verified_emails)} verified emails with 'ok' status")
    else:
        print("❌ Verified CSV doesn't have expected structure")
        return
    
    print("\nFiltering raw data...")
    # Filter raw data to keep only entries with verified emails
    # Email is in column 'email' (index 3 based on the sample)
    filtered_df = raw_df[raw_df['email'].isin(verified_emails)]
    print(f"✅ Filtered to {len(filtered_df)} entries with verified emails")
    
    print("\nRemoving duplicates...")
    # Remove duplicates based on email address
    cleaned_df = filtered_df.drop_duplicates(subset=['email'], keep='first')
    print(f"✅ After removing duplicates: {len(cleaned_df)} entries")
    
    # Save the cleaned data
    output_file = 'raw_cleaned.csv'
    cleaned_df.to_csv(output_file, index=False)
    print(f"✅ Saved cleaned data to {output_file}")
    
    print(f"\nFinal count: {len(cleaned_df)} entries")
    
    # Show sample of the cleaned data
    print("\nSample of cleaned data:")
    print(cleaned_df[['name', 'email', 'organization_name']].head())
    
    return len(cleaned_df)

if __name__ == "__main__":
    result = process_spreadsheets()
    if result:
        print(f"\n🎉 Processing complete! Final count: {result} entries")
    else:
        print("\n❌ Processing failed")