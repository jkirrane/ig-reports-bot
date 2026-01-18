# IG Reports Bot - Agent Development Guide

## Project Overview

**Mission:** Automated bot that scrapes federal Inspector General reports, filters for newsworthy content using LLM, and posts to Bluesky to make government accountability accessible to the public.

**Current Status:** 🟡 Planning/Early Development Phase

**Tech Stack:**
- Python 3.11+
- SQLite (database)
- OpenAI GPT-4o-mini (filtering & summarization)
- Bluesky (atproto for posting)
- GitHub Actions (automation)
- GitHub Pages (static website)

**Monthly Cost:** ~$2 (OpenAI API only)

---

## Architecture Overview

```
Oversight.gov → Scraper → Keyword Filter → LLM Filter → Database
                                                          ↓
                                            Bluesky ← Post Generator
                                                          ↓
                                            Website ← Static Generator
```

### Data Flow

1. **Daily Scrape** - Fetch 50-100 new IG reports from Oversight.gov
2. **Keyword Pre-filter** - Quick filter for interesting terms (fraud, waste, criminal)
3. **LLM Filter** - GPT-4o-mini evaluates newsworthiness (keep 5-10 reports)
4. **LLM Summary** - Generate plain-English Bluesky posts
5. **Store** - Save filtered reports with metadata to SQLite
6. **Post** - Auto-post to Bluesky throughout the day
7. **Website** - Generate static HTML with browsing/filtering

---

## Project Structure

```
ig-reports-bot/
├── .github/
│   └── workflows/
│       └── daily.yml          # GitHub Actions automation
├── database/
│   ├── schema.sql             # Database schema
│   ├── db.py                  # Database operations
│   └── ig_reports.db          # SQLite database (created)
├── scrapers/
│   ├── __init__.py
│   ├── base.py                # Base scraper class
│   └── oversight_gov.py       # Oversight.gov scraper
├── llm/
│   ├── __init__.py
│   ├── client.py              # OpenAI client wrapper
│   ├── filter.py              # Newsworthy filter LLM
│   └── summary.py             # Post generation LLM
├── bot/
│   ├── __init__.py
│   ├── bluesky_poster.py      # Bluesky posting logic
│   └── post_reports.py        # Main posting script
├── web/
│   ├── build.py               # Static site generator
│   ├── templates/
│   │   └── index.html.template
│   └── static/
│       ├── styles.css
│       └── script.js
├── tests/
│   ├── test_scraper.py
│   ├── test_llm.py
│   └── test_database.py
├── docs/ (generated)          # GitHub Pages output
├── .env.example               # Template for environment variables
├── .env                       # Actual secrets (gitignored)
├── .gitignore
├── requirements.txt
├── run_daily.py               # Main pipeline script
└── README.md
```

---

## Key Design Decisions

### 1. SQLite for Simplicity
- Committed to git for zero-ops hosting
- Perfect for read-heavy workload (5-10 writes/day)
- Easy to query and backup

### 2. Two-Stage LLM Pipeline
- **Keyword pre-filter** (free, fast) → reduces LLM calls by 70%
- **LLM filter** (cheap, accurate) → 100 reports/day = $0.30/month
- **LLM summary** (creative) → 10 posts/day = $0.05/month

### 3. GitHub Actions for Hosting
- Free tier sufficient
- No server maintenance
- Built-in secrets management
- Easy monitoring via logs

### 4. Static Website
- GitHub Pages (free)
- No backend needed
- RSS feeds for subscribers
- Fast, cacheable

---

## Development Phases

### ✅ Phase 0: Foundation (Current)
- [x] Project planning documents
- [ ] Repository setup
- [ ] Basic file structure
- [ ] Requirements installation

### ⏳ Phase 1: Database & Scraper (Week 1)
**Goal:** Store scraped reports in database

**Tasks:**
1. Create `database/schema.sql` with full schema from spec
2. Implement `database/db.py` with CRUD operations
3. Build `scrapers/base.py` with rate limiting and error handling
4. Implement `scrapers/oversight_gov.py` to scrape Oversight.gov
5. Add keyword pre-filtering logic
6. Test scraper with dry-run mode

**Success Criteria:**
- Can scrape 10-20 recent reports
- Stored in SQLite with all fields
- Keyword filter reduces to ~40% of reports

### ⏳ Phase 2: LLM Filtering (Week 1-2)
**Goal:** LLM determines newsworthiness

**Tasks:**
1. Set up OpenAI client in `llm/client.py`
2. Implement filter prompt in `llm/filter.py`
3. Test filtering with 10+ real reports
4. Tune prompt based on false positives/negatives
5. Add error handling and retries
6. Log decisions for review

**Success Criteria:**
- 90%+ accuracy on newsworthy detection
- <100ms average response time
- Cost stays under $0.01/day for testing

### ⏳ Phase 3: LLM Summarization (Week 2)
**Goal:** Generate engaging Bluesky posts

**Tasks:**
1. Implement summary prompt in `llm/summary.py`
2. Format posts with emoji, hashtags, link
3. Validate post length (<300 chars)
4. Test with filtered reports from Phase 2
5. Ensure posts are compelling and accurate

**Success Criteria:**
- Posts are under 300 characters
- Plain English (no jargon)
- Engaging and scannable
- Include key details ($ amount, criminal status)

### ⏳ Phase 4: Bluesky Integration (Week 2-3)
**Goal:** Auto-post to Bluesky

**Tasks:**
1. Set up Bluesky account for bot
2. Implement `bot/bluesky_poster.py` with atproto
3. Create `bot/post_reports.py` with posting logic
4. Add time distribution (spread posts throughout day)
5. Implement dry-run mode
6. Test actual posting

**Success Criteria:**
- Posts successfully to Bluesky
- Proper error handling
- Posts spread across 4-6 hours
- Dry-run mode works

### ⏳ Phase 5: Automation (Week 3)
**Goal:** Daily automated workflow

**Tasks:**
1. Create `run_daily.py` main pipeline
2. Set up `.github/workflows/daily.yml`
3. Configure GitHub Secrets
4. Test workflow manually
5. Schedule daily run (8 AM ET)
6. Monitor first week of runs

**Success Criteria:**
- Runs successfully every day
- No manual intervention needed
- Costs stay under $0.10/day
- 5-10 posts per day

### ⏳ Phase 6: Website (Week 3-4)
**Goal:** Public-facing website

**Tasks:**
1. Create `web/build.py` static generator
2. Design HTML template with Bootstrap
3. Add filtering by agency, type, date
4. Generate RSS feeds
5. Create JSON API endpoints
6. Enable GitHub Pages
7. Test site locally

**Success Criteria:**
- Clean, mobile-friendly design
- Filter/search works
- RSS feed valid
- Updates automatically

### ⏳ Phase 7: Polish & Launch (Week 4)
**Goal:** Public launch

**Tasks:**
1. Monitor quality for 1 week
2. Tune LLM prompts based on results
3. Write comprehensive README
4. Set up bot profile on Bluesky
5. Soft launch announcement
6. Gather feedback

**Success Criteria:**
- High-quality posts
- No errors in logs
- Positive feedback
- Growing follower count

---

## Key Files to Implement

### 1. database/schema.sql
```sql
-- Core tables: ig_reports, bot_posts, agencies
-- See IG_REPORTS_BOT_SPEC.md for complete schema
```

### 2. database/db.py
**Functions needed:**
- `get_connection()` - Return SQLite connection
- `initialize_database()` - Create tables from schema
- `upsert_report()` - Insert or update report
- `get_unfiltered_reports()` - Reports needing LLM filter
- `get_unposted_reports()` - Filtered reports ready to post
- `mark_filtered()` - Update filter results
- `mark_posted()` - Mark as posted to Bluesky

### 3. scrapers/oversight_gov.py
**Main functions:**
- `scrape_recent_reports(days_back=1)` - Fetch new reports
- `parse_report_card(element)` - Extract fields from HTML
- `has_interesting_keywords(report)` - Pre-filter check

### 4. llm/filter.py
**Core logic:**
- Use `FILTER_PROMPT_TEMPLATE` from LLM_INTEGRATION.md
- Return JSON: `{newsworthy, score, reason, dollar_amount, criminal, topics}`
- Handle errors gracefully

### 5. llm/summary.py
**Core logic:**
- Use `SUMMARY_PROMPT_TEMPLATE` from LLM_INTEGRATION.md
- Generate post text (<280 chars)
- Add hashtags and link
- Final post <300 chars

### 6. run_daily.py
**Main pipeline:**
```python
def main():
    reports = scrape_recent_reports()
    for report in reports:
        if has_keywords(report):
            filter_result = filter_report(report)
            if filter_result['newsworthy']:
                post_text = generate_post(report, filter_result)
                upsert_report(report, filter_result, post_text)
```

---

## Testing Strategy

### Unit Tests
```bash
pytest tests/
```

**Coverage:**
- Database operations
- Scraper parsing
- LLM prompt formatting
- Post formatting

### Integration Tests
```bash
python -m scrapers.oversight_gov --dry-run
python run_daily.py --dry-run
python -m bot.post_reports --dry-run
```

### Manual Testing
1. Scrape 10 reports
2. Run through LLM filter
3. Review decisions in `llm_decisions.log`
4. Generate summaries
5. Verify post quality

---

## Environment Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
```bash
cp .env.example .env
# Edit .env with real values:
# - OPENAI_API_KEY
# - BLUESKY_HANDLE
# - BLUESKY_APP_PASSWORD
```

### 4. Initialize Database
```bash
python -m database.db
sqlite3 database/ig_reports.db ".schema"  # Verify
```

---

## Coding Guidelines

### Python Style
- Follow PEP 8
- Type hints where helpful
- Docstrings for all functions
- Max line length: 100 chars

### Error Handling
- Use try/except blocks
- Log errors with context
- Graceful degradation
- Never fail silently

### Configuration
- All secrets in .env
- All constants at top of file
- Use dataclasses for structured data

### Testing
- Test edge cases
- Mock external APIs
- Use fixtures for test data
- Aim for 80%+ coverage

---

## Common Development Tasks

### Run Full Pipeline Locally
```bash
# Dry run (no posting or database writes)
python run_daily.py --dry-run

# Actual run
python run_daily.py
```

### Test Scraper
```bash
python -m scrapers.oversight_gov --dry-run
```

### Test LLM Filter
```bash
python -m llm.filter  # Should have test cases
```

### Test Bluesky Posting
```bash
python -m bot.post_reports --dry-run
```

### Build Website Locally
```bash
python -m web.build
open docs/index.html
```

### Check Database
```bash
sqlite3 database/ig_reports.db

# Useful queries:
SELECT COUNT(*) FROM ig_reports;
SELECT COUNT(*) FROM ig_reports WHERE passed_llm_filter = 1;
SELECT COUNT(*) FROM ig_reports WHERE posted = 1;
SELECT * FROM ig_reports WHERE newsworthy_score >= 8 LIMIT 5;
```

### Monitor Costs
```bash
cat llm_usage.log | python -c "
import sys, json
total = sum(float(json.loads(line)['cost']) for line in sys.stdin)
print(f'Total cost: ${total:.2f}')
"
```

---

## Debugging Tips

### Scraper Issues
- Check HTML structure hasn't changed
- Verify User-Agent string
- Test with curl first
- Add verbose logging

### LLM Issues
- Check `llm_decisions.log` for patterns
- Test prompts in ChatGPT first
- Verify JSON parsing
- Check token limits

### Database Issues
- Use sqlite3 CLI to inspect
- Check indexes are created
- Verify foreign keys
- Look for locking issues

### GitHub Actions Issues
- Check workflow logs
- Verify secrets are set
- Test locally first
- Check Python version matches

---

## Documentation to Reference

1. **IG_REPORTS_BOT_SPEC.md** - Complete specification
2. **IG_BOT_QUICKSTART.md** - Step-by-step implementation guide
3. **LLM_INTEGRATION.md** - LLM prompts and best practices

---

## Success Metrics

### Technical
- ✅ Scraper runs daily without errors
- ✅ LLM filter accuracy >90%
- ✅ Posts stay under 300 chars
- ✅ Website loads in <1 second
- ✅ Monthly cost stays under $3

### Product
- 🎯 5-10 quality posts per day
- 🎯 500+ Bluesky followers in month 1
- 🎯 1000+ website visits in month 1
- 🎯 Cited by journalists
- 🎯 Positive user feedback

---

## Getting Started (For Claude)

When starting work on this project:

1. **Read the spec** - Start with IG_REPORTS_BOT_SPEC.md
2. **Check current phase** - See which phase needs work above
3. **Create branch** - Work on feature branches
4. **Test first** - Always run tests before committing
5. **Document** - Update this file with progress
6. **Ask questions** - Better to clarify than assume

### Current Priority Tasks

**Phase 1 (Database & Scraper):**
1. Create database schema and db.py
2. Build oversight.gov scraper
3. Add keyword filtering
4. Test with dry-run mode

Start with these and we'll move to LLM integration once scraping works reliably.

---

## Contact & Resources

- **Oversight.gov**: https://www.oversight.gov/reports/federal
- **OpenAI Docs**: https://platform.openai.com/docs
- **Bluesky (atproto)**: https://docs.bsky.app/
- **GitHub Actions**: https://docs.github.com/en/actions

---

**Remember:** This bot makes government accountability accessible. Quality over quantity. Every post should be genuinely newsworthy. 🛡️✨
