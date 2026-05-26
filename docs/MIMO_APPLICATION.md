# Xiaomi MiMo Open Source Incentive — Application Draft

> Submission target: <https://platform.xiaomimimo.com/>
> Project: Chainsight Forensics
> GitHub: <https://github.com/divalkz/chainsight-forensics>

---

## Project name
Chainsight Forensics — on-chain fund tracing and exit-route reconstruction powered by Xiaomi MiMo V2.5 Pro

## Project URL / Repo
`https://github.com/divalkz/chainsight-forensics`

## Applicant role
DeFi infrastructure developer focused on compliance and investigation tooling. Hands-on with bridge protocols, mixer pools, and CEX clustering heuristics.

## AI tools currently used
- OpenClaw for orchestration
- Cursor + Claude Code for code editing
- Foundry / cast for transaction call graph decoding

## Underlying models used today
GPT-5 class for general reasoning. Claude Sonnet for long-context attribution work. Looking to adopt Xiaomi MiMo V2.5 Pro as the primary model for tracing because of `reasoning_content` audit traces and Token Plan pricing.

## Project description

### Problem
Stolen funds and laundering investigations require multi-hop reasoning across heterogeneous on-chain primitives — direct transfers, bridges, mixers, DEX swaps, CEX deposit clusters. Existing tools like Chainalysis and TRM are SaaS, expensive, and opaque about their attribution logic. Compliance teams that lack access need an open alternative that produces auditable trace documents.

Chainsight is open-source, multi-agent, and produces a structured trace document with confidence per hop and reasoning trace per attribution.

### Solution: Chainsight Forensics

A FastAPI gateway with seven MiMo-V2.5-Pro agents that collaborate on a compromised address:

1. address_tagger — classify source as hack victim, sanctioned, ransomware, exploiter, or normal user
2. hop_walker — BFS expansion through outbound transfers with dust pruning
3. bridge_decoder — decode LayerZero, Wormhole, Synapse, Across, Stargate, Hop, Connext, cBridge calldata
4. mixer_detector — Tornado Cash classic + Nova, Aztec, Privacy Pools deposit commitments
5. swap_decoder — DEX swap legs, classify token-laundering pattern (e.g., low-tracked stablecoin)
6. exchange_resolver — CEX deposit address clustering against known exchange labels
7. synthesis_reasoner — cross-correlate hops into a single attribution document

### Why MiMo V2.5 Pro specifically

- Long context — full transaction call graph + previous hop context fits in one call
- `reasoning_content` field — attribution audit trail is the primary deliverable
- Token Plan endpoint — predictable cost on continuous workload
- Pro tier reasoning — multi-hop attribution requires chain-of-thought across heterogeneous primitives
- OpenAI-compatible — drop-in via `MIMO_BASE_URL` + `MIMO_API_KEY`

### Token consumption profile

Per investigation:

| Stage | Calls | Tokens |
|---|---:|---:|
| address_tagger | 1 | ~3K |
| hop_walker (BFS depth 6) | ~40 | ~120K |
| bridge_decoder (per cross-chain hop) | ~12 | ~96K |
| mixer_detector (per suspicious deposit) | ~8 | ~64K |
| swap_decoder (per DEX leg) | ~25 | ~150K |
| exchange_resolver (per terminal address) | ~15 | ~75K |
| synthesis_reasoner | 1 | ~24K |
| Per investigation | ~102 | ~532K |

Operator workloads:
| Operator | Investigations / day | Daily tokens |
|---|---:|---:|
| Single forensic analyst | 5-10 | 2.5-5M |
| Compliance firm (10 analysts) | 50-100 | 25-50M |
| Vendor (100 analysts) | 500-1000 | 250-500M |

Realistic operating mode at scale: ~300M tokens / day, ~9B / month.

### Real run reference

Run against a Q1 2026 hack victim address ($4.2M drained):
- 7 agents coordinated, 94 calls, 501K tokens, 42s wall clock
- Trace converged through Curve USDC→USDT swap, Stargate ETH→Arbitrum bridge, Uniswap v3 USDT→ETH swaps, into Bybit + OKX deposit clusters at 50/50 split
- Synthesis reasoning_content surfaced fragmentation pattern + recommended compliance-request actions
- Confidence 0.88 (Bybit) / 0.86 (OKX) on terminal CEX attribution

Full breakdown in `docs/EXAMPLE_RUN.md`.

### What credits will be used for

- Phase 1 (week 1-2): Production rollout, Ethereum + Arbitrum + Base + Optimism support
- Phase 2 (week 3-4): Add Solana cross-chain support (Wormhole + Allbridge + Portal)
- Phase 3 (month 2): Browser extension (paste address → instant tag + trace summary)
- Phase 4 (month 3+): Public commitment cross-reference DB for mixer correlation across investigations

Daily target during scale-out: 4-8M tokens (single analyst), scaling toward 300M / day at firm-level adoption.

## Proof / artifacts

- Repo (public): <https://github.com/divalkz/chainsight-forensics>
- Working FastAPI backend: 5 endpoints (`/api/health`, `/api/agents`, `/api/trace/{address}`, `/api/hop/{tx_hash}`, `/api/stats`)
- Real run artifact in `docs/EXAMPLE_RUN.md` — 501K tokens, 9-hop trace, 0.88+ CEX attribution
- Architecture doc in `docs/ARCHITECTURE.md`
- Dockerfile for prod deploy
- Per-agent token tracking with SQLite persistence

## Estimated tier requested

- Plan Max — 700M tokens / month is the right starting tier for single-firm operating cadence
- During scale-out to vendor-level operations, request balance grant top-up
- Whichever fits the evaluation outcome

## Email for application
*(use the email on `platform.xiaomimimo.com` account; account holder is divalkz, primary contact aldivalk@gmail.com)*

## Notes for filling form

- Be specific about MiMo Pro tier — the reasoning workload genuinely needs Pro, not Instruct
- Mention `reasoning_content` field — attribution audit trail is the unique value prop
- Concrete real run with attribution + confidence > demo project
- Mention compliance use case — fits Xiaomi's positioning around AI-for-good

## Submission checklist
- [x] Push repo to GitHub (public)
- [ ] Verify email matches `platform.xiaomimimo.com` account
- [ ] Click "立即申请" on landing page
- [ ] Paste fields above into the form
- [ ] Wait ~3 business days for evaluation email
- [ ] Once approved: connect production RPC endpoints

## Post-approval roadmap
- Week 1: production telemetry on Ethereum
- Week 2: add Arbitrum + Base + Optimism
- Week 3: browser extension
- Week 4: Solana cross-chain support
- Month 2+: public commitment DB
