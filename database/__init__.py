"""
Database package for IG Reports Bot
"""

from .db import (
    get_connection,
    initialize_database,
    upsert_report,
    get_unfiltered_reports,
    get_unposted_reports,
    mark_filtered,
    mark_posted,
    get_report_by_id,
    get_recent_reports,
    get_stats
)

__all__ = [
    'get_connection',
    'initialize_database',
    'upsert_report',
    'get_unfiltered_reports',
    'get_unposted_reports',
    'mark_filtered',
    'mark_posted',
    'get_report_by_id',
    'get_recent_reports',
    'get_stats'
]
