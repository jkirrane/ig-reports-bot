# Implementation Guide - Inspector General Reports Bot

Step-by-step guide to build a fully automated IG reports bot with LLM filtering and summarization.

## 📋 Prerequisites

- GitHub account
- Bluesky account (create bot: `@igoversight.bsky.social` or similar)
- OpenAI account with API access
- VS Code with Claude (for building)
- Python 3.11+

## 🎯 Overview

**What we're building:**
- Scrape Oversight.gov daily for new IG reports
- Filter with keywords + LLM (GPT-4o-mini)
- Generate summaries with LLM
- Auto-post to Bluesky (5-10 posts/day)
- Website with browse/filter/RSS

**Time estimate:** 10-15 hours over 2 weeks  
**Monthly cost:** ~$2 (OpenAI API only)

---

## Phase 1: Foundation (2-3 hours)

### Step 1.1: Create GitHub Repository

```bash
# Create repo on GitHub
Name: "ig-reports-bot"
Description: "Automated bot posting federal Inspector General reports to Bluesky"
Public, with README

# Clone locally
git clone https://github.com/yourusername/ig-reports-bot.git
cd ig-reports-bot
```

### Step 1.2: Project Structure

```
ig-reports-bot/
├── .github/
│   └── workflows/
│       └── daily.yml
├── database/
│   ├── schema.sql
│   ├── db.py
│   └── ig_reports.db (created by db.py)
├── scrapers/
│   ├── __init__.py
│   ├── base.py
│   └── oversight_gov.py
├── llm/
│   ├── __init__.py
│   ├── client.py
│   ├── filter.py
│   └── summary.py
├── bot/
│   ├── __init__.py
│   ├── bluesky_poster.py
│   └── post_reports.py
├── web/
│   ├── build.py
│   ├── templates/
│   │   └── index.html.template
│   └── static/
│       ├── styles.css
│       └── script.js
├── docs/ (generated)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Step 1.3: Requirements File

```bash
# requirements.txt
requests>=2.31.0
beautifulsoup4>=4.12.0
openai>=1.0.0
atproto>=0.0.50
feedgen>=1.0.0
python-dotenv>=1.0.0
lxml>=4.9.0
```

**Install:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 1.4: Environment Variables

**Create `.env.example`:**
```
OPENAI_API_KEY=sk-proj-...
BLUESKY_HANDLE=your-handle.bsky.social
BLUESKY_APP_PASSWORD=your-app-password
```

**Create `.env` (don't commit!):**
```bash
cp .env.example .env
# Edit .env with real credentials
```

**Update `.gitignore`:**
```
.env
__pycache__/
*.pyc
.DS_Store
venv/
*.log
```

### Step 1.5: Database Schema

**In VS Code Claude:**

```
Create database/schema.sql based on IG_REPORTS_BOT_SPEC.md

Include:
- ig_reports table with all fields
- bot_posts table
- agencies table
- All indexes

Then create database/db.py with these functions:
- get_connection()
- initialize_database()
- upsert_report()
- get_unfiltered_reports()
- get_unposted_reports()
- mark_filtered()
- mark_posted()
```

**Test:**
```bash
python -m database.db  # Should create ig_reports.db
sqlite3 database/ig_reports.db ".schema"  # Verify tables
```

---

## Phase 2: Scraper (3-4 hours)

### Step 2.1: Research Oversight.gov

**Manually explore:**
1. Go to https://www.oversight.gov/reports/federal
2. Open browser DevTools (Network tab)
3. See how they load reports
4. Look for:
   - JSON endpoints?
   - Pagination?
   - Search filters?

**Common patterns:**
- Static HTML with report cards
- JavaScript-loaded content
- RSS feeds per agency
- Search API

### Step 2.2: Base Scraper

**In VS Code Claude:**

```
Create scrapers/base.py with BaseScraper class

Include:
- fetch_page(url) with proper User-Agent
- Rate limiting (1-2 seconds between requests)
- Error handling
- Logging
```

### Step 2.3: Oversight.gov Scraper

**In VS Code Claude:**

```
Create scrapers/oversight_gov.py

Scrape https://www.oversight.gov/reports/federal for:
- New reports from last 24 hours
- Extract: title, agency, date, type, abstract, URL
- Handle pagination if needed
- Return list of report dicts

Should have:
- scrape_recent_reports(days_back=1)
- parse_report_card(soup_element)
- --dry-run flag for testing
```

**Test:**
```bash
python -m scrapers.oversight_gov --dry-run
# Should print 10-20 recent reports
```

### Step 2.4: Keyword Pre-filter

**In VS Code Claude:**

```
Add to scrapers/oversight_gov.py:

def has_interesting_keywords(report):
    """Quick keyword check before LLM"""
    text = (report['title'] + ' ' + report.get('abstract', '')).lower()
    
    keywords = [
        'fraud', 'criminal', 'investigation', 'waste',
        'abuse', 'million', 'billion', 'scheme',
        'mismanagement', 'failure', 'guilty', 'charged'
    ]
    
    return any(k in text for k in keywords)

Only save reports that pass this filter.
```

---

## Phase 3: LLM Integration (3-4 hours)

### Step 3.1: OpenAI Client Setup

**In VS Code Claude:**

```
Create llm/client.py based on LLM_INTEGRATION.md

Include:
- OpenAI client setup
- call_gpt() wrapper function
- Error handling
- Retry logic
```

**Test:**
```python
from llm.client import call_gpt

response = call_gpt("Say hello in JSON", response_format={"type": "json_object"})
print(response)
# Should get: {"message": "Hello!"}
```

### Step 3.2: Filter LLM

**In VS Code Claude:**

```
Create llm/filter.py based on LLM_INTEGRATION.md

Use the FILTER_PROMPT_TEMPLATE from the spec.

Include:
- filter_report(report) function
- JSON parsing and validation
- Error handling with fallback

Test with 3-5 real reports from Oversight.gov
```

**Test:**
```python
from llm.filter import filter_report

report = {
    'title': 'DOJ: Investigation of Prison Fraud',
    'agency_name': 'Department of Justice',
    'abstract': 'Criminal charges filed against contractor...'
}

result = filter_report(report)
print(result)
# Should return JSON with newsworthy=True
```

### Step 3.3: Summary LLM

**In VS Code Claude:**

```
Create llm/summary.py based on LLM_INTEGRATION.md

Include:
- generate_post(report, filter_result)
- format_complete_post() with hashtags + link
- Length validation

Test with filtered reports from Step 3.2
```

**Test:**
```python
from llm.summary import generate_post, format_complete_post

# After filtering
post_text = generate_post(report, filter_result)
complete = format_complete_post(post_text, report, filter_result)

print(complete)
print(f"Length: {len(complete)} chars")
# Should be under 300 chars, properly formatted
```

### Step 3.4: Cost Tracking

**Add to llm/client.py:**

```python
import json
from datetime import datetime

def log_usage(model, input_tokens, output_tokens, cost):
    """Track API usage for cost monitoring"""
    with open('llm_usage.log', 'a') as f:
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': cost
        }
        f.write(json.dumps(log_entry) + '\n')

# Check monthly costs
def check_monthly_cost():
    """Sum up costs from current month"""
    # Read llm_usage.log and calculate total
    pass
```

---

## Phase 4: Bluesky Bot (2 hours)

### Step 4.1: Bluesky Poster

**In VS Code Claude:**

```
Create bot/bluesky_poster.py

Reuse pattern from regulatory comment bot:
- BlueskyPoster class
- login()
- post(text) method
- Error handling
```

**Test connection:**
```python
from bot.bluesky_poster import BlueskyPoster

poster = BlueskyPoster(handle, password)
poster.post("🧪 Test post from IG Reports Bot - please ignore!")
```

### Step 4.2: Posting Logic

**In VS Code Claude:**

```
Create bot/post_reports.py

Main function: post_newsworthy_reports()

Flow:
1. Get unposted reports from database (where posted=0 and passed_llm_filter=1)
2. For each report:
   - Get the stored post_text from database
   - Post to Bluesky
   - Mark as posted in database
   - Wait 1-2 hours between posts (stagger throughout day)

Include:
- --dry-run flag
- Posting time distribution
- Error recovery
```

**Test:**
```bash
python -m bot.post_reports --dry-run
# Should show what would be posted
```

---

## Phase 5: Daily Workflow (2 hours)

### Step 5.1: Main Pipeline Script

**Create `run_daily.py` in project root:**

```python
#!/usr/bin/env python3
"""
Main pipeline: Scrape → Filter → Summarize → Store

Run this daily via GitHub Actions
"""

import sys
from scrapers.oversight_gov import scrape_recent_reports
from llm.filter import filter_report
from llm.summary import generate_post, format_complete_post
from database.db import upsert_report, get_connection

def main(dry_run=False):
    """Main pipeline"""
    print("🔍 Scraping Oversight.gov...")
    reports = scrape_recent_reports(days_back=1)
    print(f"Found {len(reports)} new reports")
    
    conn = get_connection()
    
    newsworthy_count = 0
    
    for report in reports:
        print(f"\n📄 Processing: {report['title'][:60]}...")
        
        # Filter with LLM
        filter_result = filter_report(report)
        
        if not filter_result:
            print("❌ LLM filter failed, skipping")
            continue
        
        # Generate post if newsworthy
        post_text = None
        if filter_result['newsworthy']:
            newsworthy_count += 1
            print(f"✅ Newsworthy (score: {filter_result['score']}/10)")
            
            # Generate summary
            post_text = generate_post(report, filter_result)
            if post_text:
                complete_post = format_complete_post(post_text, report, filter_result)
                print(f"📝 Generated post ({len(complete_post)} chars)")
                post_text = complete_post
        else:
            print(f"❌ Not newsworthy: {filter_result['reason']}")
        
        # Store in database
        if not dry_run:
            upsert_report(
                report=report,
                filter_result=filter_result,
                post_text=post_text
            )
    
    conn.close()
    
    print(f"\n✅ Pipeline complete!")
    print(f"   Total reports: {len(reports)}")
    print(f"   Newsworthy: {newsworthy_count}")
    
    return newsworthy_count

if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    main(dry_run=dry_run)
```

**Test:**
```bash
python run_daily.py --dry-run
```

### Step 5.2: GitHub Actions Workflow

**In VS Code Claude:**

```
Create .github/workflows/daily.yml

Schedule:
- Daily at 8 AM ET (1 PM UTC)
- Manual trigger option

Steps:
1. Checkout code
2. Set up Python 3.11
3. Install dependencies
4. Run scraper + filter + summarize (run_daily.py)
5. Post to Bluesky (bot/post_reports.py with staggered timing)
6. Build website (later)
7. Commit database

Environment variables from GitHub Secrets:
- OPENAI_API_KEY
- BLUESKY_HANDLE
- BLUESKY_APP_PASSWORD
```

### Step 5.3: Add GitHub Secrets

1. Go to repo Settings → Secrets and variables → Actions
2. Add:
   - `OPENAI_API_KEY`
   - `BLUESKY_HANDLE`
   - `BLUESKY_APP_PASSWORD`

### Step 5.4: Test Workflow

```bash
# Push to GitHub
git add .
git commit -m "Initial bot implementation"
git push

# Go to Actions tab
# Click "Run workflow" (manual trigger)
# Watch logs
```

---

## Phase 6: Website (2-3 hours)

### Step 6.1: Static Site Generator

**In VS Code Claude:**

```
Create web/build.py

Generate:
- index.html (last 30 days of reports)
- agency pages (e.g., /agency/dod.html)
- RSS feed (feed.xml)
- JSON API (data.json)

Features:
- Filter by agency, type
- Sort by date, score
- Highlight criminal cases
- Show dollar amounts
```

### Step 6.2: Templates & Styles

**In VS Code Claude:**

```
Create web/templates/index.html.template

Bootstrap or simple CSS design:
- Header with search
- Filter buttons (agency, type)
- Report cards with:
  - Agency badge
  - Title
  - Key finding
  - $ amount if >$1M
  - 🚨 icon if criminal
  - Link to full report
```

```
Create web/static/styles.css

Clean design:
- Card-based layout
- Responsive grid
- Color coding by agency
- Mobile-friendly
```

### Step 6.3: Test Locally

```bash
python -m web.build

open docs/index.html
```

### Step 6.4: Enable GitHub Pages

1. Go to Settings → Pages
2. Source: Branch `main`, Folder `/docs`
3. Save

Site live at: `https://yourusername.github.io/ig-reports-bot/`

### Step 6.5: Add to Workflow

**Update `.github/workflows/daily.yml`:**

```yaml
- name: Build Website
  run: python -m web.build

- name: Commit Changes
  run: |
    git config user.name "IG Reports Bot"
    git config user.email "bot@noreply.github.com"
    git add database/ig_reports.db docs/
    git commit -m "Update reports - $(date)" || echo "No changes"
    git push
```

---

## Phase 7: Polish & Launch (2 hours)

### Step 7.1: Monitoring

**Check daily for first week:**
- GitHub Actions logs for errors
- LLM decisions (`llm_decisions.log`)
- Database growth (`sqlite3 database/ig_reports.db "SELECT COUNT(*) FROM ig_reports"`)
- Bluesky posts quality

### Step 7.2: Tune LLM Prompts

**Based on results:**
- False positives → Tighten filter criteria
- False negatives → Broaden criteria
- Poor summaries → Adjust summary prompt
- Cost too high → Add more keyword pre-filtering

### Step 7.3: Bot Profile

**Set up Bluesky account:**
- Avatar: Government/oversight themed
- Bio: "Automated feed of Inspector General reports on fraud, waste, and abuse in federal government. 🏛️ Data from Oversight.gov | Not affiliated with any agency"
- Link to website

### Step 7.4: Documentation

**Update README.md:**
- Clear description
- Link to website
- Link to Bluesky account
- Credits to Oversight.gov
- Mention it's automated

### Step 7.5: Announce

**Soft launch:**
- Post from your personal account
- Share in civic tech communities
- Reddit: r/transparency, r/datasets
- Hacker News (if gets traction)

---

## 💰 Cost Summary

**Monthly costs:**
- OpenAI API: $1-2
- GitHub Actions: $0 (free tier)
- GitHub Pages: $0 (free)
- Domain (optional): $1

**Total: $1-3/month** ✅

---

## 📊 Success Metrics

**After 1 month:**
- [ ] Bot posting 5-10 reports daily
- [ ] 500+ Bluesky followers
- [ ] Website gets 1000+ visits
- [ ] RSS feed has subscribers
- [ ] Zero cost overruns

**After 3 months:**
- [ ] 2000+ followers
- [ ] Cited by journalists
- [ ] Clear public value
- [ ] Sustainable and low-maintenance

---

**Ready to make government accountability accessible!** 🏛️✨

**Timeline:** 2-3 weekends to build and launch
