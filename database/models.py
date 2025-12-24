"""
Database Models for Multi-Agent Fake News Detection System
PostgreSQL and Neo4j schemas
"""
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class NewsItem:
    """PostgreSQL model for news items"""
    id: str
    headline: str
    text: str
    link: Optional[str] = None
    image_url: Optional[str] = None
    source_domain: Optional[str] = None
    detected_language: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NewsItem':
        return cls(**data)


@dataclass
class AnalysisResult:
    """PostgreSQL model for analysis results"""
    id: str
    news_item_id: str
    agent_id: str
    analysis_type: str  # visual, textual, source, etc.
    result_data: Dict[str, Any]
    confidence: float
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['result_data'] = json.dumps(self.result_data) if isinstance(self.result_data, dict) else self.result_data
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AnalysisResult':
        if isinstance(data.get('result_data'), str):
            data['result_data'] = json.loads(data['result_data'])
        return cls(**data)


@dataclass
class Verdict:
    """PostgreSQL model for verdicts"""
    id: str
    news_item_id: str
    verdict: str  # REAL, FAKE, UNSURE
    confidence: float
    confidence_interval: tuple
    criteria_scores: Dict[str, float]
    rationale: str
    judge_agent_id: str
    meta_evaluation_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['confidence_interval'] = list(self.confidence_interval)
        data['criteria_scores'] = json.dumps(self.criteria_scores) if isinstance(self.criteria_scores, dict) else self.criteria_scores
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Verdict':
        if isinstance(data.get('confidence_interval'), list):
            data['confidence_interval'] = tuple(data['confidence_interval'])
        if isinstance(data.get('criteria_scores'), str):
            data['criteria_scores'] = json.loads(data['criteria_scores'])
        return cls(**data)


@dataclass
class Correction:
    """PostgreSQL model for corrections"""
    id: str
    news_item_id: str
    original_claim: str
    accurate_information: Dict[str, Any]
    explanation: str
    educational_content: Dict[str, Any]
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['accurate_information'] = json.dumps(self.accurate_information) if isinstance(self.accurate_information, dict) else self.accurate_information
        data['educational_content'] = json.dumps(self.educational_content) if isinstance(self.educational_content, dict) else self.educational_content
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Correction':
        if isinstance(data.get('accurate_information'), str):
            data['accurate_information'] = json.loads(data['accurate_information'])
        if isinstance(data.get('educational_content'), str):
            data['educational_content'] = json.loads(data['educational_content'])
        return cls(**data)


# Neo4j Graph Models (for source relationships)
class SourceNode:
    """Neo4j node for sources"""
    def __init__(self, domain: str, credibility_score: float, source_type: str):
        self.domain = domain
        self.credibility_score = credibility_score
        self.source_type = source_type
    
    def to_cypher(self) -> str:
        return f"""
        MERGE (s:Source {{domain: '{self.domain}'}})
        SET s.credibility_score = {self.credibility_score},
            s.source_type = '{self.source_type}'
        RETURN s
        """


class Relationship:
    """Neo4j relationship between sources"""
    def __init__(self, source_domain: str, target_domain: str, relationship_type: str):
        self.source_domain = source_domain
        self.target_domain = target_domain
        self.relationship_type = relationship_type
    
    def to_cypher(self) -> str:
        return f"""
        MATCH (s1:Source {{domain: '{self.source_domain}'}})
        MATCH (s2:Source {{domain: '{self.target_domain}'}})
        MERGE (s1)-[r:{self.relationship_type}]->(s2)
        RETURN r
        """


# SQL Schema (PostgreSQL)
POSTGRES_SCHEMA = """
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
    news_item_id VARCHAR(255) REFERENCES news_items(id),
    agent_id VARCHAR(50) NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    result_data JSONB,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verdicts (
    id VARCHAR(255) PRIMARY KEY,
    news_item_id VARCHAR(255) REFERENCES news_items(id),
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
    news_item_id VARCHAR(255) REFERENCES news_items(id),
    original_claim TEXT NOT NULL,
    accurate_information JSONB,
    explanation TEXT,
    educational_content JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_news_items_source ON news_items(source_domain);
CREATE INDEX IF NOT EXISTS idx_news_items_created ON news_items(created_at);
CREATE INDEX IF NOT EXISTS idx_analysis_results_item ON analysis_results(news_item_id);
CREATE INDEX IF NOT EXISTS idx_verdicts_item ON verdicts(news_item_id);
CREATE INDEX IF NOT EXISTS idx_verdicts_verdict ON verdicts(verdict);
"""

