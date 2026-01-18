import requests
from bs4 import BeautifulSoup

resp = requests.get('https://www.oversight.gov/reports/federal', headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(resp.content, 'lxml')

# Look for table rows
table_rows = soup.find_all('tr', class_='listing-table__row')
print(f'Found {len(table_rows)} table rows')
print()

if table_rows:
    row = table_rows[0]
    
    # Get title
    title_cell = row.find('td', class_='views-field-title')
    if title_cell:
        print('Title:', title_cell.get_text(strip=True))
    
    # Get link
    link_cell = row.find('td', class_='action-cell')
    if link_cell:
        link = link_cell.find('a')
        if link:
            print('URL:', link.get('href'))
            print('Link Text:', link.get_text(strip=True))
    
    # Get date
    date_cell = row.find('td', class_='views-field-field-report-date-issued')
    if date_cell:
        time_elem = date_cell.find('time')
        if time_elem:
            print('Date:', time_elem.get('datetime'))
    
    # Get agency
    agency_cell = row.find('td', class_='views-field-field-report-agency-reviewed')
    if agency_cell:
        print('Agency:', agency_cell.get_text(strip=True))
    
    # Get type
    type_cell = row.find('td', class_='views-field-field-report-type')
    if type_cell:
        print('Type:', type_cell.get_text(strip=True))
