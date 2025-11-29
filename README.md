# Lookuply Crawler Node

Decentralized crawler node for the Lookuply search engine.

## Features

- ✅ **Coordinator Integration**: Connects to central coordinator for URL distribution
- ✅ **Robots.txt Compliance**: Respects robots.txt and crawl delays
- ✅ **Content Extraction**: Extracts clean content using trafilatura
- ✅ **Link Discovery**: Discovers links for frontier expansion
- ✅ **Lightweight**: Deployable anywhere via Docker
- ✅ **Concurrent Processing**: Handles multiple URLs concurrently
- ✅ **Privacy-First**: No user tracking, no data collection

## Architecture

```
┌─────────────────────────────────────┐
│       Crawler Node                  │
├─────────────────────────────────────┤
│                                     │
│  ┌────────────┐  ┌───────────────┐ │
│  │ Crawler    │→│ Coordinator   │ │
│  │            │  │ Client        │ │
│  └────────────┘  └───────────────┘ │
│        ↓                            │
│  ┌────────────┐  ┌───────────────┐ │
│  │ Robots     │  │ Content       │ │
│  │ Handler    │  │ Extractor     │ │
│  └────────────┘  └───────────────┘ │
│        ↓                ↓           │
│  ┌────────────┐  ┌───────────────┐ │
│  │ HTTP       │  │ Link          │ │
│  │ Client     │  │ Discoverer    │ │
│  └────────────┘  └───────────────┘ │
└─────────────────────────────────────┘
```

## Components

- **CoordinatorClient**: Communicates with central coordinator API
- **RobotsHandler**: Checks robots.txt compliance and crawl delays
- **ContentExtractor**: Extracts meaningful content from HTML
- **LinkDiscoverer**: Finds links for crawling
- **Crawler**: Main orchestration logic

## Development

### Prerequisites

- Python 3.13+
- pip

### Setup

```bash
# Clone repository
git clone https://github.com/lookuply/crawler-node.git
cd crawler-node

# Install dependencies
pip install -r requirements-dev.txt

# Install in editable mode
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Linting

```bash
# Check code style
ruff check .

# Type check
mypy src/
```

### Running Locally

```bash
# Set environment variables
export COORDINATOR_URL=http://localhost:8000

# Run crawler
python -m crawler_node
```

## Docker

### Build

```bash
docker build -t crawler-node:latest .
```

### Run

```bash
docker run -e COORDINATOR_URL=http://coordinator:8000 crawler-node:latest
```

## Configuration

Configuration via environment variables:

```bash
# Coordinator
COORDINATOR_URL=http://localhost:8000
COORDINATOR_API_VERSION=v1

# Crawler settings
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=30
USER_AGENT=Lookuply-Crawler/0.1.0 (+https://lookuply.info)

# Politeness
RESPECT_ROBOTS_TXT=true
CRAWL_DELAY=1.0

# Content
EXTRACT_LINKS=true
MAX_CONTENT_LENGTH=10000000
```

See `.env.example` for full configuration options.

## Deployment

Deployment is automated via GitHub Actions:

1. Push to `main` branch
2. GitHub Actions runs tests
3. Builds Docker image
4. Deploys to Hetzner server

### Manual Deployment

```bash
# Build and push
docker build -t crawler-node:latest .
docker save crawler-node:latest | gzip > crawler-node.tar.gz
scp crawler-node.tar.gz server:/tmp/

# On server
docker load < /tmp/crawler-node.tar.gz
cd ~/lookuply/infrastructure
docker compose up -d crawler-node
```

## TDD Approach

All code developed using Test-Driven Development:

1. ✅ Write failing test
2. ✅ Implement minimal code to pass
3. ✅ Refactor
4. ✅ Repeat

**Coverage**: >70% (current: 24 tests)

## Testing

```bash
# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Specific module
pytest tests/unit/test_crawler.py -v
```

## License

MIT

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Status**: MVP Ready ✅
**Test Coverage**: >70%
**Code Quality**: Ruff + Mypy strict mode
