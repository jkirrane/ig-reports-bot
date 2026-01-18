#!/usr/bin/env python3
"""
Main daily pipeline for IG Reports Bot

This script:
1. Scrapes recent IG reports from Oversight.gov
2. Filters with keywords
3. Filters with LLM for newsworthiness
4. Generates summaries for newsworthy reports
5. Stores everything in database

Run with: python run_daily.py [--dry-run] [--days-back N]
"""

import argparse
import logging
import sys
from datetime import datetime

# Local imports
from database import initialize_database, upsert_report, get_unfiltered_reports, mark_filtered, get_stats
from scrapers import OversightGovScraper
from llm import filter_report, generate_post


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline.log')
    ]
)

logger = logging.getLogger(__name__)


def run_scraping(days_back: int = 1, dry_run: bool = False) -> int:
    """
    Scrape recent reports and save to database
    
    Args:
        days_back: How many days back to scrape
        dry_run: If True, don't save to database
    
    Returns:
        Number of reports scraped
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Starting scraping phase...")
    
    scraper = OversightGovScraper()
    reports = scraper.scrape_recent_reports(days_back=days_back)
    
    if not reports:
        logger.warning("No reports found")
        return 0
    
    logger.info(f"Found {len(reports)} reports")
    
    # Filter by keyword
    filtered_reports = [r for r in reports if r.get('passed_keyword_filter')]
    logger.info(f"  {len(filtered_reports)} passed keyword filter ({len(filtered_reports)/len(reports)*100:.1f}%)")
    
    # Save to database
    if not dry_run:
        saved_count = 0
        for report in reports:
            try:
                report_id = upsert_report(report)
                saved_count += 1
                logger.debug(f"Saved report {report_id}: {report['title'][:50]}")
            except Exception as e:
                logger.error(f"Failed to save report: {e}")
        
        logger.info(f"✅ Saved {saved_count}/{len(reports)} reports to database")
    else:
        logger.info("[DRY RUN] Would save reports to database")
    
    return len(reports)


def run_llm_filtering(limit: int = 100, dry_run: bool = False) -> int:
    """
    Run LLM filter on unfiltered reports
    
    Args:
        limit: Maximum number of reports to process
        dry_run: If True, don't save to database
    
    Returns:
        Number of reports filtered
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Starting LLM filtering phase...")
    
    # Get reports that need filtering
    reports = get_unfiltered_reports(limit=limit)
    
    if not reports:
        logger.info("No reports need filtering")
        return 0
    
    logger.info(f"Filtering {len(reports)} reports with LLM...")
    
    newsworthy_count = 0
    
    for i, report in enumerate(reports, 1):
        logger.info(f"[{i}/{len(reports)}] Filtering: {report['title'][:60]}...")
        
        # Filter with LLM
        filter_result = filter_report(report)
        
        if not filter_result:
            logger.warning(f"  ❌ Filter failed for report {report['id']}")
            continue
        
        # Log result
        if filter_result['newsworthy']:
            newsworthy_count += 1
            logger.info(f"  ✅ NEWSWORTHY (score: {filter_result['score']}/10): {filter_result['reason']}")
        else:
            logger.info(f"  ❌ Not newsworthy (score: {filter_result['score']}/10): {filter_result['reason']}")
        
        # Save filter result to database
        if not dry_run:
            try:
                mark_filtered(report['id'], filter_result)
            except Exception as e:
                logger.error(f"Failed to save filter result: {e}")
        else:
            logger.debug("[DRY RUN] Would save filter result to database")
    
    logger.info(f"✅ Filtered {len(reports)} reports: {newsworthy_count} newsworthy, {len(reports) - newsworthy_count} not newsworthy")
    
    return len(reports)


def run_summary_generation(dry_run: bool = False) -> int:
    """
    Generate summaries for newsworthy reports that don't have them yet
    
    Args:
        dry_run: If True, don't save to database
    
    Returns:
        Number of summaries generated
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Starting summary generation phase...")
    
    # Get newsworthy reports without summaries
    from database import get_connection
    
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT * FROM ig_reports 
        WHERE passed_llm_filter = 1 
        AND (summary IS NULL OR summary = '')
        AND posted = 0
        LIMIT 20
    """
    
    cursor.execute(query)
    reports = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not reports:
        logger.info("No reports need summaries")
        return 0
    
    logger.info(f"Generating summaries for {len(reports)} reports...")
    
    generated_count = 0
    
    for i, report in enumerate(reports, 1):
        logger.info(f"[{i}/{len(reports)}] Generating summary: {report['title'][:60]}...")
        
        # Get filter result from database
        import json
        filter_result = {
            'newsworthy': bool(report['passed_llm_filter']),
            'score': report.get('newsworthy_score', 7),
            'reason': report.get('llm_filter_reason', ''),
            'dollar_amount': report.get('dollar_amount'),
            'criminal': bool(report.get('criminal')),
            'topics': json.loads(report.get('topics', '[]')) if report.get('topics') else []
        }
        
        # Generate post
        post_text = generate_post(report, filter_result)
        
        if not post_text:
            logger.warning(f"  ❌ Failed to generate post")
            continue
        
        logger.info(f"  ✅ Generated ({len(post_text)} chars): {post_text[:80]}...")
        
        # Save to database
        if not dry_run:
            try:
                conn = get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE ig_reports 
                    SET summary = ?, post_text = ?, updated_at = ?
                    WHERE id = ?
                """, (post_text, post_text, datetime.now().isoformat(), report['id']))
                
                conn.commit()
                conn.close()
                
                generated_count += 1
            except Exception as e:
                logger.error(f"Failed to save summary: {e}")
        else:
            logger.debug("[DRY RUN] Would save summary to database")
            generated_count += 1
    
    logger.info(f"✅ Generated {generated_count}/{len(reports)} summaries")
    
    return generated_count


def main():
    """
    Main pipeline
    """
    parser = argparse.ArgumentParser(description='IG Reports Bot - Daily Pipeline')
    parser.add_argument('--dry-run', action='store_true', help='Run without saving to database')
    parser.add_argument('--days-back', type=int, default=1, help='How many days back to scrape (default: 1)')
    parser.add_argument('--skip-scraping', action='store_true', help='Skip scraping phase')
    parser.add_argument('--skip-filtering', action='store_true', help='Skip LLM filtering phase')
    parser.add_argument('--skip-summary', action='store_true', help='Skip summary generation phase')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("IG REPORTS BOT - Daily Pipeline")
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'}")
    logger.info(f"Days back: {args.days_back}")
    logger.info("=" * 60)
    
    # Initialize database
    if not args.dry_run:
        try:
            initialize_database()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return 1
    
    # Phase 1: Scraping
    if not args.skip_scraping:
        try:
            scrape_count = run_scraping(days_back=args.days_back, dry_run=args.dry_run)
            logger.info(f"Phase 1 complete: {scrape_count} reports scraped")
        except Exception as e:
            logger.error(f"Scraping phase failed: {e}", exc_info=True)
    else:
        logger.info("Skipping scraping phase")
    
    # Phase 2: LLM Filtering
    if not args.skip_filtering:
        try:
            filter_count = run_llm_filtering(limit=100, dry_run=args.dry_run)
            logger.info(f"Phase 2 complete: {filter_count} reports filtered")
        except Exception as e:
            logger.error(f"Filtering phase failed: {e}", exc_info=True)
    else:
        logger.info("Skipping filtering phase")
    
    # Phase 3: Summary Generation
    if not args.skip_summary:
        try:
            summary_count = run_summary_generation(dry_run=args.dry_run)
            logger.info(f"Phase 3 complete: {summary_count} summaries generated")
        except Exception as e:
            logger.error(f"Summary phase failed: {e}", exc_info=True)
    else:
        logger.info("Skipping summary phase")
    
    # Print stats
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 60)
    
    if not args.dry_run:
        stats = get_stats()
        logger.info(f"Database stats:")
        logger.info(f"  Total reports: {stats['total_reports']}")
        logger.info(f"  Passed keyword filter: {stats['passed_keyword_filter']}")
        logger.info(f"  Passed LLM filter: {stats['passed_llm_filter']}")
        logger.info(f"  Posted: {stats['posted']}")
        logger.info(f"  Pending posts: {stats['pending_posts']}")
        
        # Show LLM costs
        from llm import get_total_cost
        total_cost = get_total_cost()
        logger.info(f"  Total LLM cost: ${total_cost:.4f}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
