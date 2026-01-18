# IG Reports Bot - Setup Files Summary

All the files you need to get Claude Sonnet 4.5 working on this project in VS Code.

## 📦 Files Created

### Core Documentation Files

1. **agents.md** (⭐ PRIMARY REFERENCE)
   - Comprehensive development guide for AI assistants
   - Project architecture and data flow
   - Development phases with detailed tasks
   - Key files to implement with specifications
   - Coding guidelines and best practices
   - Common development tasks and debugging tips

2. **CLAUDE_QUICKSTART.md** (⭐ START HERE)
   - Quick orientation for Claude
   - Current project status
   - First tasks to tackle
   - Essential reading list
   - Success criteria for Phase 1

3. **README.md**
   - Main project documentation
   - Quick start instructions
   - Project structure overview
   - Links to all resources

4. **tasks.md**
   - Detailed task breakdown for all phases
   - Phase 0-7 with specific sub-tasks
   - Priority levels and success criteria
   - Checklist format for tracking progress

5. **DEVELOPMENT.md**
   - Development workflow guide
   - Testing strategies
   - Code quality standards
   - Debugging tips
   - Common issues and solutions

### Configuration Files

6. **.clinerules**
   - Claude Code configuration
   - Project context and key files
   - Coding standards
   - Common commands
   - Development workflow notes

7. **.env.example**
   - Environment variables template
   - Shows required API keys
   - Copy to `.env` and fill in actual values

8. **requirements.txt**
   - Python dependencies
   - All packages needed for the project
   - Includes testing and development tools

9. **.gitignore**
   - Files to exclude from git
   - Protects secrets (.env)
   - Ignores Python cache files
   - Excludes logs and temp files

---

## 🚀 How to Use These Files

### For VS Code with Claude Code

1. **Create your project directory:**
   ```bash
   mkdir ig-reports-bot
   cd ig-reports-bot
   ```

2. **Copy all files into the project root:**
   - Place all 9 files in the `ig-reports-bot/` directory

3. **Initialize git repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial project setup with documentation"
   ```

4. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

6. **Open in VS Code:**
   ```bash
   code .
   ```

7. **Start Claude Code:**
   - Claude will automatically read `.clinerules` for project context
   - Claude should start by reading `CLAUDE_QUICKSTART.md`
   - Then proceed to `agents.md` for detailed guidance

### For Claude Sonnet 4.5

When Claude starts working on this project, it should:

1. **Read in this order:**
   - `CLAUDE_QUICKSTART.md` - Quick orientation
   - `agents.md` - Complete development guide
   - `tasks.md` - Current task breakdown
   - Spec files (already in `/mnt/project/`)

2. **Start with Phase 1 tasks:**
   - Create database schema
   - Build scraper
   - Test with dry-run mode

3. **Follow the workflow:**
   - Read relevant docs before coding
   - Test thoroughly with dry-run modes
   - Update documentation as needed
   - Check off tasks in `tasks.md`

---

## 📁 Recommended Directory Structure

After setup, your project should look like:

```
ig-reports-bot/
├── agents.md                  # ⭐ Main dev guide
├── CLAUDE_QUICKSTART.md       # ⭐ Start here
├── README.md
├── tasks.md
├── DEVELOPMENT.md
├── .clinerules
├── .env.example
├── .env                       # Create this (don't commit!)
├── requirements.txt
├── .gitignore
│
├── database/                  # Create these as you go
│   ├── schema.sql
│   ├── db.py
│   └── ig_reports.db
│
├── scrapers/
│   ├── __init__.py
│   ├── base.py
│   └── oversight_gov.py
│
├── llm/
│   ├── __init__.py
│   ├── client.py
│   ├── filter.py
│   └── summary.py
│
├── bot/
│   ├── __init__.py
│   ├── bluesky_poster.py
│   └── post_reports.py
│
├── web/
│   ├── build.py
│   ├── templates/
│   └── static/
│
├── tests/
│   ├── test_scraper.py
│   ├── test_llm.py
│   └── test_database.py
│
├── .github/
│   └── workflows/
│       └── daily.yml
│
└── run_daily.py
```

---

## 🎯 File Purpose Quick Reference

| File | Purpose | When to Read |
|------|---------|-------------|
| **CLAUDE_QUICKSTART.md** | Quick orientation | First thing |
| **agents.md** | Complete dev guide | Before starting work |
| **tasks.md** | Task checklist | Daily, for next task |
| **DEVELOPMENT.md** | Workflow & testing | When implementing/debugging |
| **README.md** | Project overview | For understanding goals |
| **.clinerules** | Claude Code config | Auto-loaded by Claude Code |
| **.env.example** | Env var template | During initial setup |
| **requirements.txt** | Dependencies | During pip install |
| **.gitignore** | Git exclusions | During git setup |

---

## ⚡ Quick Start Commands

```bash
# Setup
mkdir ig-reports-bot && cd ig-reports-bot
# Copy all 9 files here
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys

# Development
pytest tests/                           # Run tests
python run_daily.py --dry-run          # Test pipeline
python -m scrapers.oversight_gov --dry-run  # Test scraper

# Database
python -m database.db                  # Initialize
sqlite3 database/ig_reports.db         # Inspect
```

---

## 📝 Next Steps

1. **Set up environment** (see above)
2. **Have Claude read `CLAUDE_QUICKSTART.md`**
3. **Have Claude read `agents.md`** thoroughly
4. **Start Phase 1 tasks** from `tasks.md`:
   - Create database schema
   - Implement database operations
   - Build Oversight.gov scraper
   - Test with dry-run mode

---

## 💡 Tips for Success

### For Claude:
- Always use `--dry-run` flags when testing
- Read the spec files in `/mnt/project/` for detailed requirements
- Log everything during development
- Test incrementally, not all at once
- Update docs as you make changes

### For Developers:
- Review Claude's code thoroughly
- Test with real data before deploying
- Monitor costs in OpenAI dashboard
- Check GitHub Actions logs after automation setup
- Review LLM decisions in logs regularly

---

## 📚 Additional Resources

The project also references these spec files (already available in `/mnt/project/`):
- `IG_REPORTS_BOT_SPEC.md` - Complete specification
- `IG_BOT_QUICKSTART.md` - Step-by-step implementation guide  
- `LLM_INTEGRATION.md` - LLM prompts and best practices

---

## ✅ Setup Checklist

- [ ] Created project directory
- [ ] Copied all 9 files
- [ ] Initialized git repository
- [ ] Created Python virtual environment
- [ ] Installed dependencies from requirements.txt
- [ ] Created .env from .env.example
- [ ] Added API keys to .env
- [ ] Opened project in VS Code
- [ ] Claude read CLAUDE_QUICKSTART.md
- [ ] Claude read agents.md
- [ ] Ready to start Phase 1!

---

**You're all set! Claude can now start building the IG Reports Bot.** 🛡️✨

The bot will make government accountability accessible to everyone, automatically surfacing important Inspector General findings about fraud, waste, and abuse.

**First task:** Create the database schema (see `agents.md` Section "Phase 1" and `tasks.md` for details)
