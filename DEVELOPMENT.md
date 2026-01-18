# Development Guide

Comprehensive guide for developing and testing the IG Reports Bot.

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ig-reports-bot.git
cd ig-reports-bot

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Initialize database
python -m database.db

# 6. Test scraper
python -m scrapers.oversight_gov --dry-run

# 7. Run pipeline
python run_daily.py --dry-run
```

## Development Workflow

### 1. Starting New Work

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Verify environment
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Making Changes

```bash
# Make your changes
# Write tests as you go

# Run tests frequently
pytest tests/

# Check code quality
black .
flake8 .
mypy .
```

### 3. Testing Changes

```bash
# Test specific component
python -m scrapers.oversight_gov --dry-run
python -m llm.filter  # If it has test cases
python -m bot.post_reports --dry-run

# Test full pipeline
python run_daily.py --dry-run

# Run all tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

### 4. Committing

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add oversight.gov scraper with keyword filtering"

# Push to your branch
git push origin feature/your-feature-name

# Create pull request on GitHub
```

## Code Quality Standards

### Python Style Guide

Follow PEP 8 with these specifics:

```python
# Good: Clear, descriptive names
def scrape_recent_reports(days_back: int = 1) -> list[dict]:
    """
    Scrape recent Inspector General reports.
    
    Args:
        days_back: Number of days to look back
        
    Returns:
        List of report dictionaries
    """
    pass

# Bad: Unclear names, missing docs
def scrape(d=1):
    pass
```

### Type Hints

Use type hints for all public functions:

```python
from typing import Optional, Dict, List

def filter_report(report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Filter report with LLM."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def generate_post(report: dict, filter_result: dict) -> str:
    """
    Generate Bluesky post text from report.
    
    Args:
        report: Report dictionary with title, abstract, etc.
        filter_result: Results from LLM filter
        
    Returns:
        Post text under 280 characters
        
    Raises:
        ValueError: If report is missing required fields
        
    Example:
        >>> post = generate_post(report, filter_result)
        >>> len(post) < 280
        True
    """
    pass
```

### Error Handling

Always handle errors gracefully:

```python
# Good: Specific error handling
try:
    result = filter_report(report)
except OpenAIError as e:
    logger.error(f"OpenAI API error: {e}")
    return None
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON response: {e}")
    return None

# Bad: Silent failures
try:
    result = filter_report(report)
except:
    pass
```

## Testing Strategy

### Unit Tests

Test individual functions in isolation:

```python
# tests/test_scraper.py
from scrapers.oversight_gov import has_interesting_keywords

def test_fraud_keyword_matches():
    report = {'title': 'DOJ Fraud Investigation', 'abstract': ''}
    assert has_interesting_keywords(report) == True

def test_routine_audit_no_match():
    report = {'title': 'Annual Financial Audit', 'abstract': ''}
    assert has_interesting_keywords(report) == False
```

### Integration Tests

Test components working together:

```python
# tests/test_pipeline.py
def test_full_pipeline():
    """Test complete scrape -> filter -> summarize flow"""
    # Scrape
    reports = scrape_recent_reports(days_back=7)
    assert len(reports) > 0
    
    # Filter
    for report in reports[:5]:  # Test first 5
        result = filter_report(report)
        assert result is not None
        assert 'newsworthy' in result
```

### Mock External APIs

Use pytest-mock for external calls:

```python
# tests/test_llm_filter.py
def test_filter_with_mock(mocker):
    """Test filter without actually calling OpenAI"""
    mock_response = {
        'newsworthy': True,
        'score': 8,
        'reason': 'Major fraud case'
    }
    
    mocker.patch('llm.filter.call_gpt', return_value=json.dumps(mock_response))
    
    result = filter_report({'title': 'Test', 'abstract': 'Test'})
    assert result['newsworthy'] == True
```

## Database Development

### Working with SQLite

```bash
# Open database
sqlite3 database/ig_reports.db

# Useful commands:
.tables                    # List tables
.schema ig_reports        # Show table structure
SELECT COUNT(*) FROM ig_reports;
SELECT * FROM ig_reports LIMIT 5;

# Export data
.mode csv
.output reports.csv
SELECT * FROM ig_reports;
.quit

# Backup database
cp database/ig_reports.db database/ig_reports.db.backup
```

### Schema Changes

When modifying schema:

1. Update `database/schema.sql`
2. Create migration script if needed
3. Test with fresh database
4. Document changes

```python
# migrations/001_add_column.py
def migrate():
    conn = get_connection()
    conn.execute('ALTER TABLE ig_reports ADD COLUMN new_field TEXT')
    conn.commit()
    conn.close()
```

## LLM Development

### Testing Prompts

Use this workflow to develop/test prompts:

```python
# 1. Create test cases
test_reports = [
    {
        'title': 'DOJ: $50M Prison Fraud',
        'abstract': 'Criminal charges...',
        'expected': True
    },
    {
        'title': 'Annual Financial Audit',
        'abstract': 'Clean opinion...',
        'expected': False
    }
]

# 2. Test current prompt
for test in test_reports:
    result = filter_report(test)
    correct = result['newsworthy'] == test['expected']
    print(f"{'✅' if correct else '❌'} {test['title']}")

# 3. Review llm_decisions.log
tail -n 50 llm_decisions.log

# 4. Iterate on prompt
# Edit llm/filter.py or llm/summary.py
# Re-test until accuracy >90%
```

### Cost Monitoring

Track LLM costs during development:

```python
# Check today's costs
python -c "
import json
from datetime import datetime

today = datetime.now().date()
total = 0

with open('llm_usage.log') as f:
    for line in f:
        entry = json.loads(line)
        entry_date = datetime.fromisoformat(entry['timestamp']).date()
        if entry_date == today:
            total += entry['cost']

print(f'Today: \${total:.4f}')
"
```

### Rate Limiting

Be respectful during testing:

```python
import time

for report in test_reports:
    result = filter_report(report)
    time.sleep(1)  # Avoid hitting rate limits
```

## Debugging Tips

### Enable Verbose Logging

```python
# Add to top of script
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Use Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb for better experience
# pip install ipdb
import ipdb; ipdb.set_trace()
```

### Check Logs

```bash
# Follow logs in real-time
tail -f llm_decisions.log

# Search for errors
grep "ERROR" *.log

# Filter by date
grep "2026-01-18" llm_usage.log
```

## Common Issues & Solutions

### Issue: Scraper returns empty list

**Check:**
1. Is Oversight.gov accessible? `curl https://www.oversight.gov`
2. Has the HTML structure changed? Inspect in browser
3. Are you filtering too aggressively? Try `--verbose`

**Solution:**
```bash
python -m scrapers.oversight_gov --dry-run --verbose
# Should show detailed parsing info
```

### Issue: LLM filter always returns False

**Check:**
1. Is API key set? `echo $OPENAI_API_KEY`
2. Is prompt formatting correctly? Print before sending
3. Is response being parsed correctly? Print raw response

**Solution:**
```python
# Add debug logging to llm/filter.py
print(f"Prompt: {prompt}")
print(f"Response: {response}")
```

### Issue: Database locked

**Cause:** SQLite doesn't handle concurrent writes well

**Solution:**
```python
# Add timeout to connection
conn = sqlite3.connect('database/ig_reports.db', timeout=10.0)

# Or: Close connections properly
try:
    # ... database operations
finally:
    conn.close()
```

### Issue: GitHub Actions failing

**Check:**
1. Are secrets set correctly in GitHub?
2. Does it work locally? Test locally first
3. Check the workflow logs in GitHub Actions tab

**Solution:**
```bash
# Test locally with same commands as workflow
source venv/bin/activate
python run_daily.py
python -m bot.post_reports --dry-run
```

## Performance Optimization

### Scraping

```python
# Use session for multiple requests
session = requests.Session()
session.headers.update({'User-Agent': '...'})

# Cache responses during development
import requests_cache
requests_cache.install_cache('oversight_cache', expire_after=3600)
```

### Database

```python
# Use batch inserts
conn.executemany('INSERT INTO ...', batch_of_reports)

# Add indexes
CREATE INDEX idx_agency_date ON ig_reports(agency_id, published_date);

# Use connection pooling for concurrent access
```

### LLM Calls

```python
# Pre-filter with keywords (70% reduction)
if not has_interesting_keywords(report):
    return {'newsworthy': False, 'reason': 'No keywords'}

# Batch similar requests (future)
# Use OpenAI batch API for 50% cost savings
```

## Pre-commit Checklist

Before committing:

- [ ] All tests pass (`pytest tests/`)
- [ ] Code formatted (`black .`)
- [ ] No linting errors (`flake8 .`)
- [ ] Type checking passes (`mypy .`)
- [ ] Updated documentation if needed
- [ ] No secrets in code (check with `git diff`)
- [ ] Commit message follows convention

## Release Process

When ready to deploy:

1. **Test thoroughly**
   ```bash
   pytest tests/ --cov
   python run_daily.py --dry-run
   ```

2. **Update version**
   ```python
   # __init__.py
   __version__ = '0.2.0'
   ```

3. **Update CHANGELOG.md**
   ```markdown
   ## [0.2.0] - 2026-01-20
   ### Added
   - LLM filtering
   - Bluesky posting
   ```

4. **Tag release**
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin v0.2.0
   ```

5. **Monitor first day**
   - Check GitHub Actions logs
   - Verify posts on Bluesky
   - Check costs in OpenAI dashboard
   - Review llm_decisions.log

## Getting Help

**Resources:**
- Check `agents.md` for architecture
- Review `tasks.md` for task breakdown
- Read spec files in `/mnt/project/`

**Debugging:**
1. Read error messages carefully
2. Check logs
3. Search similar issues in code
4. Test in isolation
5. Ask for help with context

## Development Tools

### Recommended VS Code Extensions

- Python
- Pylance
- Black Formatter
- SQLite Viewer
- GitLens
- Error Lens

### Recommended CLI Tools

```bash
# Code quality
pip install black flake8 mypy

# Database inspection  
brew install sqlite3  # or apt-get install sqlite3

# HTTP debugging
brew install httpie

# JSON formatting
brew install jq
```

### Useful Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc
alias venv='source venv/bin/activate'
alias test='pytest tests/ -v'
alias format='black . && flake8 .'
alias dbshell='sqlite3 database/ig_reports.db'
```

---

**Happy coding! Remember: Quality over quantity. Every post should be genuinely newsworthy.** 🛡️✨
