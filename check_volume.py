#!/usr/bin/env python3
"""Check report volume on oversight.gov to determine backfill feasibility"""

import sys
sys.path.insert(0, '.')

from scrapers.oversight_gov import OversightGovScraper
from datetime import datetime
from collections import Counter

print("📊 Analyzing report volume on oversight.gov...")
print("   Scraping multiple pages to check date distribution...\n")

scraper = OversightGovScraper()

# Scrape several pages to get a sample
all_reports = []
for page in range(1, 11):  # Check first 10 pages
    url = f"https://www.oversight.gov/reports/federal?page={page}" if page > 1 else "https://www.oversight.gov/reports/federal"
    
    print(f"Fetching page {page}...")
    html = scraper.fetch_page(url)
    if not html:
        break
    
    reports = scraper._parse_reports_page(html)
    if not reports:
        break
    
    all_reports.extend(reports)
    print(f"  Found {len(reports)} reports on page {page}")

print(f"\n✅ Total reports scraped: {len(all_reports)}")

# Analyze dates
dates = []
for report in all_reports:
    if report.get('published_date'):
        date_str = report['published_date'].replace('Z', '+00:00')
        date = datetime.fromisoformat(date_str).date()
        dates.append(date)

if dates:
    dates.sort(reverse=True)
    print(f"\n📅 Date range:")
    print(f"   Most recent: {dates[0]}")
    print(f"   Oldest: {dates[-1]}")
    print(f"   Total days: {(dates[0] - dates[-1]).days} days")
    
    # Count by month
    print(f"\n📈 Reports by month:")
    month_counts = Counter(d.strftime('%Y-%m') for d in dates)
    for month in sorted(month_counts.keys(), reverse=True):
        print(f"   {month}: {month_counts[month]} reports")
    
    # Calculate daily average
    total_days = (dates[0] - dates[-1]).days + 1
    avg_per_day = len(dates) / total_days
    print(f"\n📊 Average: {avg_per_day:.1f} reports per day")
    print(f"   ({len(dates)} reports over {total_days} days)")
    
    # Cost estimates
    print(f"\n💰 Backfill cost estimates:")
    print(f"   With PDF analysis (~$0.0003/report):")
    print(f"     - 100 reports: ${100 * 0.0003:.2f}")
    print(f"     - 500 reports: ${500 * 0.0003:.2f}")
    print(f"     - 1000 reports: ${1000 * 0.0003:.2f}")
    print(f"     - All {len(dates)} reports: ${len(dates) * 0.0003:.2f}")
    
    # Estimate total reports in last few months
    months_to_check = [1, 3, 6, 12]
    print(f"\n🔮 Estimated total reports:")
    for months in months_to_check:
        estimated = int(avg_per_day * 30 * months)
        cost = estimated * 0.0003
        print(f"   Last {months} month(s): ~{estimated} reports (${cost:.2f} to process)")
