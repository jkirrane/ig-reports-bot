"""
Static website generator for IG Reports Bot
Generates GitHub Pages site from SQLite database
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any
import sqlite3

from database import get_connection


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs')


def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, 'data'), exist_ok=True)


def get_all_reports(days_back: int = 30) -> List[Dict[str, Any]]:
    """
    Get all reports from database
    
    Args:
        days_back: Number of days to include
    
    Returns:
        List of report dicts
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT * FROM ig_reports 
        WHERE published_date >= date('now', ? || ' days')
        ORDER BY published_date DESC, newsworthy_score DESC
    """
    
    cursor.execute(query, (f'-{days_back}',))
    rows = cursor.fetchall()
    conn.close()
    
    reports = []
    for row in rows:
        report = dict(row)
        # Parse JSON fields
        if report.get('topics'):
            try:
                report['topics'] = json.loads(report['topics'])
            except:
                report['topics'] = []
        else:
            report['topics'] = []
        reports.append(report)
    
    return reports


def get_stats() -> Dict[str, Any]:
    """Get statistics for the website"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total reports
    cursor.execute("SELECT COUNT(*) as count FROM ig_reports")
    stats['total_reports'] = cursor.fetchone()['count']
    
    # Newsworthy reports
    cursor.execute("SELECT COUNT(*) as count FROM ig_reports WHERE passed_llm_filter = 1")
    stats['newsworthy_reports'] = cursor.fetchone()['count']
    
    # Posted reports
    cursor.execute("SELECT COUNT(*) as count FROM ig_reports WHERE posted = 1")
    stats['posted_reports'] = cursor.fetchone()['count']
    
    # Reports by agency (top 10)
    cursor.execute("""
        SELECT agency_id, agency_name, COUNT(*) as count
        FROM ig_reports
        WHERE passed_llm_filter = 1
        GROUP BY agency_id
        ORDER BY count DESC
        LIMIT 10
    """)
    stats['top_agencies'] = [dict(row) for row in cursor.fetchall()]
    
    # Last updated
    cursor.execute("SELECT MAX(created_at) as last_update FROM ig_reports")
    last_update = cursor.fetchone()['last_update']
    stats['last_updated'] = last_update if last_update else datetime.now().isoformat()
    
    conn.close()
    
    return stats


def generate_data_json(reports: List[Dict[str, Any]]):
    """Generate JSON data file for JavaScript"""
    # Prepare data for frontend
    data = {
        'reports': [],
        'updated': datetime.now().isoformat()
    }
    
    for report in reports:
        data['reports'].append({
            'id': report['id'],
            'title': report['title'],
            'agency_name': report['agency_name'],
            'agency_id': report['agency_id'],
            'published_date': report['published_date'],
            'report_type': report['report_type'],
            'url': report['url'],
            'newsworthy': bool(report.get('passed_llm_filter')),
            'score': report.get('newsworthy_score'),
            'reason': report.get('llm_filter_reason'),
            'post_text': report.get('post_text'),
            'topics': report.get('topics', []),
            'dollar_amount': report.get('dollar_amount'),
            'criminal': bool(report.get('criminal')),
            'posted': bool(report.get('posted')),
            'posted_at': report.get('posted_at')
        })
    
    # Write JSON file
    with open(os.path.join(OUTPUT_DIR, 'data', 'reports.json'), 'w') as f:
        json.dump(data, f, indent=2)


def generate_html(reports: List[Dict[str, Any]], stats: Dict[str, Any]):
    """Generate main HTML file"""
    
    # Read template
    template_path = os.path.join(TEMPLATE_DIR, 'index.html')
    with open(template_path, 'r') as f:
        template = f.read()
    
    # Format last updated
    last_updated = datetime.fromisoformat(stats['last_updated']).strftime('%B %d, %Y at %I:%M %p')
    
    # Replace placeholders
    html = template.replace('{{TOTAL_REPORTS}}', str(stats['total_reports']))
    html = html.replace('{{NEWSWORTHY_REPORTS}}', str(stats['newsworthy_reports']))
    html = html.replace('{{POSTED_REPORTS}}', str(stats['posted_reports']))
    html = html.replace('{{LAST_UPDATED}}', last_updated)
    
    # Generate agency filter options
    agencies = sorted(set(r['agency_name'] for r in reports))
    agency_options = '\n'.join([f'<option value="{a}">{a}</option>' for a in agencies])
    html = html.replace('{{AGENCY_OPTIONS}}', agency_options)
    
    # Write HTML
    with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w') as f:
        f.write(html)


def copy_static_files():
    """Copy CSS and JS files to output directory"""
    import shutil
    
    # Copy CSS
    css_src = os.path.join(STATIC_DIR, 'styles.css')
    css_dest = os.path.join(OUTPUT_DIR, 'styles.css')
    if os.path.exists(css_src):
        shutil.copy(css_src, css_dest)
    
    # Copy JS
    js_src = os.path.join(STATIC_DIR, 'script.js')
    js_dest = os.path.join(OUTPUT_DIR, 'script.js')
    if os.path.exists(js_src):
        shutil.copy(js_src, js_dest)


def build_website(days_back: int = 30):
    """
    Build the complete static website
    
    Args:
        days_back: Number of days of reports to include
    """
    print("🌐 Building IG Reports Bot website...")
    
    # Create output directory
    ensure_output_dir()
    print(f"   Created output directory: {OUTPUT_DIR}")
    
    # Get data
    print(f"   Fetching reports (last {days_back} days)...")
    reports = get_all_reports(days_back=days_back)
    print(f"   Found {len(reports)} reports")
    
    # Get stats
    stats = get_stats()
    print(f"   {stats['newsworthy_reports']} newsworthy, {stats['posted_reports']} posted")
    
    # Generate JSON data
    print("   Generating data files...")
    generate_data_json(reports)
    
    # Generate HTML
    print("   Generating HTML...")
    generate_html(reports, stats)
    
    # Copy static files
    print("   Copying static assets...")
    copy_static_files()
    
    print(f"\n✅ Website built successfully!")
    print(f"   Output: {OUTPUT_DIR}")
    print(f"   Open: {os.path.join(OUTPUT_DIR, 'index.html')}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Build IG Reports Bot website')
    parser.add_argument('--days-back', type=int, default=30, help='Number of days of reports to include')
    
    args = parser.parse_args()
    
    build_website(days_back=args.days_back)
