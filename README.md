# Multi-Agent Fake News Detection System

A comprehensive multi-agent system for detecting fake news using advanced AI techniques and debate framework.

## System Architecture

### Agent Layers

1. **Data Collection Layer**
   - `CrawlerAgent` (CR-A): Multi-source data collection
   - `SourceTrackerAgent` (STA): Source analysis and tracking

2. **Preprocessing Layer**
   - `PreprocessingAgent` (PP-A): Data normalization and cleaning

3. **Analysis Layer**
   - `VisualValidatorAgent` (VVA): Image content analysis
   - `TextualContextAgent` (TCA): Textual analysis

4. **Debate Framework**
   - `ClaimAgent` (CA): Supports claim validity
   - `ChallengeAgent` (CHA): Challenges the claim
   - `RefuterAgent` (RA): Refutes challenges

5. **Decision Layer**
   - `JudgeAgent` (JA): Final decision making
   - `MetaEvaluatorAgent` (MEA): Meta-analysis of decisions

6. **Optimization Layer**
   - `OptimizerAgent` (OA): System performance optimization
   - `ReinforcementAgent` (RLA): Continuous learning

7. **Correction Layer**
   - `CorrectionAgent` (COA): Generates corrections for fake news

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Neo4j 5.14+
- Redis 7+

### Setup

1. Clone the repository:
```bash
cd ma-fnd
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

5. Run with Docker Compose:
```bash
docker-compose up -d
```

Or run manually:
```bash
# Start PostgreSQL, Neo4j, Redis (optional)
# Then run the API
python api.py
```

### Web Arayüzü

API'yi başlattıktan sonra web tarayıcınızda şu adrese gidin:
```
http://localhost:8000
```

Web arayüzü özellikleri:
- ✅ URL ile haber analizi
- ✅ 7 kategori altında sahte haber skorlama (0-100)
- ✅ En son kontrol edilen 5 haber
- ✅ Bu hafta en çok kontrol edilen haberler
- ✅ Gerçek haber tespitinde pozitif feedback

## Usage

### API Endpoints

#### Analyze News Item
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "headline": "Breaking: Major discovery announced",
    "text": "Article text here...",
    "link": "https://example.com/article"
  }'
```

#### Get Statistics
```bash
curl "http://localhost:8000/statistics"
```

#### Get Performance Metrics
```bash
# Overall summary
curl "http://localhost:8000/metrics/summary"

# Agent-specific metrics
curl "http://localhost:8000/metrics/agents"
curl "http://localhost:8000/metrics/agents?agent_id=JA"

# Phase-specific metrics
curl "http://localhost:8000/metrics/phases"
curl "http://localhost:8000/metrics/phases?phase_name=decision_making"
```

#### Health Check
```bash
curl "http://localhost:8000/health"
```

### Python Usage

```python
from orchestrator import Orchestrator

orchestrator = Orchestrator()

# Process a news item
item = {
    "id": "001",
    "headline": "News headline",
    "text": "Article text...",
    "link": "https://example.com"
}

result = orchestrator.process_news_item(item)
print(f"Verdict: {result['verdict']}")
print(f"Confidence: {result['confidence']}")
```

## Configuration

Environment variables (`.env`):
```
# OpenAI (for LLM judge)
OPENAI_API_KEY=your_openai_key

# Twitter/X API (choose one method)
# Method 1: Bearer Token (simpler, read-only)
TWITTER_BEARER_TOKEN=your_bearer_token

# Method 2: OAuth 1.0a (full access)
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost/fakenews
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
REDIS_URL=redis://localhost:6379
```

## Project Structure

```
ma-fnd/
├── agents/              # All agent implementations
│   ├── base_agent.py
│   ├── message_broker.py
│   ├── crawler_agent.py
│   ├── source_tracker_agent.py
│   ├── preprocessing_agent.py
│   ├── visual_validator_agent.py
│   ├── textual_context_agent.py
│   ├── claim_agent.py
│   ├── challenge_agent.py
│   ├── refuter_agent.py
│   ├── judge_agent_rule.py
│   ├── meta_evaluator_agent.py
│   ├── optimizer_agent.py
│   ├── reinforcement_agent.py
│   └── correction_agent.py
├── database/            # Database models and schemas
│   ├── models.py
│   └── schema.sql
├── orchestrator.py      # Main orchestration system
├── api.py              # FastAPI REST API
├── main.py             # Legacy CLI (backward compatible)
├── metrics.py          # Performance metrics tracking system
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose setup
└── README.md          # This file
```

## Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black agents/ orchestrator.py api.py
```

### Type Checking
```bash
mypy agents/ orchestrator.py api.py
```

## Features

- ✅ Multi-agent architecture with inter-agent communication
- ✅ Debate framework for argumentation
- ✅ Visual and textual analysis
- ✅ Source credibility tracking
- ✅ Meta-evaluation and bias detection
- ✅ Continuous learning and optimization
- ✅ Correction generation for fake news
- ✅ REST API for integration
- ✅ Docker support for easy deployment
- ✅ Performance metrics tracking and monitoring

## Roadmap

- [ ] Integration with BLIP-2 for image captioning
- [ ] Integration with CLIP for image-text matching
- [ ] Deepfake detection models
- [ ] Graph database integration for source relationships
- [ ] Advanced ML models (mBERT, XLM-R)
- [ ] Real-time monitoring dashboard
- [x] Performance metrics tracking

## License

MIT License

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

