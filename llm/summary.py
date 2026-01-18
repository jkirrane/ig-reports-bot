"""
LLM-based summary generator for Bluesky posts
"""

import logging
from typing import Dict, Any, Optional

from .client import call_gpt


logger = logging.getLogger(__name__)


# Prompt template for generating Bluesky posts
SUMMARY_PROMPT_TEMPLATE = """You are writing a social media post about a government Inspector General report.

Report:
Title: {title}
Agency: {agency_name}
Type: {report_type}
Published: {published_date}
Key Finding: {reason}
Dollar Amount: {dollar_amount}
Criminal: {criminal}
Topics: {topics}

Abstract:
{abstract}

Write a compelling Bluesky post (like Twitter) that:
- Is 200-280 characters (NOT 280 words - be very concise!)
- Uses plain English (no jargon or bureaucratese)
- Highlights the most important finding
- Mentions dollar amounts if significant
- Notes if criminal charges involved
- Is factual and neutral (not sensational)
- Includes 1-2 relevant hashtags
- Ends with "🔗 Full report: [will be added]"

Example good posts:
"VA Chief of Staff substantiated for sexual harassment. Investigation found inappropriate conduct over 6 months. #Accountability #VA 🔗 Full report: [will be added]"

"DOD wasted $2.3M on unused equipment that sat in storage for 3 years. Audit recommends better inventory management. #Waste #Defense 🔗 Full report: [will be added]"

"HHS employee charged with stealing $450K meant for COVID relief programs. Criminal investigation ongoing. #Fraud #Healthcare 🔗 Full report: [will be added]"

Respond with ONLY the post text (no quotes, no explanation, no markdown).
"""


def generate_post(report: Dict[str, Any], filter_result: Dict[str, Any]) -> Optional[str]:
    """
    Generate a Bluesky post for a newsworthy report
    
    Args:
        report: Report dictionary
        filter_result: Result from filter_report() with score, reason, etc.
    
    Returns:
        Post text (string) or None on error
    """
    try:
        # Format dollar amount
        dollar_amount = filter_result.get('dollar_amount')
        if dollar_amount:
            if dollar_amount >= 1_000_000:
                dollar_str = f"${dollar_amount / 1_000_000:.1f}M"
            elif dollar_amount >= 1_000:
                dollar_str = f"${dollar_amount / 1_000:.0f}K"
            else:
                dollar_str = f"${dollar_amount}"
        else:
            dollar_str = "N/A"
        
        # Build prompt
        prompt = SUMMARY_PROMPT_TEMPLATE.format(
            title=report.get('title', 'Unknown'),
            agency_name=report.get('agency_name', 'Unknown Agency'),
            report_type=report.get('report_type', 'Report'),
            published_date=report.get('published_date', 'Unknown'),
            reason=filter_result.get('reason', 'No reason provided'),
            dollar_amount=dollar_str,
            criminal='Yes' if filter_result.get('criminal') else 'No',
            topics=', '.join(filter_result.get('topics', [])),
            abstract=report.get('abstract', '')[:800]  # Truncate long abstracts
        )
        
        # Call LLM with higher temperature for creativity
        response = call_gpt(
            prompt=prompt,
            max_tokens=150,
            temperature=0.7  # Higher = more creative/varied
        )
        
        if not response:
            logger.error(f"LLM returned no response for summary: {report.get('title', 'Unknown')[:50]}")
            return None
        
        # Clean up response
        post_text = response.strip()
        
        # Remove any quotes if LLM added them
        if post_text.startswith('"') and post_text.endswith('"'):
            post_text = post_text[1:-1]
        
        # Replace placeholder with actual URL
        actual_url = report.get('url', 'https://www.oversight.gov')
        post_text = post_text.replace('[will be added]', actual_url)
        
        # Validate length (Bluesky limit is 300 chars)
        if len(post_text) > 300:
            logger.warning(f"Generated post too long ({len(post_text)} chars), truncating")
            # Try to truncate gracefully
            post_text = post_text[:280] + "... 🔗 " + actual_url
        
        logger.info(f"✅ Generated post ({len(post_text)} chars): {post_text[:80]}...")
        
        return post_text
    
    except Exception as e:
        logger.error(f"Error generating post: {e}")
        return None


def generate_fallback_post(report: Dict[str, Any]) -> str:
    """
    Generate a simple fallback post if LLM fails
    
    Args:
        report: Report dictionary
    
    Returns:
        Simple post text
    """
    title = report.get('title', 'Inspector General Report')
    agency = report.get('agency_name', 'Federal Agency')
    url = report.get('url', 'https://www.oversight.gov')
    
    # Truncate title if too long
    if len(title) > 150:
        title = title[:147] + "..."
    
    post = f"🚨 New IG Report: {title}\n\n{agency}\n\n🔗 {url}"
    
    return post


# Test function
if __name__ == '__main__':
    print("Testing LLM summary generator...")
    
    # Test report and filter result
    test_report = {
        'report_id': 'test-001',
        'title': 'Investigation Substantiates Sexual Harassment Allegations Against VA Medical Center Chief of Staff',
        'agency_name': 'Department of Veterans Affairs',
        'agency_id': 'VA',
        'report_type': 'Investigation',
        'published_date': '2024-01-15',
        'abstract': 'An investigation substantiated allegations that the Chief of Staff engaged in sexual harassment...',
        'url': 'https://www.oversight.gov/report/va/investigation-substantiates-sexual-harassment'
    }
    
    test_filter_result = {
        'newsworthy': True,
        'score': 8,
        'reason': 'Sexual harassment by senior official, substantiated investigation',
        'dollar_amount': None,
        'criminal': False,
        'topics': ['misconduct', 'healthcare']
    }
    
    post = generate_post(test_report, test_filter_result)
    
    if post:
        print(f"\n✅ Generated post ({len(post)} characters):")
        print(f"\n{post}")
        print(f"\n{'✅' if len(post) <= 300 else '❌'} Within 300 character limit")
    else:
        print("\n❌ Failed to generate post")
        print("\n🔄 Fallback post:")
        print(f"\n{generate_fallback_post(test_report)}")
