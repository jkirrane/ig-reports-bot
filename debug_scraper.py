#!/usr/bin/env python3
"""
Debug script to understand oversight.gov HTML structure
"""
import requests
from bs4 import BeautifulSoup

resp = requests.get('https://www.oversight.gov/reports/federal', 
                    headers={'User-Agent': 'Mozilla/5.0'})
soup = BeautifulSoup(resp.content, 'lxml')

# Get first article
container = soup.find('div', class_='views-element-container')
if not container:
    print("No views-element-container found!")
    exit(1)

articles = container.find_all('article')
print(f"Found {len(articles)} articles\n")

if not articles:
    print("No articles found!")
    exit(1)

article = articles[0]

print("=== FIRST ARTICLE ===")
print(f"Classes: {article.get('class')}\n")

# Find all fields
fields = article.find_all('div', class_=lambda x: x and 'field' in ' '.join(x))
print(f"Found {len(fields)} field divs\n")

for field in fields:
    classes = field.get('class', [])
    field_names = [c for c in classes if c.startswith('field--name-')]
    
    if field_names:
        name = field_names[0].replace('field--name-', '')
        
        # Get value
        value_div = field.find('div', class_='field__item')
        if value_div:
            value = value_div.get_text(strip=True)
            print(f"\n{name}:")
            print(f"  Value: {value[:150]}{'...' if len(value) > 150 else ''}")
            
            # Check for links
            links = value_div.find_all('a')
            if links:
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    print(f"  Link: {text[:50]} -> {href}")

# Also check for any h2, h3 tags with links
print("\n\n=== ALL HEADINGS IN ARTICLE ===")
for heading in article.find_all(['h1', 'h2', 'h3', 'h4']):
    print(f"{heading.name}: {heading.get_text(strip=True)[:80]}")
    links = heading.find_all('a')
    if links:
        for link in links:
            print(f"  Link: {link.get('href')}")

# Check for data attributes that might have the report URL/title
print("\n\n=== ARTICLE DATA ATTRIBUTES ===")
for attr, value in article.attrs.items():
    if attr.startswith('data-'):
        print(f"{attr}: {value}")

# Look at the actual full HTML
print("\n\n=== FULL ARTICLE HTML (first 3000 chars) ===")
print(article.prettify()[:3000])
