# Contributing

## Getting started

```bash
git clone https://github.com/divalkz/chainsight-forensics.git
cd chainsight-forensics
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio ruff

cp .env.example .env
# Set MIMO_API_KEY + RPC endpoints per chain

pytest tests/ -v
uvicorn src.main:app --reload --port 8000
```

## Adding a new bridge or mixer adapter

1. Add detection logic in `src/agents.py` under `bridge_decoder` or `mixer_detector`
2. Add a fixture to `tests/fixtures/` showing the input + expected attribution
3. Wire it into the prompt template if needed
4. Open a PR with the trace example

## Pull request workflow

1. Fork from `main`
2. `ruff check src/ tests/`
3. `pytest tests/`
4. Open PR

## Reporting issues

Use GitHub issues. Include the source address, chain, time window, and what attribution was incorrect or missing.
