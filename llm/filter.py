"""
LLM-based filter to determine if IG reports are newsworthy
"""

import json
import logging
from typing import Dict, Any, Optional

from .client import call_gpt


logger = logging.getLogger(__name__)


# Prompt template for filtering reports
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
✓ Corruption or bribery
✓ Large-scale embezzlement or theft

NOT newsworthy:
✗ Routine financial audits with clean findings
✗ Minor process recommendations
✗ IT infrastructure reports (unless breach)
✗ Accounting discrepancies under $100K
✗ Standard compliance checks
✗ Positive performance reviews
✗ Routine management advisories

Extract information:
- Dollar amount mentioned (null if none or unclear, integer if found)
- Criminal investigation involved (true/false)
- Topic tags (1-3 from: fraud, waste, mismanagement, security, safety, healthcare, defense, criminal, corruption)

Score 1-10 where:
- 10 = Major fraud/criminal case with massive impact
- 8-9 = Significant waste/abuse or serious misconduct
- 6-7 = Notable mismanagement or medium-sized fraud
- 4-5 = Minor issues but still public interest
- 1-3 = Routine/administrative

Only consider newsworthy if score >= 6.

Respond with ONLY valid JSON (no markdown, no explanation):
{{
    "newsworthy": true,
    "score": 8,
    "reason": "Major fraud case with criminal charges and $2M in losses",
    "dollar_amount": 2000000,
    "criminal": true,
    "topics": ["fraud", "criminal"]
}}
"""


def filter_report(report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Use LLM to determine if report is newsworthy
    
    Args:
        report: Report dictionary with title, agency_name, abstract, etc.
    
    Returns:
        Dict with filtering decision:
        {
            'newsworthy': bool,
            'score': int (1-10),
            'reason': str,
            'dollar_amount': int or None,
            'criminal': bool,
            'topics': list of str
        }
        Or None on error
    """
    try:
        # Build prompt
        prompt = FILTER_PROMPT_TEMPLATE.format(
            title=report.get('title', 'Unknown'),
            agency_name=report.get('agency_name', 'Unknown Agency'),
            report_type=report.get('report_type', 'Report'),
            published_date=report.get('published_date', 'Unknown'),
            abstract=report.get('abstract', '')[:1500]  # Truncate very long abstracts
        )
        
        # Call LLM with JSON response format
        response = call_gpt(
            prompt=prompt,
            max_tokens=200,
            temperature=0.3,  # Lower = more consistent decisions
            response_format={"type": "json_object"}
        )
        
        if not response:
            logger.error(f"LLM returned no response for report: {report.get('title', 'Unknown')[:50]}")
            return None
        
        # Parse JSON response
        result = json.loads(response)
        
        # Validate required fields
        required = ['newsworthy', 'score', 'reason']
        if not all(k in result for k in required):
            logger.error(f"Missing required fields in LLM response: {result}")
            return None
        
        # Ensure types are correct
        result['newsworthy'] = bool(result['newsworthy'])
        result['score'] = int(result['score'])
        result['criminal'] = bool(result.get('criminal', False))
        result['topics'] = result.get('topics', [])
        
        # Log decision
        log_filter_decision(report, result)
        
        return result
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {e}")
        logger.error(f"Response was: {response}")
        return None
    
    except Exception as e:
        logger.error(f"Error filtering report: {e}")
        return None


def log_filter_decision(report: Dict[str, Any], decision: Dict[str, Any]) -> None:
    """
    Log LLM filter decisions for review
    """
    try:
        log_entry = {
            'timestamp': report.get('published_date'),
            'report_id': report.get('report_id'),
            'title': report.get('title', '')[:100],
            'agency': report.get('agency_name'),
            'decision': decision
        }
        
        with open('llm_decisions.log', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    except Exception as e:
        logger.warning(f"Failed to log decision: {e}")


def get_filter_stats() -> Dict[str, Any]:
    """
    Analyze filter decisions from log
    
    Returns:
        Stats dict with counts and percentages
    """
    try:
        total = 0
        newsworthy = 0
        scores = []
        
        with open('llm_decisions.log', 'r') as f:
            for line in f:
                entry = json.loads(line)
                decision = entry.get('decision', {})
                
                total += 1
                if decision.get('newsworthy'):
                    newsworthy += 1
                
                score = decision.get('score')
                if score:
                    scores.append(score)
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            'total_evaluated': total,
            'newsworthy': newsworthy,
            'not_newsworthy': total - newsworthy,
            'newsworthy_percentage': (newsworthy / total * 100) if total > 0 else 0,
            'average_score': avg_score
        }
    
    except FileNotFoundError:
        return {
            'total_evaluated': 0,
            'newsworthy': 0,
            'not_newsworthy': 0,
            'newsworthy_percentage': 0,
            'average_score': 0
        }
    except Exception as e:
        logger.warning(f"Failed to get filter stats: {e}")
        return {}


# Test function
if __name__ == '__main__':
    print("Testing LLM filter...")
    
    # Test with a sample report
    test_report = {
        'report_id': 'test-001',
        'title': 'Investigation Substantiates Sexual Harassment Allegations Against VA Medical Center Chief of Staff',
        'agency_name': 'Department of Veterans Affairs',
        'agency_id': 'VA',
        'report_type': 'Investigation',
        'published_date': '2024-01-15',
        'abstract': 'An investigation substantiated allegations that the Chief of Staff engaged in sexual harassment...',
        'url': 'https://www.oversight.gov/report/test'
    }
    
    result = filter_report(test_report)
    
    if result:
        print(f"\n✅ Filter result:")
        print(f"   Newsworthy: {result['newsworthy']}")
        print(f"   Score: {result['score']}/10")
        print(f"   Reason: {result['reason']}")
        print(f"   Criminal: {result['criminal']}")
        print(f"   Topics: {result['topics']}")
        print(f"   Dollar amount: ${result.get('dollar_amount', 'N/A')}")
    else:
        print("❌ Filter failed")
