"""
Scraper for Oversight.gov federal IG reports
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
import logging

from .base import BaseScraper


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
                    report_date = datetime.fromisoformat(report['published_date']).date()
                    if report_date >= cutoff_date:
                        all_reports.append(report)
            
            # If oldest report on this page is older than cutoff, stop
            if oldest_date:
                oldest = datetime.fromisoformat(oldest_date).date()
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
        
        # Find all report cards - adjust selector based on actual HTML structure
        # This is a common pattern but may need adjustment
        report_cards = soup.select('.views-row, .report-card, article.node--type-report')
        
        if not report_cards:
            # Try alternative selectors
            report_cards = soup.select('article')
        
        self.logger.debug(f"Found {len(report_cards)} potential report cards")
        
        for card in report_cards:
            try:
                report = self._parse_report_card(card)
                if report:
                    reports.append(report)
            except Exception as e:
                self.logger.warning(f"Failed to parse report card: {e}")
                continue
        
        return reports
    
    def _parse_report_card(self, element) -> Optional[Dict[str, Any]]:
        """
        Extract report data from a single report card element
        
        Returns:
            Report dictionary or None if parsing fails
        """
        try:
            report = {}
            
            # Extract title and URL
            title_elem = element.select_one('h2 a, h3 a, .field--name-title a, a.report-title')
            if not title_elem:
                # Try any link with substantial text
                title_elem = element.find('a', string=lambda s: s and len(s.strip()) > 20)
            
            if not title_elem:
                return None
            
            report['title'] = title_elem.get_text(strip=True)
            report['url'] = title_elem.get('href', '')
            
            # Make URL absolute
            if report['url'].startswith('/'):
                report['url'] = self.BASE_URL + report['url']
            
            # Generate report_id from URL or title
            report['report_id'] = self._extract_report_id(report['url'], report['title'])
            
            # Extract agency
            agency_elem = element.select_one('.field--name-field-agency, .agency, .report-agency')
            if agency_elem:
                agency_text = agency_elem.get_text(strip=True)
                report['agency_name'] = agency_text
                report['agency_id'] = self._normalize_agency_id(agency_text)
            else:
                # Try to extract from URL or title
                report['agency_name'] = self._extract_agency_from_text(report['title'])
                report['agency_id'] = self._normalize_agency_id(report['agency_name'])
            
            # Extract date
            date_elem = element.select_one('.field--name-field-publish-date, .date, time, .report-date')
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                report['published_date'] = self._parse_date(date_text)
            else:
                # Use current date as fallback
                report['published_date'] = datetime.now().isoformat()
            
            # Extract report type
            type_elem = element.select_one('.field--name-field-report-type, .report-type')
            if type_elem:
                report['report_type'] = type_elem.get_text(strip=True)
            else:
                report['report_type'] = 'Report'
            
            # Extract abstract/summary
            abstract_elem = element.select_one('.field--name-body, .summary, .description, .report-summary')
            if abstract_elem:
                report['abstract'] = abstract_elem.get_text(strip=True)
            else:
                # Use title as fallback
                report['abstract'] = report['title']
            
            return report
        
        except Exception as e:
            self.logger.warning(f"Error parsing report card: {e}")
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
