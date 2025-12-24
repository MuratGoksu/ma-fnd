-- PostgreSQL Schema for Multi-Agent Fake News Detection System

CREATE TABLE IF NOT EXISTS news_items (
    id VARCHAR(255) PRIMARY KEY,
    headline TEXT NOT NULL,
    text TEXT NOT NULL,
    link VARCHAR(500),
    image_url VARCHAR(500),
    source_domain VARCHAR(255),
    detected_language VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analysis_results (
    id VARCHAR(255) PRIMARY KEY,
    news_item_id VARCHAR(255) REFERENCES news_items(id) ON DELETE CASCADE,
    agent_id VARCHAR(50) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    result_data JSONB,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verdicts (
    id VARCHAR(255) PRIMARY KEY,
    news_item_id VARCHAR(255) REFERENCES news_items(id) ON DELETE CASCADE,
    verdict VARCHAR(10) NOT NULL CHECK (verdict IN ('REAL', 'FAKE', 'UNSURE')),
    confidence FLOAT NOT NULL,
    confidence_interval FLOAT[],
    criteria_scores JSONB,
    rationale TEXT,
    judge_agent_id VARCHAR(50),
    meta_evaluation_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS corrections (
    id VARCHAR(255) PRIMARY KEY,
    news_item_id VARCHAR(255) REFERENCES news_items(id) ON DELETE CASCADE,
    original_claim TEXT NOT NULL,
    accurate_information JSONB,
    explanation TEXT,
    educational_content JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_news_items_source ON news_items(source_domain);
CREATE INDEX IF NOT EXISTS idx_news_items_created ON news_items(created_at);
CREATE INDEX IF NOT EXISTS idx_analysis_results_item ON analysis_results(news_item_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_agent ON analysis_results(agent_id);
CREATE INDEX IF NOT EXISTS idx_verdicts_item ON verdicts(news_item_id);
CREATE INDEX IF NOT EXISTS idx_verdicts_verdict ON verdicts(verdict);
CREATE INDEX IF NOT EXISTS idx_corrections_item ON corrections(news_item_id);

