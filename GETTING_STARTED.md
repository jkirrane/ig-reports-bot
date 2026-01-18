# Getting Started with IG Reports Bot

## What's Ready Now

I've built **Phases 1 & 2** of the IG Reports Bot. Here's what you can do immediately:

## 🚀 Quick Start (5 minutes)

### 1. Test the Setup
```bash
python test_setup.py
```

This validates:
- Python version
- Dependencies
- Database
- Scraper connectivity

### 2. Try the Scraper (No API Key Needed)
```bash
python -m scrapers.oversight_gov
```

This will:
- Scrape recent reports from Oversight.gov
- Show keyword filtering in action
- Display sample reports
- No database writes, no costs

**You'll see output like:**
```
📊 Scraped 47 reports
   18 passed keyword filter (38.3%)

📝 Sample reports:
- Investigation of Allegations That an EPA Employee Committed Time and...
  Agency: Environmental Protection Agency (EPA)
  Date: 2024-01-15
  Keyword filter: ✅
```

### 3. Test the Database
```bash
python -m database.db
```

This shows:
- Database statistics
- Table counts
- Current state

### 4. Use the Helper Script
```bash
./dev.sh help
```

Quick commands for everything:
- `./dev.sh test-scraper` - Test scraper
- `./dev.sh db-stats` - View database stats
- `./dev.sh dry-run` - Test full pipeline (no LLM calls)

## 🤖 With OpenAI API Key

Once you add your OpenAI API key to `.env`, you can:

### 1. Configure Environment
```bash
cp .env.example .env
# Edit .env and add:
# OPENAI_API_KEY=sk-proj-your-key-here
```

### 2. Test LLM Filter
```bash
python -m llm.filter
```

This will:
- Test the newsworthiness filter
- Show a sample evaluation
- Display cost (should be ~$0.001)

### 3. Test Summary Generator
```bash
python -m llm.summary
```

This will:
- Generate a sample Bluesky post
- Show character count
- Display cost (should be ~$0.002)

### 4. Run Full Pipeline (Dry Run)
```bash
python run_daily.py --dry-run --days-back 2
```

This will:
- Scrape 2 days of reports
- Filter with keywords
- Evaluate with LLM
- Generate summaries
- Show what would be saved
- **NO database writes**
- Cost: ~$0.10-0.30

### 5. Run Full Pipeline (Production)
```bash
python run_daily.py --days-back 1
```

This will:
- Do everything above
- Save to database
- Track costs
- Create logs

## 📊 Monitoring & Analysis

### View Reports in Database
```bash
sqlite3 database/ig_reports.db

-- See all reports
SELECT COUNT(*) FROM ig_reports;

-- See newsworthy reports
SELECT title, newsworthy_score, agency_name 
FROM ig_reports 
WHERE passed_llm_filter = 1 
ORDER BY newsworthy_score DESC 
LIMIT 10;

-- See generated posts
SELECT title, post_text 
FROM ig_reports 
WHERE post_text IS NOT NULL 
LIMIT 5;
```

### Check Costs
```bash
./dev.sh costs
# OR
python -c "from llm import get_total_cost; print(f'Total: \${get_total_cost():.4f}')"
```

### Review LLM Decisions
```bash
./dev.sh decisions
# OR
cat llm_decisions.log | jq
```

### View Logs
```bash
./dev.sh logs
# OR
tail -f pipeline.log
```

## 🧪 Testing Workflow

Here's a recommended testing sequence:

```bash
# 1. Validate setup
./dev.sh test-setup

# 2. Test scraper (free, no API needed)
./dev.sh test-scraper

# 3. Initialize database
./dev.sh init-db

# 4. Run dry run (no LLM, no costs)
python run_daily.py --dry-run --skip-filtering --skip-summary --days-back 1

# 5. Once you have API key, test LLM components
./dev.sh test-filter
./dev.sh test-summary

# 6. Run full pipeline dry run (costs ~$0.10)
./dev.sh dry-run

# 7. Run production pipeline (costs ~$0.30)
./dev.sh run

# 8. Check results
./dev.sh db-stats
./dev.sh costs
```

## 📝 What Each File Does

### Core Scripts
- `run_daily.py` - Main pipeline (scrape → filter → summarize)
- `test_setup.py` - Validate installation
- `dev.sh` - Helper script for common commands

### Database
- `database/schema.sql` - Database structure
- `database/db.py` - CRUD operations
- `database/ig_reports.db` - SQLite database (created on first run)

### Scrapers
- `scrapers/base.py` - Base scraper with rate limiting
- `scrapers/oversight_gov.py` - Oversight.gov scraper

### LLM
- `llm/client.py` - OpenAI wrapper with cost tracking
- `llm/filter.py` - Newsworthiness evaluation
- `llm/summary.py` - Post generation

## 🎯 Example Output

When you run the full pipeline, you'll see:

```
============================================================
IG REPORTS BOT - Daily Pipeline
Mode: PRODUCTION
Days back: 1
============================================================

[2024-01-18 01:30:00] Starting scraping phase...
[2024-01-18 01:30:02] Found 52 reports
[2024-01-18 01:30:02]   19 passed keyword filter (36.5%)
[2024-01-18 01:30:02] ✅ Saved 52/52 reports to database

[2024-01-18 01:30:03] Starting LLM filtering phase...
[2024-01-18 01:30:03] Filtering 19 reports with LLM...
[2024-01-18 01:30:05] [1/19] Filtering: Investigation Substantiates...
[2024-01-18 01:30:06]   ✅ NEWSWORTHY (score: 8/10): Sexual harassment case
[2024-01-18 01:30:07] [2/19] Filtering: Audit of IT Security Controls...
[2024-01-18 01:30:08]   ❌ Not newsworthy (score: 4/10): Routine audit
...
[2024-01-18 01:31:00] ✅ Filtered 19 reports: 6 newsworthy, 13 not newsworthy

[2024-01-18 01:31:01] Starting summary generation phase...
[2024-01-18 01:31:01] Generating summaries for 6 reports...
[2024-01-18 01:31:02] [1/6] Generating summary: Investigation Substantiates...
[2024-01-18 01:31:03]   ✅ Generated (248 chars): VA Chief of Staff substantiated for...
...

============================================================
PIPELINE COMPLETE
============================================================
Database stats:
  Total reports: 52
  Passed keyword filter: 19
  Passed LLM filter: 6
  Posted: 0
  Pending posts: 6
  Total LLM cost: $0.2847
```

## 🎉 What You've Got

**Working Right Now:**
- ✅ Automated scraping from Oversight.gov
- ✅ Intelligent keyword filtering
- ✅ LLM-based newsworthiness evaluation
- ✅ Automatic post generation
- ✅ Database storage
- ✅ Cost tracking
- ✅ Comprehensive logging

**Still To Build:**
- 🚧 Bluesky posting integration
- 🚧 GitHub Actions automation
- 🚧 Static website (optional)

**The hard part is done!** The core pipeline is working and ready to find newsworthy reports.

## 💡 Tips

1. **Start with dry runs** - Test without API costs using `--dry-run`
2. **Check costs frequently** - Use `./dev.sh costs` to monitor spending
3. **Review decisions** - Use `./dev.sh decisions` to see what LLM filtered
4. **Adjust prompts** - Edit `llm/filter.py` and `llm/summary.py` to tune behavior
5. **Monitor logs** - Use `./dev.sh logs` to troubleshoot issues

## 🆘 Troubleshooting

**"OpenAI SDK not installed"**
```bash
pip install openai python-dotenv
```

**"OPENAI_API_KEY not found"**
```bash
cp .env.example .env
# Edit .env with your key
```

**"Database locked"**
```bash
# Close any SQLite shells, then:
./dev.sh db-reset  # Warning: deletes data!
```

**"No reports found"**
- Oversight.gov might be down
- Try different `--days-back` value
- Check `pipeline.log` for errors

## 📚 Learn More

- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Full technical details
- [IG_REPORTS_BOT_SPEC.md](IG_REPORTS_BOT_SPEC.md) - Original specification
- [tasks.md](tasks.md) - Remaining tasks and roadmap

---

**Ready to start?** Run `./dev.sh test-setup` and let's go! 🚀
