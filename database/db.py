"""
Database operations for IG Reports Bot
Handles all SQLite database interactions
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json


DB_PATH = os.path.join(os.path.dirname(__file__), 'ig_reports.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def get_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database
    Returns connection with row_factory set for dict-like access
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def initialize_database() -> None:
    """
    Create all tables from schema.sql if they don't exist
    Safe to call multiple times
    """
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, 'r') as f:
        schema_sql = f.read()
    
    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print(f"✅ Database initialized: {DB_PATH}")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        raise
    finally:
        conn.close()


def upsert_report(report: Dict[str, Any]) -> int:
    """
    Insert or update a report
    If report_id exists, update; otherwise insert
    
    Args:
        report: Dict with report data (must include report_id, url, agency_id, etc.)
    
    Returns:
        The report's database ID
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if report exists
        cursor.execute("SELECT id FROM ig_reports WHERE report_id = ?", (report['report_id'],))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing report
            report_db_id = existing['id']
            
            # Build update query for provided fields
            update_fields = []
            update_values = []
            
            for key, value in report.items():
                if key != 'report_id' and key != 'id':
                    update_fields.append(f"{key} = ?")
                    # Handle lists/dicts by converting to JSON
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value)
                    update_values.append(value)
            
            if update_fields:
                update_values.append(datetime.now().isoformat())
                update_values.append(report_db_id)
                
                query = f"UPDATE ig_reports SET {', '.join(update_fields)}, updated_at = ? WHERE id = ?"
                cursor.execute(query, update_values)
        else:
            # Insert new report
            columns = ['report_id', 'url', 'agency_id', 'agency_name', 'title', 
                      'report_type', 'published_date', 'abstract']
            values = []
            
            # Only include columns that are in the report dict
            actual_columns = []
            for col in columns:
                if col in report:
                    actual_columns.append(col)
                    value = report[col]
                    # Handle lists/dicts by converting to JSON
                    if isinstance(value, (list, dict)):
                        value = json.dumps(value)
                    values.append(value)
            
            placeholders = ', '.join(['?' for _ in actual_columns])
            query = f"INSERT INTO ig_reports ({', '.join(actual_columns)}) VALUES ({placeholders})"
            
            cursor.execute(query, values)
            report_db_id = cursor.lastrowid
        
        conn.commit()
        return report_db_id
    
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to upsert report {report.get('report_id')}: {e}")
        raise
    finally:
        conn.close()


def get_unfiltered_reports(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get reports that passed keyword filter but haven't been LLM filtered yet
    
    Args:
        limit: Maximum number of reports to return
    
    Returns:
        List of report dicts
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT * FROM ig_reports 
        WHERE passed_keyword_filter = 1 
        AND passed_llm_filter = 0
        AND newsworthy_score IS NULL
        ORDER BY published_date DESC
        LIMIT ?
    """
    
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_unposted_reports(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get reports that passed LLM filter but haven't been posted yet
    
    Args:
        limit: Maximum number of reports to return
    
    Returns:
        List of report dicts, sorted by newsworthy_score DESC
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT * FROM ig_reports 
        WHERE passed_llm_filter = 1 
        AND posted = 0
        ORDER BY newsworthy_score DESC, published_date DESC
        LIMIT ?
    """
    
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def mark_filtered(report_id: int, filter_result: Dict[str, Any]) -> None:
    """
    Update report with LLM filter results
    
    Args:
        report_id: Database ID of report
        filter_result: Dict with keys: newsworthy, score, reason, dollar_amount, criminal, topics
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            UPDATE ig_reports SET
                passed_llm_filter = ?,
                newsworthy_score = ?,
                llm_filter_reason = ?,
                dollar_amount = ?,
                criminal = ?,
                topics = ?,
                updated_at = ?
            WHERE id = ?
        """
        
        cursor.execute(query, (
            1 if filter_result.get('newsworthy') else 0,
            filter_result.get('score'),
            filter_result.get('reason'),
            filter_result.get('dollar_amount'),
            1 if filter_result.get('criminal') else 0,
            json.dumps(filter_result.get('topics', [])),
            datetime.now().isoformat(),
            report_id
        ))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to mark report {report_id} as filtered: {e}")
        raise
    finally:
        conn.close()


def mark_posted(report_id: int, post_text: str, post_uri: Optional[str] = None) -> None:
    """
    Mark report as posted to Bluesky
    
    Args:
        report_id: Database ID of report
        post_text: The text that was posted
        post_uri: Bluesky post URI (optional)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        now = datetime.now().isoformat()
        
        # Update report
        cursor.execute("""
            UPDATE ig_reports SET
                posted = 1,
                posted_at = ?,
                post_text = ?,
                updated_at = ?
            WHERE id = ?
        """, (now, post_text, now, report_id))
        
        # Add to bot_posts table if we have a URI
        if post_uri:
            cursor.execute("""
                INSERT INTO bot_posts (report_id, post_uri, posted_at)
                VALUES (?, ?, ?)
            """, (report_id, post_uri, now))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to mark report {report_id} as posted: {e}")
        raise
    finally:
        conn.close()


def get_report_by_id(report_db_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a single report by database ID
    
    Returns:
        Report dict or None if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM ig_reports WHERE id = ?", (report_db_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def get_recent_reports(days: int = 30, agency_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get reports from the last N days
    
    Args:
        days: Number of days to look back
        agency_id: Optional agency filter
    
    Returns:
        List of report dicts
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
    
    if agency_id:
        query = """
            SELECT * FROM ig_reports 
            WHERE published_date >= ? AND agency_id = ?
            ORDER BY published_date DESC
        """
        cursor.execute(query, (cutoff_date, agency_id))
    else:
        query = """
            SELECT * FROM ig_reports 
            WHERE published_date >= ?
            ORDER BY published_date DESC
        """
        cursor.execute(query, (cutoff_date,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_stats() -> Dict[str, Any]:
    """
    Get database statistics
    
    Returns:
        Dict with counts and metrics
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total reports
    cursor.execute("SELECT COUNT(*) as count FROM ig_reports")
    stats['total_reports'] = cursor.fetchone()['count']
    
    # Passed keyword filter
    cursor.execute("SELECT COUNT(*) as count FROM ig_reports WHERE passed_keyword_filter = 1")
    stats['passed_keyword_filter'] = cursor.fetchone()['count']
    
    # Passed LLM filter
    cursor.execute("SELECT COUNT(*) as count FROM ig_reports WHERE passed_llm_filter = 1")
    stats['passed_llm_filter'] = cursor.fetchone()['count']
    
    # Posted
    cursor.execute("SELECT COUNT(*) as count FROM ig_reports WHERE posted = 1")
    stats['posted'] = cursor.fetchone()['count']
    
    # Pending posts (filtered but not posted)
    cursor.execute("SELECT COUNT(*) as count FROM ig_reports WHERE passed_llm_filter = 1 AND posted = 0")
    stats['pending_posts'] = cursor.fetchone()['count']
    
    conn.close()
    
    return stats


# If run directly, initialize the database
if __name__ == '__main__':
    print("Initializing IG Reports Bot database...")
    initialize_database()
    
    # Show stats
    stats = get_stats()
    print(f"\nDatabase stats:")
    print(f"  Total reports: {stats['total_reports']}")
    print(f"  Passed keyword filter: {stats['passed_keyword_filter']}")
    print(f"  Passed LLM filter: {stats['passed_llm_filter']}")
    print(f"  Posted: {stats['posted']}")
    print(f"  Pending posts: {stats['pending_posts']}")
