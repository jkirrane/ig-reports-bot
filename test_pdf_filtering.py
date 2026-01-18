#!/usr/bin/env python3
"""Test PDF extraction and LLM filtering on a single report"""

import sys
sys.path.insert(0, '.')

from scrapers.oversight_gov import OversightGovScraper
from llm.filter import filter_report
from database.db import initialize_database

# Initialize database
initialize_database()

# Scrape just 1 report
print("🔍 Scraping 1 recent report...")
scraper = OversightGovScraper()
reports = scraper.scrape_recent_reports(days_back=1)

if reports:
    report = reports[0]
    print(f'\n📄 Report: {report["title"][:80]}...')
    print(f'   Agency: {report.get("agency_name")}')
    print(f'   PDF URL: {report.get("pdf_url", "N/A")}')
    print(f'   PDF Text: {len(report.get("pdf_text", ""))} chars')
    print(f'   PDF Pages: {report.get("pdf_pages", "N/A")}')
    
    # Filter with LLM
    print(f'\n🤖 Filtering with LLM using PDF content...')
    result = filter_report(report)
    
    if result:
        print(f'\n✅ LLM Result:')
        print(f'   Newsworthy: {result["newsworthy"]}')
        print(f'   Score: {result["score"]}/10')
        print(f'   Reason: {result["reason"]}')
        print(f'   Criminal: {result.get("criminal", False)}')
        print(f'   Dollar Amount: ${result.get("dollar_amount", 0):,}' if result.get("dollar_amount") else "   Dollar Amount: None")
        print(f'   Topics: {result.get("topics", [])}')
    else:
        print('❌ Filtering failed')
else:
    print('❌ No reports found')
