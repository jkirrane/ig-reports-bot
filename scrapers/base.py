"""
Base scraper class with rate limiting, error handling, and retries
"""

import time
import requests
from typing import Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseScraper:
    """
    Base class for web scrapers with best practices built in
    """
    
    def __init__(self, rate_limit: float = 2.0):
        """
        Args:
            rate_limit: Minimum seconds between requests (default 2.0)
        """
        self.rate_limit = rate_limit
        self.last_request_time = 0
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Rotate user agents to be respectful
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        self.current_ua_index = 0
    
    def _get_user_agent(self) -> str:
        """Rotate through user agents"""
        ua = self.user_agents[self.current_ua_index]
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        return ua
    
    def _enforce_rate_limit(self) -> None:
        """Ensure we don't make requests too quickly"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            sleep_time = self.rate_limit - elapsed
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def fetch_page(
        self, 
        url: str, 
        max_retries: int = 3,
        timeout: int = 30,
        headers: Optional[dict] = None
    ) -> Optional[str]:
        """
        Fetch a web page with error handling and retries
        
        Args:
            url: URL to fetch
            max_retries: Number of retry attempts
            timeout: Request timeout in seconds
            headers: Optional custom headers (will be merged with defaults)
        
        Returns:
            HTML content as string, or None on failure
        """
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Build headers
        default_headers = {
            'User-Agent': self._get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        if headers:
            default_headers.update(headers)
        
        # Retry loop
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Fetching: {url} (attempt {attempt + 1}/{max_retries})")
                
                response = requests.get(
                    url,
                    headers=default_headers,
                    timeout=timeout,
                    allow_redirects=True
                )
                
                # Check status code
                if response.status_code == 200:
                    self.logger.info(f"✅ Success: {url} ({len(response.content)} bytes)")
                    return response.text
                
                elif response.status_code == 404:
                    self.logger.warning(f"❌ 404 Not Found: {url}")
                    return None  # Don't retry 404s
                
                elif response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = (attempt + 1) * 5
                    self.logger.warning(f"⚠️ Rate limited (429). Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                else:
                    self.logger.warning(f"⚠️ HTTP {response.status_code}: {url}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
            
            except requests.exceptions.Timeout:
                self.logger.warning(f"⚠️ Timeout: {url}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"⚠️ Connection error: {url} - {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
            
            except requests.exceptions.RequestException as e:
                self.logger.error(f"❌ Request failed: {url} - {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
        
        # All retries failed
        self.logger.error(f"❌ Failed to fetch after {max_retries} attempts: {url}")
        return None
    
    def log_scrape_result(self, success_count: int, total_count: int, source: str) -> None:
        """
        Log summary of scraping results
        
        Args:
            success_count: Number of successful items
            total_count: Total items attempted
            source: Description of what was scraped
        """
        timestamp = datetime.now().isoformat()
        
        if success_count == total_count:
            self.logger.info(f"✅ Scraped {success_count}/{total_count} {source}")
        else:
            self.logger.warning(f"⚠️ Scraped {success_count}/{total_count} {source} ({total_count - success_count} failed)")


# Example usage
if __name__ == '__main__':
    scraper = BaseScraper(rate_limit=1.0)
    
    # Test with a simple page
    html = scraper.fetch_page('https://www.oversight.gov')
    
    if html:
        print(f"Successfully fetched page ({len(html)} characters)")
    else:
        print("Failed to fetch page")
