-- IG Reports Bot Database Schema
-- SQLite database for storing scraped reports, filter results, and posts

-- Main table for all scraped IG reports
CREATE TABLE IF NOT EXISTS ig_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Identifiers
    report_id TEXT NOT NULL UNIQUE,           -- Unique ID from Oversight.gov
    url TEXT NOT NULL,                        -- Link to full report landing page
    pdf_url TEXT,                             -- Direct link to PDF file
    
    -- Basic info
    agency_id TEXT NOT NULL,                  -- Short code: DOD, HHS, VA, etc.
    agency_name TEXT NOT NULL,                -- Full agency name
    title TEXT NOT NULL,                      -- Report title
    report_type TEXT,                         -- Audit, Investigation, Evaluation, etc.
    published_date DATE NOT NULL,             -- When IG published it
    
    -- Content
    abstract TEXT,                            -- Report abstract/summary from source
    pdf_text TEXT,                            -- Extracted text from PDF (first 20 pages)
    pdf_pages INTEGER,                        -- Number of pages extracted
    summary TEXT,                             -- LLM-generated plain English summary
    
    -- Metadata extracted by LLM
    topics TEXT,                              -- JSON array: ["fraud", "healthcare"]
    dollar_amount INTEGER,                    -- Dollar figure mentioned (null if none)
    criminal BOOLEAN DEFAULT 0,               -- Criminal investigation involved?
    
    -- Filtering pipeline
    passed_keyword_filter BOOLEAN DEFAULT 0,  -- Did it pass initial keyword filter?
    passed_llm_filter BOOLEAN DEFAULT 0,      -- Did LLM deem it newsworthy?
    llm_filter_reason TEXT,                   -- LLM's explanation for decision
    newsworthy_score INTEGER,                 -- 1-10 newsworthiness score from LLM
    
    -- Posting status
    posted BOOLEAN DEFAULT 0,                 -- Posted to Bluesky?
    posted_at TIMESTAMP,                      -- When posted
    post_text TEXT,                           -- Generated Bluesky post content
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Track individual posts to Bluesky
CREATE TABLE IF NOT EXISTS bot_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL,               -- FK to ig_reports
    post_uri TEXT NOT NULL,                   -- Bluesky post URI
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES ig_reports(id)
);

-- Agency information
CREATE TABLE IF NOT EXISTS agencies (
    id TEXT PRIMARY KEY,                      -- Short code: DOD, EPA, etc.
    name TEXT NOT NULL,                       -- Display name
    full_name TEXT,                           -- Official full name
    website TEXT,                             -- Agency website
    ig_website TEXT,                          -- IG office website
    common_topics TEXT                        -- JSON array of common topics
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_published_date ON ig_reports(published_date);
CREATE INDEX IF NOT EXISTS idx_agency_id ON ig_reports(agency_id);
CREATE INDEX IF NOT EXISTS idx_posted ON ig_reports(posted);
CREATE INDEX IF NOT EXISTS idx_newsworthy ON ig_reports(passed_llm_filter, newsworthy_score);
CREATE INDEX IF NOT EXISTS idx_report_id ON ig_reports(report_id);
CREATE INDEX IF NOT EXISTS idx_created_at ON ig_reports(created_at);
