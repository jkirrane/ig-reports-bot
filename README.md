# IG Reports Bot 🛡️

> **Automated bot that makes federal Inspector General reports accessible to the public**

Scrapes [Oversight.gov](https://www.oversight.gov) daily, uses AI to identify newsworthy reports on fraud, waste, and abuse, and posts them to Bluesky in plain English.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 🎯 Mission

Make government accountability accessible by automatically detecting and sharing important Inspector General findings that would otherwise go unnoticed.

**Every day, federal IGs publish dozens of reports on:**
- Multi-million dollar fraud schemes
- Criminal investigations
- Waste and mismanagement
- Agency failures
- Whistleblower findings

**But only insiders see them.** This bot fixes that.

---

## ✨ Features

- 🔍 **Smart Filtering** - AI (GPT-4o-mini) reads every report and identifies what's genuinely newsworthy
- 📝 **Plain English Summaries** - Translates bureaucratic language into scannable posts
- 🤖 **Fully Automated** - Runs daily via GitHub Actions, zero maintenance
- 🌐 **Public Website** - Browse, filter, and search all reports
- 📡 **RSS Feeds** - Subscribe by agency or topic
- 💰 **Essentially Free** - Costs ~$2/month (OpenAI API only)

---

## 🏗️ Architecture

```
Oversight.gov (50-100 daily reports)
           ↓
    Keyword Filter (reduce to ~40)
           ↓
    LLM Filter (GPT-4o-mini) → Keep 5-10 newsworthy
           ↓
    LLM Summary → Generate plain English post
           ↓
    SQLite Database
           ↓
         ┌─────┴─────┐
         ↓           ↓
    Bluesky      Website
```

**Tech Stack:**
- Python 3.11+ (scraping, LLM, bot logic)
- SQLite (committed to git for zero-ops)
- OpenAI GPT-4o-mini (filtering & summarization)
- atproto (Bluesky posting)
- GitHub Actions (daily automation)
- GitHub Pages (static website hosting)

---

## 📦 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Bluesky account

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/ig-reports-bot.git
cd ig-reports-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
#   OPENAI_API_KEY=sk-proj-...
#   BLUESKY_HANDLE=your-handle.bsky.social
#   BLUESKY_APP_PASSWORD=your-app-password

# Initialize database
python -m database.db

# Test scraper (dry run)
python -m scrapers.oversight_gov --dry-run

# Run full pipeline (dry run)
python run_daily.py --dry-run

# Build website
python -m web.build --days-back 30
```

---

## 🚀 Usage

### Scrape Recent Reports

```bash
python -m scrapers.oversight_gov --days-back 7
```

### Run Full Pipeline

```bash
# Dry run (no database writes, no posting)
python run_daily.py --dry-run

# Actual run
python run_daily.py
```

### Post to Bluesky

```bash
# Dry run
python -m bot.post_reports --dry-run

# Actual posting
python -m bot.post_reports
```

### Build Website

```bash
python -m web.build --days-back 30
open docs/index.html

# Or serve locally
cd docs && python -m http.server 8000
# Visit http://localhost:8000
```

---

## 📊 Project Structure

```
ig-reports-bot/
├── agents.md              # 👈 START HERE (Claude development guide)
├── tasks.md               # Detailed task breakdown
├── DEVELOPMENT.md         # Development workflow guide
│
├── database/
│   ├── schema.sql         # Database schema
│   ├── db.py              # Database operations
│   └── ig_reports.db      # SQLite database
│
├── scrapers/
│   ├── base.py            # Base scraper with rate limiting
│   └── oversight_gov.py   # Oversight.gov scraper
│
├── llm/
│   ├── client.py          # OpenAI client wrapper
│   ├── filter.py          # Newsworthy filter
│   └── summary.py         # Post generation
│
├── bot/
│   ├── bluesky_poster.py  # Bluesky integration
│   └── post_reports.py    # Posting logic
│
├── web/
│   ├── build.py           # Static site generator
│   ├── templates/         # HTML templates
│   └── static/            # CSS, JS, images
│
├── tests/                 # Unit & integration tests
├── docs/                  # Generated website (GitHub Pages)
│
├── .github/workflows/
│   └── daily.yml          # GitHub Actions automation
│
├── run_daily.py           # Main pipeline script
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
└── README.md              # This file
```

---

## 🔧 Development

### For AI Assistants (Claude, etc.)

**Start here:** Read [`agents.md`](agents.md) - comprehensive development guide with:
- Project architecture
- Development phases
- Key design decisions
- Task breakdown
- Coding guidelines

### For Human Developers

1. Read [`DEVELOPMENT.md`](DEVELOPMENT.md) for workflow details
2. Check [`tasks.md`](tasks.md) for current priorities
3. Follow the coding standards in `DEVELOPMENT.md`
4. Run tests before committing: `pytest tests/`

### Current Status

🟡 **Phase 1: Database & Scraper** (In Progress)

See [`tasks.md`](tasks.md) for detailed task breakdown.

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov

# Test specific component
python -m scrapers.oversight_gov --dry-run
python -m llm.filter  # If it has test cases
python -m bot.post_reports --dry-run
```

---

## 📈 Monitoring

### Check Daily Costs

```python
# View LLM usage
cat llm_usage.log | tail -n 10

# Calculate monthly cost
python -c "
import json
total = sum(float(json.loads(line)['cost']) 
            for line in open('llm_usage.log'))
print(f'Total: \${total:.2f}')
"
```

### Review LLM Decisions

```bash
# Check filtering decisions
cat llm_decisions.log | tail -n 20

# Count newsworthy vs not newsworthy
grep '"newsworthy": true' llm_decisions.log | wc -l
```

### Database Stats

```bash
sqlite3 database/ig_reports.db <<EOF
SELECT COUNT(*) as total_reports FROM ig_reports;
SELECT COUNT(*) as newsworthy FROM ig_reports WHERE passed_llm_filter = 1;
SELECT COUNT(*) as posted FROM ig_reports WHERE posted = 1;
EOF
```

---

## 💰 Cost Breakdown

**Monthly costs:**
- OpenAI API (GPT-4o-mini): $1-2
- GitHub Actions: $0 (free tier)
- GitHub Pages: $0 (free)
- Domain (optional): ~$1

**Total: $1-3/month** ✨

---

## 🗓️ Automation

Runs automatically via GitHub Actions:
- **Schedule:** Daily at 8 AM ET (1 PM UTC)
- **Tasks:** Scrape → Filter → Summarize → Post → Update Website

See [`.github/workflows/daily.yml`](.github/workflows/daily.yml) for details.

---

## 🌐 Links

- **Bot:** [@igoversight.bsky.social](https://bsky.app/profile/igoversight.bsky.social)
- **Website:** [yourusername.github.io/ig-reports-bot](https://yourusername.github.io/ig-reports-bot)
- **Data Source:** [Oversight.gov](https://www.oversight.gov/reports/federal)

---

## 📄 Documentation

- **[agents.md](agents.md)** - Comprehensive development guide (for AI assistants)
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development workflow and best practices
- **[tasks.md](tasks.md)** - Detailed task breakdown by phase
- **Project Specs:**
  - [IG_REPORTS_BOT_SPEC.md](/mnt/project/IG_REPORTS_BOT_SPEC.md) - Complete specification
  - [IG_BOT_QUICKSTART.md](/mnt/project/IG_BOT_QUICKSTART.md) - Step-by-step guide
  - [LLM_INTEGRATION.md](/mnt/project/LLM_INTEGRATION.md) - LLM prompts & best practices

---

## 🤝 Contributing

Contributions welcome! This bot serves the public interest.

**Before contributing:**
1. Read [`DEVELOPMENT.md`](DEVELOPMENT.md)
2. Check [`tasks.md`](tasks.md) for current priorities
3. Follow the coding standards
4. Write tests for new features
5. Keep costs low (LLM usage)

---

## ⚖️ License

MIT License - see [LICENSE](LICENSE) for details

---

## 🙏 Credits

- **Data Source:** [Oversight.gov](https://www.oversight.gov) - Aggregates reports from 70+ federal IGs
- **Inspiration:** Making government accountability accessible to all
- **Tech:** Built with Python, OpenAI, Bluesky (atproto), and GitHub Actions

---

## 📞 Contact

- **Issues:** [GitHub Issues](https://github.com/yourusername/ig-reports-bot/issues)
- **Bluesky:** [@igoversight.bsky.social](https://bsky.app/profile/igoversight.bsky.social)

---

**Making government accountability accessible, one report at a time.** 🛡️✨

---

## 🎯 Success Metrics

**After 1 month:**
- [ ] 5-10 quality posts daily
- [ ] 500+ Bluesky followers
- [ ] 1,000+ website visits
- [ ] Zero cost overruns
- [ ] Cited by journalists

**After 3 months:**
- [ ] 2,000+ followers
- [ ] Clear public value
- [ ] Sustainable & low-maintenance
- [ ] Referenced in news articles
- [ ] Growing RSS subscriber base
