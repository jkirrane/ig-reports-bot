# Quick Start Guide for Claude

**Welcome! You're helping build an automated bot that posts Inspector General reports to Bluesky.**

## 🎯 What You're Building

An automated system that:
1. Scrapes Oversight.gov daily for IG reports
2. Uses GPT-4o-mini to filter for newsworthy content (fraud, waste, abuse)
3. Generates plain-English summaries
4. Auto-posts to Bluesky
5. Maintains a public website

**Monthly cost:** ~$2 (OpenAI API only)  
**Tech stack:** Python, SQLite, OpenAI, Bluesky (atproto), GitHub Actions

---

## 📚 Essential Reading (In Order)

1. **[agents.md](agents.md)** - Your main development guide (READ FIRST!)
   - Project architecture
   - Development phases
   - Key files to implement
   - Coding guidelines

2. **[tasks.md](tasks.md)** - Current task breakdown
   - Phase-by-phase checklist
   - Priority tasks
   - Success criteria

3. **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development workflow
   - How to test
   - Debugging tips
   - Code quality standards

4. **Project Specs** (in `/mnt/project/`):
   - `IG_REPORTS_BOT_SPEC.md` - Complete specification
   - `IG_BOT_QUICKSTART.md` - Step-by-step implementation
   - `LLM_INTEGRATION.md` - LLM prompts and best practices

---

## 🚀 Where We Are Now

**Current Phase:** Phase 1 - Database & Scraper

**Next Tasks:**
1. Create `database/schema.sql` (see spec for full schema)
2. Implement `database/db.py` (CRUD operations)
3. Build `scrapers/oversight_gov.py` (scrape Oversight.gov)
4. Test scraper with `--dry-run` mode

---

## 📁 Key Files You'll Create

### Phase 1 (Current)
- `database/schema.sql` - Database schema with ig_reports, bot_posts, agencies tables
- `database/db.py` - Database operations (get_connection, upsert_report, etc.)
- `scrapers/base.py` - Base scraper class with rate limiting
- `scrapers/oversight_gov.py` - Oversight.gov scraper with keyword filtering
- `run_daily.py` - Main pipeline script

### Phase 2 (Next)
- `llm/client.py` - OpenAI client wrapper
- `llm/filter.py` - Newsworthy filter using GPT-4o-mini
- `llm/summary.py` - Post generation with LLM

### Phase 3 (Later)
- `bot/bluesky_poster.py` - Bluesky integration
- `bot/post_reports.py` - Posting logic with time distribution
- `web/build.py` - Static site generator
- `.github/workflows/daily.yml` - GitHub Actions automation

---

## 🎯 Your First Task

**Create the database schema:**

1. Read the schema definition in `IG_REPORTS_BOT_SPEC.md` (search for "Database Schema")
2. Create `database/schema.sql` with:
   - `ig_reports` table (all fields from spec)
   - `bot_posts` table
   - `agencies` table
   - All indexes

3. Create `database/db.py` with these functions:
   - `get_connection()` - Return SQLite connection
   - `initialize_database()` - Create tables from schema.sql
   - `upsert_report()` - Insert or update report
   - `get_unfiltered_reports()` - Reports needing LLM filter
   - `get_unposted_reports()` - Filtered reports ready to post
   - `mark_filtered()` - Update filter results
   - `mark_posted()` - Mark as posted

4. Test:
   ```bash
   python -m database.db
   sqlite3 database/ig_reports.db ".schema"
   ```

---

## 🧪 How to Test Your Work

### Database
```bash
python -m database.db  # Initialize
sqlite3 database/ig_reports.db ".schema"  # Verify
```

### Scraper (once built)
```bash
python -m scrapers.oversight_gov --dry-run
```

### Full Pipeline (once built)
```bash
python run_daily.py --dry-run
```

### Unit Tests (as you go)
```bash
pytest tests/
```

---

## 💡 Development Tips

### 1. Always Use Dry-Run First
```bash
# Test without side effects
python run_daily.py --dry-run
python -m bot.post_reports --dry-run
```

### 2. Check Examples in Spec Files
The spec files have detailed examples for:
- Database schema
- LLM prompts
- Post formats
- Error handling

### 3. Follow the Phases
Don't skip ahead! Each phase builds on the previous one:
- Phase 1: Database + Scraper
- Phase 2: LLM Filtering
- Phase 3: LLM Summarization
- Phase 4: Bluesky Posting
- Phase 5: Automation
- Phase 6: Website

### 4. Log Everything During Development
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info(f"Scraped {len(reports)} reports")
logger.debug(f"Report: {report}")
```

### 5. Cost Awareness
- Keep LLM testing under $0.10/day
- Use keyword pre-filter to reduce LLM calls
- Monitor `llm_usage.log`

---

## 🐛 Common Issues

### "Module not found"
```bash
# Make sure you're in venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### "Database locked"
```python
# Add timeout to connection
conn = sqlite3.connect('database/ig_reports.db', timeout=10.0)
```

### "API key not found"
```bash
# Check .env file exists and has correct key
cat .env | grep OPENAI_API_KEY
```

---

## 📖 Reference Hierarchy

When you need information:

1. **Architecture questions** → `agents.md`
2. **What to work on next** → `tasks.md`
3. **How to test/debug** → `DEVELOPMENT.md`
4. **Detailed requirements** → Spec files in `/mnt/project/`

---

## ✅ Success Criteria for Phase 1

You've completed Phase 1 when:
- [x] Database schema created and tested
- [x] Can scrape 10-20 recent reports from Oversight.gov
- [x] Keyword filter reduces reports by ~60%
- [x] All fields extracted correctly (title, agency, date, abstract, URL)
- [x] Reports stored in SQLite database
- [x] `--dry-run` mode works
- [x] No errors in logs

---

## 🎓 Learning Resources

### SQLite
- Official docs: https://www.sqlite.org/docs.html
- Python sqlite3: https://docs.python.org/3/library/sqlite3.html

### Web Scraping
- BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- requests: https://requests.readthedocs.io/

### OpenAI API
- Official docs: https://platform.openai.com/docs
- GPT-4o-mini: Cost-effective model for this use case

### Bluesky (atproto)
- atproto docs: https://docs.bsky.app/
- Python SDK: https://github.com/MarshalX/atproto

---

## 🎯 Remember

- **Quality over quantity** - Every post should be genuinely newsworthy
- **Test everything** - Use dry-run modes extensively
- **Cost awareness** - Keep LLM usage low during testing
- **Document as you go** - Update docs when you make changes
- **Ask questions** - Better to clarify than assume

---

**Ready to make government accountability accessible!** 🛡️✨

**Next step:** Read [`agents.md`](agents.md) thoroughly, then start on Phase 1 tasks from [`tasks.md`](tasks.md).
