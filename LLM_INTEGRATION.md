# LLM Integration Guide - IG Reports Bot

Complete guide to using GPT-4o-mini for filtering and summarization with best practices, prompt engineering, and cost optimization.

## Table of Contents
1. [Overview](#overview)
2. [Setup](#setup)
3. [Filter LLM](#filter-llm)
4. [Summary LLM](#summary-llm)
5. [Prompt Engineering](#prompt-engineering)
6. [Cost Optimization](#cost-optimization)
7. [Error Handling](#error-handling)
8. [Testing & Iteration](#testing--iteration)

---

## Overview

**Two LLM calls per interesting report:**
1. **Filter** - Is this newsworthy? (Yes/No decision)
2. **Summary** - Generate Bluesky post text

**Why GPT-4o-mini:**
- Cheapest capable model ($0.15/$0.60 per 1M tokens)
- Fast responses (~1-2 seconds)
- Good at structured output (JSON)
- Reliable for this use case

**Expected costs:**
- 100 filter checks/day = $0.30/month
- 10 summaries/day = $0.30/month
- **Total: ~$0.60-1/month**

---

## Setup

### Install OpenAI SDK

```bash
pip install openai python-dotenv
```

### Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-proj-...
```

### Basic Client Setup

```python
# llm/client.py

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def call_gpt(prompt, max_tokens=100, temperature=0.3, response_format=None):
    """
    Wrapper for OpenAI API calls
    
    Args:
        prompt: The prompt text
        max_tokens: Maximum response length
        temperature: 0=deterministic, 1=creative
        response_format: {"type": "json_object"} for JSON responses
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            response_format=response_format
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None
```

---

## Filter LLM

### Purpose

**Decide:** Is this report newsworthy enough to post?

**Input:** Title, agency, abstract  
**Output:** JSON with decision, score, reasoning

### The Prompt

```python
# llm/filter.py

import json
from llm.client import call_gpt

FILTER_PROMPT_TEMPLATE = """You are a journalist evaluating Inspector General reports for newsworthiness.

Report:
Title: {title}
Agency: {agency_name}
Type: {report_type}
Published: {published_date}
Abstract: {abstract}

Determine if this report is newsworthy enough to share publicly.

NEWSWORTHY criteria (any of these):
✓ Fraud cases, especially $1M+
✓ Criminal investigations or charges
✓ Major waste/abuse ($1M+ wasted)
✓ Significant agency failures affecting public
✓ Whistleblower revelations
✓ High-profile mismanagement
✓ Public safety/health issues
✓ Major security breaches

NOT newsworthy:
✗ Routine financial audits with clean findings
✗ Minor process recommendations
✗ IT infrastructure reports (unless breach)
✗ Accounting discrepancies under $100K
✗ Standard compliance checks
✗ Positive performance reviews

Extract information:
- Dollar amount mentioned (null if none or unclear)
- Criminal investigation involved (true/false)
- Topic tags (1-3 from: fraud, waste, mismanagement, security, safety, healthcare, defense, etc.)

Respond with ONLY valid JSON (no markdown, no explanation):
{{
    "newsworthy": true,
    "score": 8,
    "reason": "Major fraud case with criminal charges",
    "dollar_amount": 1000000,
    "criminal": true,
    "topics": ["fraud", "healthcare"]
}}
"""

def filter_report(report):
    """
    Use LLM to determine if report is newsworthy
    
    Returns: dict with filtering decision or None on error
    """
    
    # Build prompt
    prompt = FILTER_PROMPT_TEMPLATE.format(
        title=report['title'],
        agency_name=report['agency_name'],
        report_type=report.get('report_type', 'Report'),
        published_date=report['published_date'],
        abstract=report.get('abstract', '')[:1000]  # Truncate long abstracts
    )
    
    # Call LLM with JSON response format
    response = call_gpt(
        prompt=prompt,
        max_tokens=150,
        temperature=0.3,  # Lower = more consistent
        response_format={"type": "json_object"}
    )
    
    if not response:
        return None
    
    # Parse JSON response
    try:
        result = json.loads(response)
        
        # Validate required fields
        required = ['newsworthy', 'score', 'reason']
        if not all(k in result for k in required):
            print(f"Missing required fields in LLM response: {result}")
            return None
        
        return result
    
    except json.JSONDecodeError as e:
        print(f"Failed to parse LLM JSON response: {e}")
        print(f"Response was: {response}")
        return None
```

### Usage Example

```python
from llm.filter import filter_report

report = {
    'title': 'Audit of Medicare Fraud Prevention Program',
    'agency_name': 'Department of Health and Human Services',
    'report_type': 'Audit',
    'published_date': '2026-01-18',
    'abstract': 'This audit found that two contractors billed Medicare for $45 million in services never provided...'
}

result = filter_report(report)

if result and result['newsworthy']:
    print(f"✅ Newsworthy (score: {result['score']}/10)")
    print(f"Reason: {result['reason']}")
    print(f"Topics: {result['topics']}")
    print(f"Dollar amount: ${result.get('dollar_amount', 0):,}")
else:
    print(f"❌ Not newsworthy")
```

---

## Summary LLM

### Purpose

**Generate:** Plain-English Bluesky post text

**Input:** Report details + filter results  
**Output:** Formatted post text (under 280 chars)

### The Prompt

```python
# llm/summary.py

from llm.client import call_gpt

SUMMARY_PROMPT_TEMPLATE = """Write a Bluesky post about this Inspector General report.

Report:
Title: {title}
Agency: {agency_name}
Type: {report_type}
Key Finding: {filter_reason}
Dollar Amount: {dollar_display}
Criminal: {criminal}
Topics: {topics}

REQUIREMENTS:
1. Start with emoji:
   - 🚨 for fraud/criminal cases
   - 💰 for waste/mismanagement
   - ⚠️ for failures/safety issues
   - 🔍 for investigations

2. Format:
   [emoji] {agency}: {compelling headline}
   
   {key finding in plain English - 1-2 sentences}
   
   {dollar amount if >$1M}
   
3. Style:
   - Plain English (no jargon)
   - Active voice
   - Scannable and compelling
   - Under 280 characters TOTAL
   - DO NOT include report link (added separately)
   - DO NOT include hashtags (added separately)

4. Avoid:
   - Government-speak
   - Report numbers
   - Phrases like "Inspector General finds..."
   - Passive voice
   - Being boring

Write ONLY the post text (no quotes, no extra commentary):"""

def generate_post(report, filter_result):
    """
    Generate Bluesky post text using LLM
    
    Args:
        report: Dict with report details
        filter_result: Dict from filter_report()
    
    Returns: Post text string or None on error
    """
    
    # Format dollar amount for display
    dollar_amount = filter_result.get('dollar_amount')
    if dollar_amount and dollar_amount >= 1000000:
        dollar_display = f"${dollar_amount:,}"
    else:
        dollar_display = "N/A"
    
    # Build prompt
    prompt = SUMMARY_PROMPT_TEMPLATE.format(
        title=report['title'],
        agency_name=report['agency_name'],
        report_type=report.get('report_type', 'Report'),
        filter_reason=filter_result['reason'],
        dollar_display=dollar_display,
        criminal="Yes" if filter_result.get('criminal') else "No",
        topics=", ".join(filter_result.get('topics', []))
    )
    
    # Call LLM with higher temperature for creativity
    post_text = call_gpt(
        prompt=prompt,
        max_tokens=200,
        temperature=0.7  # More creative
    )
    
    if not post_text:
        return None
    
    # Clean up response
    post_text = post_text.strip()
    post_text = post_text.strip('"\'')  # Remove quotes if LLM added them
    
    # Verify length
    if len(post_text) > 280:
        print(f"Warning: Post too long ({len(post_text)} chars), truncating")
        post_text = post_text[:277] + "..."
    
    return post_text
```

### Adding Hashtags and Link

```python
def format_complete_post(post_text, report, filter_result):
    """
    Add hashtags and report link to LLM-generated post
    
    Args:
        post_text: Text from generate_post()
        report: Report dict
        filter_result: Filter result dict
    
    Returns: Complete post ready to send
    """
    
    # Build hashtags
    hashtags = []
    
    # Agency tag
    agency_tag = f"#{report['agency_id']}"
    hashtags.append(agency_tag)
    
    # Topic tags (max 2 more)
    topics = filter_result.get('topics', [])
    for topic in topics[:2]:
        tag = f"#{topic.title().replace(' ', '')}"
        if tag not in hashtags:
            hashtags.append(tag)
    
    # Build complete post
    complete_post = f"""{post_text}

Report: {report['url']}

{' '.join(hashtags)}"""
    
    # Final length check (Bluesky limit is 300 chars)
    if len(complete_post) > 300:
        # Trim hashtags if needed
        complete_post = f"""{post_text}

Report: {report['url']}

{hashtags[0]}"""
    
    return complete_post
```

### Usage Example

```python
from llm.summary import generate_post, format_complete_post

# After filtering
if filter_result['newsworthy']:
    # Generate post text
    post_text = generate_post(report, filter_result)
    
    if post_text:
        # Add hashtags and link
        complete_post = format_complete_post(post_text, report, filter_result)
        
        print("Ready to post:")
        print(complete_post)
        print(f"\nLength: {len(complete_post)} chars")
```

---

## Prompt Engineering

### Best Practices

#### 1. Be Specific About Format

**❌ Bad:**
```
Is this report interesting?
```

**✅ Good:**
```
Respond with ONLY valid JSON (no markdown):
{"newsworthy": true, "score": 8, "reason": "..."}
```

#### 2. Provide Examples in Context

```python
FILTER_PROMPT = """...

Example NEWSWORTHY reports:
- "$45M Medicare fraud scheme - two executives charged"
- "VA failed to inspect 40% of high-risk facilities"
- "Pentagon wasted $2B on unused aircraft parts"

Example NOT newsworthy:
- "Annual financial statements audit - no findings"
- "IT security controls - minor improvements needed"

Now evaluate this report:
..."""
```

#### 3. Use Clear Decision Criteria

**Be explicit about what makes something newsworthy:**
- Dollar thresholds ($1M+)
- Criminal involvement
- Public impact
- Safety issues

#### 4. Control Temperature

```python
# Filtering (consistency matters)
temperature=0.3  # More deterministic

# Summarization (creativity helps)
temperature=0.7  # More varied, engaging
```

#### 5. Set Token Limits Appropriately

```python
# Filter: Need structured JSON
max_tokens=150  # Enough for full JSON response

# Summary: Need concise text
max_tokens=200  # Prevent rambling
```

### Iterating on Prompts

**Test with real examples:**

```python
# Test cases
test_reports = [
    {
        'title': 'DOJ: $68M Adult Day Care Fraud',
        'abstract': 'Two defendants plead guilty...',
        'should_be_newsworthy': True
    },
    {
        'title': 'Annual Financial Statement Audit',
        'abstract': 'Standard audit found no material weaknesses...',
        'should_be_newsworthy': False
    }
]

for report in test_reports:
    result = filter_report(report)
    correct = result['newsworthy'] == report['should_be_newsworthy']
    print(f"{'✅' if correct else '❌'} {report['title']}: {result['newsworthy']}")
```

**Adjust prompt based on results:**
- False positives → Add negative examples
- False negatives → Expand newsworthy criteria
- Inconsistent → Lower temperature
- Too conservative → Adjust thresholds

---

## Cost Optimization

### Token Usage

**Typical report:**
```
Input tokens:
- Prompt template: ~300 tokens
- Title: ~10-20 tokens
- Abstract: ~100-300 tokens
Total input: ~500 tokens

Output tokens:
- Filter JSON: ~50 tokens
- Summary text: ~100-150 tokens
```

### Cost Per Report

**Filter:**
- Input: 500 tokens × $0.15/1M = $0.000075
- Output: 50 tokens × $0.60/1M = $0.00003
- **Total: ~$0.0001 per report**

**Summary:**
- Input: 500 tokens × $0.15/1M = $0.000075
- Output: 150 tokens × $0.60/1M = $0.00009
- **Total: ~$0.00016 per report**

**Monthly costs (100 reports/day):**
- Filter all: 100 × 30 × $0.0001 = $0.30
- Summarize 10: 10 × 30 × $0.00016 = $0.05
- **Total: ~$0.35/month**

### Optimization Strategies

#### 1. Pre-filter with Keywords

```python
def should_check_llm(report):
    """Quick keyword check before expensive LLM call"""
    text = (report['title'] + ' ' + report.get('abstract', '')).lower()
    
    interesting_keywords = [
        'fraud', 'criminal', 'investigation', 'charged',
        'scheme', 'million', 'billion', 'waste', 'abuse',
        'mismanagement', 'failure', 'violation', 'guilty'
    ]
    
    return any(keyword in text for keyword in interesting_keywords)

# Only call LLM if keywords match
if should_check_llm(report):
    result = filter_report(report)
else:
    result = {'newsworthy': False, 'reason': 'No keywords matched'}
```

**Savings:** Reduces LLM calls by ~70%, saves ~$0.20/month

#### 2. Truncate Long Abstracts

```python
# Don't send 2000-word abstracts
abstract = report.get('abstract', '')[:1000]  # First 1000 chars only
```

#### 3. Batch Requests (Future)

```python
# OpenAI supports batch API for 50% discount
# Process overnight batch of reports
```

#### 4. Cache Responses

```python
# Store LLM responses in database
# Don't re-process same report
```

---

## Error Handling

### Robust LLM Calls

```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
def call_gpt_with_retry(prompt, **kwargs):
    """Call GPT with automatic retries on failure"""
    return call_gpt(prompt, **kwargs)
```

### Handle Common Errors

```python
def safe_filter_report(report):
    """Filter with comprehensive error handling"""
    
    try:
        result = filter_report(report)
        
        if not result:
            print(f"LLM returned None for: {report['title']}")
            return {
                'newsworthy': False,
                'reason': 'LLM error',
                'error': True
            }
        
        # Validate score range
        if 'score' in result:
            result['score'] = max(1, min(10, result['score']))
        
        return result
    
    except Exception as e:
        print(f"Error filtering report: {e}")
        return {
            'newsworthy': False,
            'reason': f'Error: {str(e)}',
            'error': True
        }
```

### Fallback to Keywords

```python
def filter_with_fallback(report):
    """Try LLM, fall back to keywords if it fails"""
    
    # Try LLM first
    result = safe_filter_report(report)
    
    if result.get('error'):
        # Fall back to simple keyword matching
        print(f"LLM failed, using keyword fallback")
        return keyword_filter(report)
    
    return result
```

---

## Testing & Iteration

### Manual Testing

```python
# test_llm.py

from llm.filter import filter_report
from llm.summary import generate_post, format_complete_post

# Test report
report = {
    'title': 'Audit of Medicare Fraud Prevention',
    'agency_name': 'HHS Office of Inspector General',
    'agency_id': 'HHS',
    'report_type': 'Audit',
    'published_date': '2026-01-18',
    'abstract': 'This audit identified $45 million in fraudulent Medicare claims...',
    'url': 'https://oig.hhs.gov/report/123'
}

print("🔍 Testing Filter...")
filter_result = filter_report(report)
print(json.dumps(filter_result, indent=2))

if filter_result['newsworthy']:
    print("\n📝 Testing Summary...")
    post_text = generate_post(report, filter_result)
    print(f"\nGenerated text:\n{post_text}")
    
    print("\n📮 Complete Post:")
    complete = format_complete_post(post_text, report, filter_result)
    print(complete)
    print(f"\nLength: {len(complete)} chars")
```

### Automated Testing

```python
# tests/test_llm.py

def test_filter_fraud_case():
    """Test that fraud cases are correctly identified"""
    report = {
        'title': 'Investigation: $50M Fraud Scheme',
        'abstract': 'Criminal charges filed against contractor...'
    }
    
    result = filter_report(report)
    
    assert result['newsworthy'] == True
    assert result['criminal'] == True
    assert result['dollar_amount'] >= 50000000

def test_filter_routine_audit():
    """Test that routine audits are filtered out"""
    report = {
        'title': 'Annual Financial Statement Audit',
        'abstract': 'Clean audit opinion, no findings...'
    }
    
    result = filter_report(report)
    
    assert result['newsworthy'] == False
```

### Monitor Quality

```python
# Track LLM performance
def log_llm_decision(report, result):
    """Log decisions for later review"""
    with open('llm_decisions.log', 'a') as f:
        f.write(f"{datetime.now()},{report['title']},{result['newsworthy']},{result['score']}\n")

# Weekly review
# Check llm_decisions.log for:
# - False positives (boring reports marked newsworthy)
# - False negatives (interesting reports missed)
# - Adjust prompts accordingly
```

---

## Quick Reference

### Filter Call

```python
result = filter_report(report)
# → {'newsworthy': True, 'score': 8, 'reason': '...', 'dollar_amount': 1000000}
```

### Summary Call

```python
post_text = generate_post(report, filter_result)
complete_post = format_complete_post(post_text, report, filter_result)
# → Ready to post to Bluesky
```

### Cost Check

```python
# Monthly: ~$0.60-1
# Per report filtered: ~$0.0001
# Per report summarized: ~$0.00016
```

---

**LLM integration makes the bot smart, scalable, and costs less than a coffee!** ☕🤖
