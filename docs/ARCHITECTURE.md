# Architecture

Chainsight is a multi-agent on-chain forensic tracer. Six specialized agents run on `mimo-v2.5-pro` and collaborate to reconstruct fund exit routes from a compromised address.

## Pipeline

```
Source address (compromised)
  │
  ▼
address_tagger        classify the source
  │
  ▼
hop_walker (BFS)      expand outbound graph, prune dust
  │
  ▼ (per-hop classification, fan-out)
  │
  ├── bridge_decoder       cross-chain destination
  ├── mixer_detector       deposit commitment, terminate branch
  ├── swap_decoder         token-laundering legs
  └── exchange_resolver    CEX cluster identification
  │
  ▼
synthesis_reasoner    cross-correlate hops into attribution doc
  │
  ▼
Trace document (JSON)
```

## BFS bounds

- `max_depth = 6` — most stolen-fund traces terminate inside 6 hops (direct → bridge → swap → bridge → CEX deposit)
- `min_hop_usd = 100` — drop noise hops that do not advance the trace
- `dust_threshold_usd = 50` — prune dust before expansion to reduce token spend

The walker stops a branch when:
- A mixer terminal is hit (commitment is recorded for cross-reference)
- A CEX deposit cluster is identified
- `max_depth` is reached
- The hop value falls below `min_hop_usd`

## Why MiMo V2.5 Pro

| Feature | Value for this workload |
|---|---|
| Long context | Full transaction call graph + previous hop context fits in one call |
| `reasoning_content` | Attribution trace is the primary deliverable; reasoning visibility makes it auditable for compliance teams |
| Token Plan endpoint | Predictable cost on continuous workload |
| Pro tier reasoning | Multi-hop attribution requires chain-of-thought across heterogeneous primitives |
| OpenAI-compatible | Drop-in via `MIMO_BASE_URL` + `MIMO_API_KEY` |

## Token consumption

Per investigation:

| Stage | Calls | Tokens |
|---|---:|---:|
| address_tagger | 1 | ~3K |
| hop_walker (BFS, depth 6) | ~40 | ~120K |
| bridge_decoder (per cross-chain hop) | ~12 | ~96K |
| mixer_detector (per suspicious deposit) | ~8 | ~64K |
| swap_decoder (per DEX leg) | ~25 | ~150K |
| exchange_resolver (per terminal address) | ~15 | ~75K |
| synthesis_reasoner | 1 | ~24K |
| **Per investigation** | **~102** | **~532K** |

Operator workloads:
| Operator | Investigations / day | Daily tokens |
|---|---:|---:|
| Single forensic analyst | 5-10 | 2.5-5M |
| Compliance firm (10 analysts) | 50-100 | 25-50M |
| Global compliance vendor (100 analysts) | 500-1000 | 250-500M |

Realistic operating mode at scale: **300M tokens / day**, **~9B / month**.

## Detection details

### Bridge decoder

LayerZero / Wormhole / Synapse / Across / Stargate / Hop / Connext all use distinct calldata signatures. The decoder maps:
- Source tx → destination chain + address
- Bridge fee + protocol identification
- Settlement timing (estimated arrival on destination chain)

Output joins seamlessly with `hop_walker` on the destination chain to continue the trace.

### Mixer detector

Tornado Cash and forks emit deterministic deposit events with commitment hashes. The detector identifies:
- Pool denomination (0.1 ETH, 1 ETH, 10 ETH, 100 ETH for Tornado classic)
- Deposit commitment hash
- Block timestamp for downstream correlation against future withdrawals

Mixer deposits effectively terminate the trace branch — but the synthesis agent flags the deposit hash so downstream investigations can cross-reference if a withdrawal is linked.

### Exchange resolver

CEX deposit addresses are cycled aggressively. The resolver clusters addresses via:
- Withdrawal patterns (single-source funder = exchange hot wallet)
- Known exchange labels from public databases (Etherscan tags, Chainalysis public tags)
- Heuristic clustering (multiple deposits → single hot wallet within 24h)

Output: best-guess exchange + confidence + basis explanation.

## Failure modes

| Failure | Mitigation |
|---|---|
| Single agent timeout | Tenacity retry with exponential backoff (3 attempts) |
| Malformed JSON output | Regex match + fallback to raw text |
| RPC rate limit | Round-robin across configured endpoints |
| Bridge protocol unknown | Mark hop as `bridge_unknown`, continue trace via destination heuristics |
| Cyclic graph | BFS uses `seen` set on addresses, prevents revisit |

## Storage

SQLite (`./data/chainsight.db`) records:
- Per-call token usage (agent, model, prompt, completion, duration)
- Trace records (source, hops, terminals, synthesis)
- Mixer commitments for cross-investigation correlation

## Provider portability

```env
# Xiaomi MiMo Token Plan (default)
MIMO_BASE_URL=https://token-plan-sgp.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5-pro

# OpenAI fallback
MIMO_BASE_URL=https://api.openai.com/v1
MIMO_MODEL=gpt-4o
```
