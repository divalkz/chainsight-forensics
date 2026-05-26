# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- pytest smoke tests
- GitHub Actions CI workflow (Python 3.11 + 3.12)
- Ruff linting in CI
- Badges in README
- CONTRIBUTING.md

## [0.1.0] - 2026-05-26

### Added
- FastAPI gateway with 5 endpoints
- 7 forensic agents: address_tagger, hop_walker, bridge_decoder, mixer_detector, swap_decoder, exchange_resolver, synthesis_reasoner
- BFS hop walker with dust pruning
- Bridge decoder coverage: LayerZero, Wormhole, Synapse, Across, Stargate, Hop, Connext, cBridge
- Mixer detector: Tornado Cash classic + Nova, Aztec, Privacy Pools
- Real-run artifact: 9-hop trace through Curve, Stargate, Uniswap v3 to Bybit + OKX
- Architecture diagram in `docs/ARCHITECTURE.md`
- Application draft in `docs/MIMO_APPLICATION.md`
- Dockerfile for production deploy
