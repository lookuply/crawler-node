# Lookuply Crawler Node

Decentralized crawler node for the Lookuply search engine.

## Features

- Connects to central coordinator for URL distribution
- Respects robots.txt
- Extracts content using trafilatura
- Discovers links for frontier expansion
- Lightweight and deployable anywhere

## Development

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Lint
ruff check .
mypy .
```

## Deployment

Deployment is automated via GitHub Actions. Push to `main` branch to trigger deployment.

## Architecture

- **CoordinatorClient**: Communicates with central coordinator
- **RobotsHandler**: Checks robots.txt compliance
- **ContentExtractor**: Extracts meaningful content
- **LinkDiscoverer**: Finds links for crawling
- **Crawler**: Main crawling logic

## TDD Approach

All code is developed using Test-Driven Development:
1. Write failing test
2. Implement minimal code to pass
3. Refactor
4. Repeat

Target: >80% code coverage
