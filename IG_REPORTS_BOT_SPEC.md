# Inspector General Reports Bot - Full Automation

## 🎯 Mission

**Broadcast federal Inspector General reports to the public, highlighting fraud, waste, and abuse in government.**

Make government accountability accessible by automatically detecting newsworthy IG findings and posting them to Bluesky in plain language.

## 🔍 The Problem

### Current State (Broken)

**Discovery is impossible:**
- Oversight.gov exists but requires active searching
- No notifications or alerts
- 50-100 reports published daily across 70+ agencies
- No way to know what's important vs routine audits
- Dense government language

**Result:** Major fraud cases, waste findings, and accountability failures go unnoticed by journalists and the public.

### What People Don't Know They're Missing

**Every day, IGs publish reports on:**
- Multi-million dollar fraud schemes
- Agency mismanagement
- Criminal investigations
- Waste and abuse
- Major failures
- Whistleblower findings

**But only insiders and specialized reporters see them.**

## 🚀 The Solution

### Fully Automated Bot + Website

1. **Scrape** - Check Oversight.gov daily for new reports
2. **Filter** - LLM reads each report and decides if newsworthy
3. **Summarize** - LLM generates plain-English post
4. **Post** - Automatically share on Bluesky
5. **Publish** - Update website with all recent reports

### Architecture

```
┌─────────────────────┐
│  Oversight.gov      │
│  (70+ federal IGs)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Daily Scraper      │
│  50-100 new reports │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Rule Filter        │
│  Keywords: fraud,   │
│  waste, criminal    │
│  Keep 30-40 reports │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  LLM Filter         │
│  (GPT-4o-mini)      │
│  "Is this news?"    │
│  Keep 5-10 reports  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐       ┌──────────────────┐
│  ig_reports.db      │──────▶│  Post to Bluesky │
│  (SQLite)           │       │  - LLM summary   │
└─────────────────────┘       │  - Plain English │
           │                  │  - Hashtags      │
           │                  └──────────────────┘
           ▼
┌─────────────────────┐
│  Static Website     │
│  - Browse reports   │
│  - Filter by agency │
│  - RSS feed         │
└─────────────────────┘
```

### Core Features

**1. Smart Filtering (LLM)**
- Reads title, abstract, agency
- Identifies fraud, waste, abuse, mismanagement
- Detects dollar amounts and severity
- Avoids routine audits

**2. Plain English Summaries (LLM)**
- Translates bureaucratese
- Highlights key finding
- Mentions dollar amounts
- Notes criminal charges if any

**3. Automated Posting**
- 5-10 posts per day
- Spread throughout day
- Include report link
- Agency-specific hashtags

**4. Website**
- Browse all reports (last 30 days)
- Filter by agency, type, topic
- Search functionality
- RSS feeds by agency

## 📊 Database Schema

### Table: `ig_reports`

```sql
CREATE TABLE ig_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Identifiers
    report_id TEXT NOT NULL UNIQUE,      -- From Oversight.gov
    url TEXT NOT NULL,
    
    -- Basic info
    agency_id TEXT NOT NULL,              -- DOD, HHS, VA, etc.
    agency_name TEXT NOT NULL,
    title TEXT NOT NULL,
    report_type TEXT,                     -- Audit, Investigation, Evaluation
    published_date DATE NOT NULL,
    
    -- Content
    abstract TEXT,
    summary TEXT,                         -- LLM-generated plain English
    
    -- Metadata
    topics TEXT,                          -- JSON: ["fraud", "healthcare"]
    dollar_amount INTEGER,                -- Extracted dollar figure
    criminal BOOLEAN DEFAULT 0,           -- Criminal investigation?
    
    -- Filtering
    passed_keyword_filter BOOLEAN DEFAULT 0,
    passed_llm_filter BOOLEAN DEFAULT 0,
    llm_filter_reason TEXT,              -- Why LLM said yes/no
    newsworthy_score INTEGER,            -- 1-10 from LLM
    
    -- Posting
    posted BOOLEAN DEFAULT 0,
    posted_at TIMESTAMP,
    post_text TEXT,                      -- Generated post content
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_published_date ON ig_reports(published_date);
CREATE INDEX idx_agency_id ON ig_reports(agency_id);
CREATE INDEX idx_posted ON ig_reports(posted);
CREATE INDEX idx_newsworthy ON ig_reports(passed_llm_filter, newsworthy_score);
```

### Table: `bot_posts`

```sql
CREATE TABLE bot_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,
    post_uri TEXT NOT NULL,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES ig_reports(id)
);
```

### Table: `agencies`

```sql
CREATE TABLE agencies (
    id TEXT PRIMARY KEY,                  -- DOD, EPA, etc.
    name TEXT NOT NULL,
    full_name TEXT,
    website TEXT,
    ig_website TEXT,
    common_topics TEXT                    -- JSON array
);
```

## 🔌 Data Sources

### Primary: Oversight.gov

**Why:** Central aggregator for all federal IGs

**URL:** `https://www.oversight.gov/reports/federal`

**What we get:**
- All federal IG reports
- Standardized format
- Daily updates
- Search/filter API (if available)

**Scraping approach:**
```python
# They have a search interface - can we access it programmatically?
# If not, scrape the /reports/federal page daily
# Look for new reports since last check
```

**Fields available:**
- Title
- Agency
- Report type (Audit, Investigation, Evaluation, etc.)
- Published date
- Abstract/summary
- PDF link
- Report number

### Secondary: Individual Agency OIG Sites

**For richer data if needed:**
- DOJ OIG: https://oig.justice.gov/reports
- HHS OIG: https://oig.hhs.gov/reports/
- DOD OIG: https://www.dodig.mil/reports.html/
- VA OIG: https://www.va.gov/oig/publications/

**Fallback if Oversight.gov scraping fails**

## 🤖 LLM Integration

### Cost Estimate: ~$2/month

**GPT-4o-mini pricing:**
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens

**Daily usage:**
- 100 reports scraped
- Filter check: 500 tokens in, 50 out per report
- 10 reports pass filter
- Summary generation: 1000 tokens in, 200 out per report

**Monthly:**
- Filtering: 100 reports × 550 tokens × 30 days = 1.65M tokens → $0.30
- Summaries: 10 reports × 1200 tokens × 30 days = 360K tokens → $0.30
- **Total: ~$0.60-1/month**

(Padding to $2/month for safety)

### LLM #1: Newsworthy Filter

**Purpose:** Decide if a report is worth posting

**Prompt template:**
```python
FILTER_PROMPT = """You are a journalist evaluating Inspector General reports for newsworthiness.

Report:
Title: {title}
Agency: {agency_name}
Type: {report_type}
Abstract: {abstract}

Determine if this report is newsworthy enough to share publicly.

NEWSWORTHY criteria:
- Fraud cases (especially $1M+)
- Criminal investigations or charges
- Major waste/abuse ($1M+)
- Significant agency failures
- Whistleblower revelations
- High-profile mismanagement
- Public safety issues

NOT newsworthy:
- Routine audits with no findings
- Process recommendations
- IT infrastructure reports (unless security breach)
- Minor accounting discrepancies
- Standard financial statement audits

Extract:
- Dollar amount if mentioned (null if none)
- Whether criminal investigation (yes/no)

Respond ONLY with valid JSON:
{{
    "newsworthy": true/false,
    "score": 1-10,
    "reason": "one sentence why",
    "dollar_amount": 1000000 or null,
    "criminal": true/false,
    "topics": ["fraud", "healthcare"] // 1-3 topic tags
}}"""
```

**Model:** GPT-4o-mini  
**Max tokens:** 100  
**Temperature:** 0.3 (consistent decisions)

### LLM #2: Post Generator

**Purpose:** Create plain-English Bluesky post

**Prompt template:**
```python
POST_PROMPT = """You are writing a Bluesky post about an Inspector General report.

Report:
Title: {title}
Agency: {agency_name}
Type: {report_type}
Abstract: {abstract}
Dollar amount: ${dollar_amount:,}
Criminal: {criminal}

Write a compelling Bluesky post that:
- Starts with emoji (🚨 for fraud/criminal, 💰 for waste, ⚠️ for failures)
- Summarizes the KEY finding in plain English
- Mentions dollar amount if significant
- Notes if criminal charges/investigation
- Keeps it under 280 characters
- Uses active voice
- Is scannable and compelling

Include relevant hashtags:
- Agency: #{agency_id}
- Topics: #Fraud #Waste #Mismanagement etc.

Do NOT:
- Use jargon or government-speak
- Include report numbers
- Be boring or bureaucratic
- Start with "Inspector General finds..."

Respond with ONLY the post text (no quotes, no explanation):"""
```

**Model:** GPT-4o-mini  
**Max tokens:** 150  
**Temperature:** 0.7 (creative but focused)

**Example output:**
```
🚨 VA Healthcare Scheme: $68M Fraud

Two executives plead guilty to billing Medicare for fake adult day care services over 3 years

Report: [link]

#VA #Fraud #Healthcare
```

## 📝 Bot Posting Strategy

### Volume

**Daily:**
- Scrape: ~100 new reports
- Keyword filter: Keep ~30-40
- LLM filter: Keep ~5-10
- Post: All that pass LLM filter

**Result:** 5-10 high-quality posts per day

### Timing

**Spread throughout day:**
```python
# Post at these times (ET):
posting_times = [
    "09:00",  # Morning commute
    "12:00",  # Lunch
    "15:00",  # Afternoon
    "18:00",  # Evening commute
]

# If 8 reports to post, spread across these times
```

### Post Format

**Template:**
```
{emoji} {agency}: {headline}

{key_finding}

{dollar_amount if >$1M}
{criminal_note if applicable}

Report: {url}

#{agency} #{topic1} #{topic2}
```

**Examples:**

```
🚨 DOJ: $45M Prison Construction Fraud

Contractor billed for work never completed on 3 federal facilities

Report: oversight.gov/report/doj-...

#DOJ #Fraud #Prisons
```

```
💰 DOD: $2.3B Wasted on Unused Equipment

Pentagon purchased aircraft parts that sat in warehouse for 8+ years

Report: oversight.gov/report/dod-...

#DOD #Waste #Defense
```

```
⚠️ EPA: Chemical Plant Inspections Failing

35% of high-risk facilities not inspected in 2 years despite regulations

Report: oversight.gov/report/epa-...

#EPA #PublicSafety #Environment
```

## 🌐 Website Features

### Homepage

**"Recent IG Findings"**
- Last 30 days of reports
- Cards showing:
  - Agency logo/icon
  - Title (plain English)
  - Key finding
  - Dollar amount (if >$1M)
  - 🚨 icon if criminal
  - Published date
  - Link to full report

**Filters:**
- By agency (dropdown)
- By type (Fraud, Waste, Mismanagement, Other)
- By date range
- By dollar amount (>$1M, >$10M, >$100M)
- Criminal cases only (toggle)

**Sort by:**
- Date (newest first) - default
- Dollar amount (highest first)
- Newsworthiness score

### Individual Report Page

**Shows:**
- Full title
- Agency
- Published date
- Plain English summary (LLM-generated)
- Official abstract
- Key facts:
  - Dollar amount
  - Criminal investigation (if applicable)
  - Topics/tags
- Link to full report (PDF)
- Share buttons

### Agency Pages

**Example: `/agency/dod`**
- All recent DOD IG reports
- Stats:
  - Total reports this year
  - Total dollar amount of waste/fraud found
  - Number of criminal investigations
- Chart: Reports over time

### RSS Feeds

- All reports: `/feed.xml`
- By agency: `/feed/dod.xml`
- Criminal only: `/feed/criminal.xml`
- High-value: `/feed/high-value.xml` (>$10M)

### JSON API

```
GET /api/reports              # Recent reports
GET /api/reports/{id}         # Single report
GET /api/agencies             # List agencies
GET /api/agencies/{id}/reports # Agency reports
GET /api/stats                # Summary stats
```

## 🎯 Success Metrics

**After 1 month:**
- Bot has 500+ followers
- Website gets 1000+ visits
- Journalists follow/cite it
- Posts get engagement (likes/reposts)

**After 6 months:**
- Bot is go-to source for IG news
- Cited in news articles
- 5,000+ followers
- Clear public value

## 🔮 Future Enhancements

**Phase 2:**
1. **Email alerts** - Daily digest of new reports
2. **Trend analysis** - "DOD waste up 40% this quarter"
3. **Follow-up tracking** - "Remember that $50M case? Update:"
4. **Agency scorecards** - Rank agencies by accountability
5. **Historical database** - Search all IG reports back years

**Phase 3:**
1. **State-level IGs** - Expand beyond federal
2. **International** - Government Accountability Office (GAO)
3. **Congressional investigations** - Overlap with oversight
4. **FOIA requests** - Track what's been requested/released

## 🛠️ Tech Stack

**Same as regulatory comment bot:**
- **Language:** Python 3.11+
- **Database:** SQLite (committed to git)
- **APIs:** Oversight.gov (scraping), OpenAI GPT-4o-mini, atproto (Bluesky)
- **Scraping:** requests, beautifulsoup4
- **Website:** Static HTML/CSS/JS
- **Hosting:** GitHub Pages + GitHub Actions
- **Cost:** ~$2/month (OpenAI API only)

## 📋 Implementation Phases

### Phase 1: Scraper + Manual Review (Week 1)
- Build Oversight.gov scraper
- Keyword filtering
- Store in database
- Manually review to understand patterns

### Phase 2: LLM Filtering (Week 2)
- Add GPT-4o-mini for newsworthy check
- Test filtering quality
- Tune prompts
- Verify cost estimates

### Phase 3: LLM Summaries + Posting (Week 2-3)
- Generate post text with LLM
- Test posting to Bluesky
- Automated daily workflow
- GitHub Actions setup

### Phase 4: Website (Week 3-4)
- Static site generator
- Browse/filter interface
- RSS feeds
- Deploy to GitHub Pages

### Phase 5: Polish & Launch (Week 4)
- Monitor for quality
- Tune LLM prompts based on results
- Public announcement
- Gather feedback

## 💰 Total Cost Breakdown

**Monthly:**
- OpenAI API: ~$2
- GitHub Actions: $0 (free tier)
- GitHub Pages: $0 (free)
- Domain (optional): ~$1/month

**Total: $2-3/month**

Still essentially free! 🎉

## 🎁 Reusable Patterns

**From regulatory comment bot:**
- Database schema patterns
- GitHub Actions workflow
- Bluesky posting logic
- Static site generator
- RSS feed generation

**New for IG bot:**
- LLM filtering pipeline
- LLM summarization
- Multi-source scraping strategy

---

**Ready to make government accountability accessible!** 🏛️📢

See **LLM_INTEGRATION.md** for detailed prompt engineering.
See **IMPLEMENTATION_GUIDE.md** for step-by-step build process.
See **LESSONS_FROM_PREVIOUS_BOTS.md** for architecture patterns.
