#!/usr/bin/env python3
"""Quick test of PDF filtering on one report"""

import sys
sys.path.insert(0, '.')

from scrapers.oversight_gov import OversightGovScraper
from scrapers.pdf_extractor import extract_pdf_text
from llm.filter import filter_report

# Test with a known report
print("📄 Testing PDF extraction on recent IG report...\n")

report = {
    'title': 'Audit of the Administration of Help America Vote Act Grants Awarded to the State of Utah',
    'agency_name': 'Election Assistance Commission',
    'report_type': 'Audit',
    'published_date': '2026-01-16',
    'url': 'https://www.oversight.gov/reports/audit/audit-administration-help-america-vote-act-grants-awarded-state-utah',
    'pdf_url': 'https://www.oversight.gov/sites/default/files/documents/reports/2026-01/G25UT0069-26-06_Utah_HAVA_Audit_Report.pdf'
}

# Extract PDF text
print(f"Extracting PDF: {report['pdf_url']}")
pdf_data = extract_pdf_text(report['pdf_url'])

if pdf_data:
    report['pdf_text'] = pdf_data['text']
    report['pdf_pages'] = pdf_data['pages']
    print(f"✅ Extracted {pdf_data['chars']:,} chars from {pdf_data['pages']} pages\n")
    
    # Show first 500 chars
    print("First 500 chars of PDF:")
    print(pdf_data['text'][:500])
    print("...\n")
    
    # Filter with LLM
    print("🤖 Filtering with LLM using full PDF content...")
    result = filter_report(report)
    
    if result:
        print(f'\n✅ LLM Result:')
        print(f'   Newsworthy: {result["newsworthy"]}')
        print(f'   Score: {result["score"]}/10')
        print(f'   Reason: {result["reason"]}')
        print(f'   Criminal: {result.get("criminal", False)}')
        if result.get("dollar_amount"):
            print(f'   Dollar Amount: ${result["dollar_amount"]:,}')
        print(f'   Topics: {result.get("topics", [])}')
        
        print(f'\n💰 Cost estimate: ~$0.002-0.004 per report with PDF analysis')
        print(f'   (vs ~$0.0001 with title only)')
    else:
        print('❌ Filtering failed')
else:
    print('❌ PDF extraction failed')
