# IG Reports Bot - Task Breakdown

## Current Phase: Phase 1 - Database & Scraper

---

## Phase 0: Foundation ✅

### 0.1 Project Setup
- [x] Create project planning documents
- [ ] Initialize Git repository
- [ ] Create directory structure
- [ ] Set up .gitignore
- [ ] Create requirements.txt
- [ ] Create .env.example

### 0.2 Documentation
- [x] Write agents.md
- [x] Write .clinerules
- [x] Create tasks.md
- [ ] Write initial README.md

---

## Phase 1: Database & Scraper (Priority: HIGH)

### 1.1 Database Schema
**Files:** `database/schema.sql`, `database/db.py`

- [ ] Create `database/schema.sql`
  - [ ] Define `ig_reports` table with all fields
  - [ ] Define `bot_posts` table
  - [ ] Define `agencies` table
  - [ ] Add all indexes (published_date, agency_id, posted, newsworthy)
  - [ ] Add foreign key constraints

- [ ] Create `database/db.py`
  - [ ] `get_connection()` - Return SQLite connection with row factory
  - [ ] `initialize_database()` - Create tables from schema.sql
  - [ ] `upsert_report()` - Insert or update report
  - [ ] `get_unfiltered_reports()` - Get reports needing LLM filter
  - [ ] `get_unposted_reports()` - Get filtered reports ready to post
  - [ ] `mark_filtered()` - Update filter results
  - [ ] `mark_posted()` - Mark report as posted with timestamp
  - [ ] `get_report_by_id()` - Fetch single report
  - [ ] `get_recent_reports()` - Get reports from last N days

**Testing:**
```bash
python -m database.db  # Should create ig_reports.db
sqlite3 database/ig_reports.db ".schema"  # Verify structure
```

**Success Criteria:**
- [x] All tables created correctly
- [x] Indexes in place
- [x] All CRUD operations work
- [x] No SQL injection vulnerabilities

### 1.2 Base Scraper
**File:** `scrapers/base.py`

- [ ] Create `BaseScraper` class
  - [ ] `fetch_page(url)` - HTTP GET with proper headers
  - [ ] Rate limiting (1-2 seconds between requests)
  - [ ] User-Agent rotation
  - [ ] Error handling (timeouts, 404s, 500s)
  - [ ] Retry logic (3 attempts)
  - [ ] Logging integration

**Testing:**
```python
from scrapers.base import BaseScraper
scraper = BaseScraper()
html = scraper.fetch_page('https://www.oversight.gov')
assert html is not None
```

**Success Criteria:**
- [x] Respectful rate limiting
- [x] Handles network errors gracefully
- [x] Logs requests
- [x] Returns None on failure

### 1.3 Oversight.gov Scraper
**File:** `scrapers/oversight_gov.py`

- [ ] Research Oversight.gov structure
  - [ ] Identify report listing page
  - [ ] Find report detail elements
  - [ ] Check for pagination
  - [ ] Look for date filters
  - [ ] Document HTML structure

- [ ] Create `OversightGovScraper` class
  - [ ] `scrape_recent_reports(days_back=1)` - Main entry point
  - [ ] `parse_report_card(element)` - Extract fields from HTML element
  - [ ] `extract_title(element)` - Get report title
  - [ ] `extract_agency(element)` - Get agency name and ID
  - [ ] `extract_date(element)` - Parse published date
  - [ ] `extract_abstract(element)` - Get summary text
  - [ ] `extract_url(element)` - Get report link
  - [ ] `extract_report_type(element)` - Get type (Audit, Investigation, etc.)

- [ ] Add keyword pre-filtering
  - [ ] `has_interesting_keywords(report)` - Quick filter
  - [ ] Define keyword list (fraud, criminal, waste, etc.)
  - [ ] Case-insensitive matching
  - [ ] Check title + abstract

- [ ] Add CLI interface
  - [ ] `--dry-run` flag (print, don't save)
  - [ ] `--days-back N` argument
  - [ ] `--verbose` flag for debugging

**Testing:**
```bash
python -m scrapers.oversight_gov --dry-run --days-back 7
# Should print 10-20 reports with all fields
```

**Success Criteria:**
- [x] Scrapes 10-20 recent reports
- [x] All fields extracted correctly
- [x] Keyword filter reduces by ~60%
- [x] Handles missing fields gracefully
- [x] Dry-run mode works

### 1.4 Integration
**File:** `run_daily.py` (Phase 1 version)

- [ ] Create basic pipeline
  - [ ] Import scraper and database modules
  - [ ] Scrape recent reports
  - [ ] Apply keyword filter
  - [ ] Store in database (without LLM fields yet)
  - [ ] Print summary statistics
  - [ ] Support --dry-run flag

**Testing:**
```bash
python run_daily.py --dry-run
# Should show:
# - N reports scraped
# - M passed keyword filter
# - Would store in database
```

**Success Criteria:**
- [x] End-to-end scraping works
- [x] Reports stored in database
- [x] No errors or crashes
- [x] Runs in under 1 minute

---

## Phase 2: LLM Filtering (Priority: MEDIUM)

### 2.1 OpenAI Client Setup
**File:** `llm/client.py`

- [ ] Create OpenAI client wrapper
  - [ ] Load API key from environment
  - [ ] `call_gpt()` function with parameters
  - [ ] Error handling (API errors, rate limits, timeouts)
  - [ ] Retry logic with exponential backoff
  - [ ] Token usage logging
  - [ ] Cost tracking

- [ ] Add usage monitoring
  - [ ] `log_usage()` - Write to llm_usage.log
  - [ ] `check_monthly_cost()` - Calculate total from logs
  - [ ] Alert if cost exceeds threshold

**Testing:**
```python
from llm.client import call_gpt
response = call_gpt("Say hello in JSON", response_format={"type": "json_object"})
print(response)  # Should get valid JSON
```

**Success Criteria:**
- [x] API calls work reliably
- [x] Retries on failure
- [x] Logs token usage
- [x] Calculates costs correctly

### 2.2 Filter LLM
**File:** `llm/filter.py`

- [ ] Implement filter prompt
  - [ ] Use `FILTER_PROMPT_TEMPLATE` from LLM_INTEGRATION.md
  - [ ] Format with report fields
  - [ ] Request JSON response format

- [ ] Create `filter_report()` function
  - [ ] Build prompt from template
  - [ ] Call GPT-4o-mini
  - [ ] Parse JSON response
  - [ ] Validate response fields
  - [ ] Handle errors with fallback

- [ ] Add validation
  - [ ] Check required fields (newsworthy, score, reason)
  - [ ] Validate score range (1-10)
  - [ ] Validate dollar_amount type
  - [ ] Validate topics array

**Testing:**
```python
report = {
    'title': 'DOJ: Investigation of Prison Fraud',
    'agency_name': 'Department of Justice',
    'abstract': 'Criminal charges filed...'
}
result = filter_report(report)
assert result['newsworthy'] in [True, False]
assert 1 <= result['score'] <= 10
```

**Success Criteria:**
- [x] Correctly identifies newsworthy reports
- [x] Returns valid JSON
- [x] <90% accuracy on test set
- [x] Response time <2 seconds
- [x] Cost <$0.01 per 10 reports

### 2.3 Filter Testing & Tuning
**File:** `tests/test_llm_filter.py`

- [ ] Create test dataset
  - [ ] 10 clearly newsworthy reports (fraud, criminal, waste)
  - [ ] 10 clearly not newsworthy (routine audits)
  - [ ] 5 edge cases
  - [ ] Label ground truth

- [ ] Test filter accuracy
  - [ ] Run all test cases through filter
  - [ ] Calculate accuracy, precision, recall
  - [ ] Identify false positives/negatives
  - [ ] Document error patterns

- [ ] Tune prompt based on results
  - [ ] Adjust criteria if needed
  - [ ] Add more examples
  - [ ] Refine instructions
  - [ ] Re-test until 90%+ accuracy

**Success Criteria:**
- [x] Test suite runs automatically
- [x] 90%+ accuracy achieved
- [x] Documented test cases
- [x] Prompt tuning process documented

---

## Phase 3: LLM Summarization (Priority: MEDIUM)

### 3.1 Summary LLM
**File:** `llm/summary.py`

- [ ] Implement summary prompt
  - [ ] Use `SUMMARY_PROMPT_TEMPLATE` from LLM_INTEGRATION.md
  - [ ] Include filter results in context
  - [ ] Request plain text response

- [ ] Create `generate_post()` function
  - [ ] Format dollar amounts nicely
  - [ ] Choose appropriate emoji
  - [ ] Generate engaging summary
  - [ ] Keep under 280 characters
  - [ ] Handle errors with retry

- [ ] Create `format_complete_post()` function
  - [ ] Add report URL
  - [ ] Generate hashtags from agency + topics
  - [ ] Keep final post under 300 chars
  - [ ] Validate final output

**Testing:**
```python
from llm.summary import generate_post, format_complete_post
post_text = generate_post(report, filter_result)
complete = format_complete_post(post_text, report, filter_result)
print(complete)
assert len(complete) <= 300
```

**Success Criteria:**
- [x] Posts are engaging and scannable
- [x] All posts <300 characters
- [x] Appropriate emoji selection
- [x] Plain English (no jargon)
- [x] Includes key details

### 3.2 Summary Testing
**File:** `tests/test_summary.py`

- [ ] Test with filtered reports
  - [ ] Generate 20 different summaries
  - [ ] Manually review quality
  - [ ] Check length constraints
  - [ ] Verify hashtag generation
  - [ ] Test emoji selection

- [ ] Edge case testing
  - [ ] Very long titles
  - [ ] Multiple dollar amounts
  - [ ] No abstract
  - [ ] Complex agency names
  - [ ] Special characters

**Success Criteria:**
- [x] All tests pass
- [x] High-quality posts
- [x] No formatting issues
- [x] Consistent style

### 3.3 Update Pipeline
**File:** `run_daily.py` (updated)

- [ ] Add LLM processing to pipeline
  - [ ] Filter scraped reports with LLM
  - [ ] Generate summaries for newsworthy ones
  - [ ] Store filter results in database
  - [ ] Store generated posts in database
  - [ ] Log all LLM decisions

**Success Criteria:**
- [x] Full pipeline runs without errors
- [x] LLM results stored correctly
- [x] Decisions logged for review
- [x] Cost tracking works

---

## Phase 4: Bluesky Integration (Priority: MEDIUM)

### 4.1 Bluesky Poster
**File:** `bot/bluesky_poster.py`

- [ ] Set up atproto client
  - [ ] Create `BlueskyPoster` class
  - [ ] `login()` - Authenticate with handle/password
  - [ ] `post(text)` - Send post to Bluesky
  - [ ] Error handling
  - [ ] Rate limiting

- [ ] Add connection management
  - [ ] Session persistence
  - [ ] Auto-reconnect on failure
  - [ ] Graceful error messages

**Testing:**
```python
from bot.bluesky_poster import BlueskyPoster
poster = BlueskyPoster(handle, password)
poster.post("🧪 Test post - please ignore!")
```

**Success Criteria:**
- [x] Can authenticate successfully
- [x] Can post text
- [x] Handles errors gracefully
- [x] Rate limiting works

### 4.2 Posting Logic
**File:** `bot/post_reports.py`

- [ ] Create main posting script
  - [ ] `post_newsworthy_reports()` - Main function
  - [ ] Get unposted reports from database
  - [ ] Post each report with time distribution
  - [ ] Mark as posted in database
  - [ ] Log posting activity

- [ ] Add time distribution
  - [ ] Define posting times (9am, 12pm, 3pm, 6pm ET)
  - [ ] Spread reports across times
  - [ ] Add randomness (+/- 15 minutes)
  - [ ] Respect rate limits

- [ ] Add CLI interface
  - [ ] `--dry-run` flag
  - [ ] `--limit N` posts
  - [ ] `--verbose` logging

**Testing:**
```bash
python -m bot.post_reports --dry-run
# Should show what would be posted
```

**Success Criteria:**
- [x] Posts spread throughout day
- [x] All posts successful
- [x] Database updated correctly
- [x] Dry-run mode works

---

## Phase 5: Automation (Priority: HIGH)

### 5.1 GitHub Actions Workflow
**File:** `.github/workflows/daily.yml`

- [ ] Create workflow file
  - [ ] Define schedule (daily at 8 AM ET / 1 PM UTC)
  - [ ] Add manual trigger
  - [ ] Set up Python 3.11
  - [ ] Install dependencies
  - [ ] Run scraper + filter
  - [ ] Run posting (staggered)
  - [ ] Commit database changes

- [ ] Configure secrets
  - [ ] Add OPENAI_API_KEY
  - [ ] Add BLUESKY_HANDLE  
  - [ ] Add BLUESKY_APP_PASSWORD
  - [ ] Document in README

**Testing:**
- [ ] Test workflow manually
- [ ] Verify secrets work
- [ ] Check logs
- [ ] Confirm database commits

**Success Criteria:**
- [x] Workflow runs daily
- [x] No manual intervention needed
- [x] Secrets secure
- [x] Logs viewable

### 5.2 Monitoring
**File:** `monitoring/check_health.py` (optional)

- [ ] Daily health checks
  - [ ] Verify database not corrupted
  - [ ] Check recent posts
  - [ ] Monitor LLM costs
  - [ ] Check error logs

- [ ] Alert on issues
  - [ ] Create GitHub issue on failure
  - [ ] Email notification (optional)

**Success Criteria:**
- [x] Automated health checks
- [x] Issues caught quickly
- [x] Cost monitoring works

---

## Phase 6: Website (Priority: LOW)

### 6.1 Static Site Generator
**File:** `web/build.py`

- [ ] Create site builder
  - [ ] Read reports from database
  - [ ] Generate index.html
  - [ ] Generate agency pages
  - [ ] Generate RSS feed
  - [ ] Generate JSON API
  - [ ] Copy static assets

- [ ] Add filtering logic
  - [ ] Filter by agency
  - [ ] Filter by type
  - [ ] Filter by date range
  - [ ] Sort by score, date, amount

**Success Criteria:**
- [x] Site generates successfully
- [x] All pages linked correctly
- [x] Filtering works
- [x] RSS valid

### 6.2 Templates & Styling
**Files:** `web/templates/`, `web/static/`

- [ ] Create HTML template
  - [ ] Responsive layout
  - [ ] Report cards
  - [ ] Filter controls
  - [ ] Search box
  - [ ] Footer with links

- [ ] Create CSS
  - [ ] Clean, modern design
  - [ ] Mobile-friendly
  - [ ] Agency color coding
  - [ ] Accessibility (WCAG)

- [ ] Create JavaScript
  - [ ] Client-side filtering
  - [ ] Search functionality
  - [ ] Sort controls

**Success Criteria:**
- [x] Clean design
- [x] Mobile responsive
- [x] Fast loading
- [x] Accessible

### 6.3 GitHub Pages
**Configuration**

- [ ] Enable GitHub Pages
  - [ ] Set source to /docs folder
  - [ ] Custom domain (optional)
  - [ ] HTTPS enabled

- [ ] Add to workflow
  - [ ] Generate site after posting
  - [ ] Commit to /docs
  - [ ] Push to main branch

**Success Criteria:**
- [x] Site live and accessible
- [x] Updates automatically
- [x] HTTPS working

---

## Phase 7: Polish & Launch (Priority: MEDIUM)

### 7.1 Monitoring & Tuning
- [ ] Monitor first week
  - [ ] Review all posts manually
  - [ ] Check LLM decisions
  - [ ] Monitor costs daily
  - [ ] Fix any bugs

- [ ] Tune based on results
  - [ ] Adjust filter criteria
  - [ ] Refine summary prompts
  - [ ] Optimize posting times
  - [ ] Improve keyword filter

**Success Criteria:**
- [x] High-quality posts
- [x] Costs under budget
- [x] No errors in logs
- [x] Positive feedback

### 7.2 Documentation
**File:** `README.md`

- [ ] Write comprehensive README
  - [ ] Project description
  - [ ] Link to website and bot
  - [ ] Setup instructions
  - [ ] Architecture overview
  - [ ] Credits and license

- [ ] Add badges
  - [ ] Build status
  - [ ] Python version
  - [ ] License badge

**Success Criteria:**
- [x] Clear documentation
- [x] Easy to understand
- [x] Links work

### 7.3 Bot Profile
- [ ] Set up Bluesky profile
  - [ ] Professional avatar
  - [ ] Clear bio
  - [ ] Link to website
  - [ ] Pin intro post

**Success Criteria:**
- [x] Professional appearance
- [x] Clear purpose stated
- [x] Links work

### 7.4 Launch
- [ ] Soft launch
  - [ ] Post from personal account
  - [ ] Share in civic tech communities
  - [ ] Post on Reddit (r/datasets, r/transparency)
  - [ ] Hacker News (if gains traction)

- [ ] Gather feedback
  - [ ] Monitor replies
  - [ ] Track follower growth
  - [ ] Check website analytics
  - [ ] Iterate based on feedback

**Success Criteria:**
- [x] Positive reception
- [x] Growing follower base
- [x] Clear public value
- [x] Sustainable operation

---

## Future Enhancements (Phase 8+)

### Email Alerts
- [ ] Daily digest email
- [ ] Subscribe by agency
- [ ] High-priority alerts

### Trend Analysis
- [ ] "DOD waste up 40% this quarter"
- [ ] Agency scorecards
- [ ] Historical comparisons

### Expansion
- [ ] State-level IGs
- [ ] GAO reports
- [ ] Congressional investigations

---

## Task Priority Legend

- **HIGH** - Critical path, blocks other work
- **MEDIUM** - Important but can wait
- **LOW** - Nice to have, can defer

## Task Status Legend

- [ ] Not started
- [🔄] In progress
- [âœ"] Complete
- [❌] Blocked
- [⚠️] Needs review
