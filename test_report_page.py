import requests
from bs4 import BeautifulSoup

# Test with the first report from our database
report_url = 'https://www.oversight.gov/reports/audit/audit-administration-help-america-vote-act-grants-awarded-state-utah'

resp = requests.get(report_url, headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(resp.content, 'lxml')

print(f'Status: {resp.status_code}')
print(f'Content length: {len(resp.content)} bytes')
print()

# Look for PDF links
pdf_links = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
print(f'Found {len(pdf_links)} PDF links:')
for link in pdf_links:
    href = link.get('href')
    text = link.get_text(strip=True)
    print(f'  Text: {text}')
    print(f'  Href: {href}')
    print()

# Look for download buttons or report links
download_links = soup.find_all('a', class_=lambda x: x and ('download' in x.lower() or 'report' in x.lower()))
print(f'\nFound {len(download_links)} download/report links:')
for link in download_links[:5]:
    href = link.get('href', '')
    text = link.get_text(strip=True)
    classes = link.get('class', [])
    print(f'  Text: {text[:50]}')
    print(f'  Href: {href}')
    print(f'  Classes: {classes}')
    print()
