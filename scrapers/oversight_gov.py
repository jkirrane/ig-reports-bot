"""
Scraper for Oversight.gov federal IG reports
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import logging

from .base import BaseScraper
from .pdf_extractor import extract_pdf_text


logger = logging.getLogger(__name__)


# Common keywords that indicate newsworthy content
INTERESTING_KEYWORDS = [
    'fraud', 'waste', 'abuse', 'criminal', 'investigation', 'misconduct',
    'mismanagement', 'violation', 'deficiency', 'failure', 'breach',
    'unauthorized', 'improper', 'illegal', 'theft', 'embezzlement',
    'kickback', 'bribery', 'corruption', 'whistleblower', 'substantiated'
]


class OversightGovScraper(BaseScraper):
    """
    Scraper for Oversight.gov federal IG reports
    """
    
    BASE_URL = 'https://www.oversight.gov'
    REPORTS_URL = 'https://www.oversight.gov/reports/federal'
    
    def __init__(self):
        super().__init__(rate_limit=2.0)
        self.logger = logging.getLogger(__name__)
    
    def scrape_recent_reports(self, days_back: int = 1) -> List[Dict[str, Any]]:
        """
        Scrape recent IG reports from Oversight.gov
        
        Args:
            days_back: How many days back to look for reports (default 1)
        
        Returns:
            List of report dictionaries
        """
        self.logger.info(f"🔍 Scraping reports from last {days_back} day(s)")
        
        all_reports = []
        cutoff_date = datetime.now().date() - timedelta(days=days_back)
        
        # Start with first page
        page = 1
        max_pages = 10  # Safety limit
        
        while page <= max_pages:
            # Build URL with pagination
            if page == 1:
                url = self.REPORTS_URL
            else:
                url = f"{self.REPORTS_URL}?page={page}"
            
            self.logger.info(f"Fetching page {page}...")
            html = self.fetch_page(url)
            
            if not html:
                self.logger.warning(f"Failed to fetch page {page}, stopping")
                break
            
            # Parse the page
            reports = self._parse_reports_page(html)
            
            if not reports:
                self.logger.info(f"No more reports found on page {page}")
                break
            
            # Check if we've gone past our date range
            oldest_date = min(r['published_date'] for r in reports if r.get('published_date'))
            
            # Add reports that are within our date range
            for report in reports:
                if report.get('published_date'):
                    # Handle ISO format with Z suffix
                    date_str = report['published_date'].replace('Z', '+00:00')
                    report_date = datetime.fromisoformat(date_str).date()
                    if report_date >= cutoff_date:
                        all_reports.append(report)
            
            # If oldest report on this page is older than cutoff, stop
            if oldest_date:
                oldest_date_str = oldest_date.replace('Z', '+00:00')
                oldest = datetime.fromisoformat(oldest_date_str).date()
                if oldest < cutoff_date:
                    self.logger.info(f"Reached reports older than {cutoff_date}, stopping")
                    break
            
            page += 1
        
        self.logger.info(f"✅ Found {len(all_reports)} reports from last {days_back} day(s)")
        
        return all_reports
    
    def _parse_reports_page(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse a single page of reports
        
        Returns:
            List of report dictionaries
        """
        soup = BeautifulSoup(html, 'lxml')
        reports = []
        
        # Find all table rows - oversight.gov uses a table layout
        table_rows = soup.find_all('tr', class_='listing-table__row')
        
        self.logger.debug(f"Found {len(table_rows)} report table rows")
        
        for row in table_rows:
            try:
                report = self._parse_report_row(row)
                if report:
                    reports.append(report)
            except Exception as e:
                self.logger.warning(f"Failed to parse report row: {e}")
                continue
        
        return reports
    
    def _parse_report_row(self, row) -> Optional[Dict[str, Any]]:
        """
        Extract report data from a single table row
        
        Returns:
            Report dictionary or None if parsing fails
        """
        try:
            report = {}
            
            # Extract title
            title_cell = row.find('td', class_='views-field-title')
            if title_cell:
                report['title'] = title_cell.get_text(strip=True)
                report['abstract'] = report['title']  # Use title as abstract
            
            # Extract link to report page
            link_cell = row.find('td', class_='action-cell')
            if link_cell:
                link = link_cell.find('a')
                if link:
                    href = link.get('href', '')
                    if href.startswith('/'):
                        report['url'] = self.BASE_URL + href
                    else:
                        report['url'] = href
            
            # Extract date
            date_cell = row.find('td', class_='views-field-field-report-date-issued')
            if date_cell:
                time_elem = date_cell.find('time')
                if time_elem:
                    datetime_str = time_elem.get('datetime', '')
                    if datetime_str:
                        report['published_date'] = datetime_str
            
            # Extract agency
            agency_cell = row.find('td', class_='views-field-field-report-agency-reviewed')
            if agency_cell:
                agency_text = agency_cell.get_text(strip=True)
                report['agency_name'] = agency_text
                report['agency_id'] = self._normalize_agency_id(agency_text)
            
            # Extract report type
            type_cell = row.find('td', class_='views-field-field-report-type')
            if type_cell:
                report['report_type'] = type_cell.get_text(strip=True)
            
            # Generate report_id from URL
            if report.get('url'):
                # Extract the last part of the URL as report_id
                url_parts = report['url'].rstrip('/').split('/')
                report['report_id'] = url_parts[-1] if url_parts else report.get('url')
            
            # Check if we got minimum required fields
            if not report.get('title') or not report.get('url') or not report.get('agency_name'):
                return None
            
            # Use current date as fallback if no date found
            if not report.get('published_date'):
                report['published_date'] = datetime.now().isoformat()
            
            # Use generic type if none found
            if not report.get('report_type'):
                report['report_type'] = 'Report'
            
            # Fetch PDF link from report landing page
            if report.get('url'):
                pdf_url = self._fetch_pdf_url(report['url'])
                if pdf_url:
                    report['pdf_url'] = pdf_url
                    
                    # Extract PDF text for LLM analysis
                    pdf_data = extract_pdf_text(pdf_url)
                    if pdf_data:
                        report['pdf_text'] = pdf_data['text']
                        report['pdf_pages'] = pdf_data['pages']
                        self.logger.info(f"📄 Extracted {pdf_data['chars']:,} chars from PDF ({pdf_data['pages']} pages)")
            
            return report
        
        except Exception as e:
            self.logger.warning(f"Error parsing report row: {e}")
            return None
    
    def _fetch_pdf_url(self, report_url: str) -> Optional[str]:
        """
        Fetch the PDF URL from a report landing page
        
        Args:
            report_url: URL of the report landing page
            
        Returns:
            Full URL to PDF file, or None if not found
        """
        try:
            html = self.fetch_page(report_url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Look for PDF link
            pdf_link = soup.find('a', href=lambda x: x and '.pdf' in x.lower())
            if pdf_link:
                href = pdf_link.get('href', '')
                if href.startswith('/'):
                    return self.BASE_URL + href
                elif href.startswith('http'):
                    return href
                else:
                    # Relative URL
                    return self.BASE_URL + '/' + href.lstrip('/')
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error fetching PDF URL from {report_url}: {e}")
            return None
    
    def _extract_report_id(self, url: str, title: str) -> str:
        """
        Extract or generate unique report ID
        """
        # Try to extract from URL
        match = re.search(r'/node/(\d+)', url)
        if match:
            return f"oversight-{match.group(1)}"
        
        # Try other URL patterns
        match = re.search(r'/reports?/([a-zA-Z0-9-]+)', url)
        if match:
            return match.group(1)
        
        # Generate from title (fallback)
        title_slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:50]
        return f"report-{title_slug}"
    
    def _normalize_agency_id(self, agency_name: str) -> str:
        """
        Convert agency name to short ID (e.g., "Department of Defense" -> "DOD")
        """
        # Common agency mappings
        agency_map = {
            'defense': 'DOD',
            'health and human services': 'HHS',
            'veterans affairs': 'VA',
            'homeland security': 'DHS',
            'justice': 'DOJ',
            'state': 'DOS',
            'treasury': 'TREAS',
            'agriculture': 'USDA',
            'commerce': 'DOC',
            'education': 'ED',
            'energy': 'DOE',
            'transportation': 'DOT',
            'interior': 'DOI',
            'labor': 'DOL',
            'housing and urban development': 'HUD',
            'environmental protection': 'EPA',
            'small business': 'SBA',
            'social security': 'SSA',
        }
        
        agency_lower = agency_name.lower()
        
        for key, code in agency_map.items():
            if key in agency_lower:
                return code
        
        # Extract acronym if present
        acronym_match = re.search(r'\b([A-Z]{2,})\b', agency_name)
        if acronym_match:
            return acronym_match.group(1)
        
        # Generate from first letters
        words = agency_name.split()[:3]
        return ''.join(w[0].upper() for w in words if w)
    
    def _extract_agency_from_text(self, text: str) -> str:
        """
        Try to extract agency name from text (fallback)
        """
        # Common patterns
        match = re.search(r'(?:Department of|Office of)\s+([A-Za-z\s]+)', text)
        if match:
            return match.group(1).strip()
        
        return 'Unknown Agency'
    
    def _parse_date(self, date_text: str) -> str:
        """
        Parse various date formats into ISO format
        """
        # Try common formats
        formats = [
            '%B %d, %Y',     # December 15, 2023
            '%b %d, %Y',     # Dec 15, 2023
            '%m/%d/%Y',      # 12/15/2023
            '%Y-%m-%d',      # 2023-12-15
            '%d-%m-%Y',      # 15-12-2023
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_text.strip(), fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        # If all parsing fails, return current date
        self.logger.warning(f"Could not parse date: {date_text}")
        return datetime.now().isoformat()
    



def main():
    """
    Test the scraper
    """
    scraper = OversightGovScraper()
    
    # Scrape last 2 days
    reports = scraper.scrape_recent_reports(days_back=2)
    
    print(f"\n📊 Scraped {len(reports)} reports")
    print(f"   All reports will be evaluated by LLM (no keyword pre-filtering)")
    
    # Show sample
    print("\n📝 Sample reports:")
    for report in reports[:5]:
        print(f"\n- {report['title'][:80]}")
        print(f"  Agency: {report['agency_name']} ({report['agency_id']})")
        print(f"  Date: {report['published_date']}")
        print(f"  URL: {report['url']}")


if __name__ == '__main__':
    main()
