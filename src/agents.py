"""Six forensic agents — fund tracing primitives."""
import json
import logging
import os
import re
from dataclasses import dataclass

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("agents")


@dataclass
class AgentConfig:
    base_url: str
    api_key: str
    model: str

    @classmethod
    def from_env(cls):
        key = os.getenv("MIMO_API_KEY")
        if not key:
            raise RuntimeError("MIMO_API_KEY not set")
        return cls(
            base_url=os.getenv("MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1"),
            api_key=key,
            model=os.getenv("MIMO_MODEL", "mimo-v2.5-pro"),
        )


AGENT_DESCRIPTORS = [
    {"name": "address_tagger", "role": "Classify source address: hack victim, sanctioned, ransomware, exploiter, mixer-output", "tokens_per_call": 3_000},
    {"name": "hop_walker", "role": "Expand outbound graph (BFS), prune dust, dedupe self-transfers", "tokens_per_call": 3_000},
    {"name": "bridge_decoder", "role": "Decode LayerZero/Wormhole/Synapse/Across calldata, output cross-chain destination", "tokens_per_call": 8_000},
    {"name": "mixer_detector", "role": "Identify Tornado/Aztec/Privacy-Pool deposits, output deposit commitment", "tokens_per_call": 8_000},
    {"name": "swap_decoder", "role": "Decode DEX swap routes, identify token-laundering legs", "tokens_per_call": 6_000},
    {"name": "exchange_resolver", "role": "Cluster CEX deposit addresses to known exchanges", "tokens_per_call": 5_000},
    {"name": "synthesis_reasoner", "role": "Cross-correlate hops into attribution trace, surface reasoning_content", "tokens_per_call": 24_000},
]


class AgentRunner:
    def __init__(self, tracker, config: AgentConfig | None = None):
        self.config = config or AgentConfig.from_env()
        self.tracker = tracker
        self.client = AsyncOpenAI(base_url=self.config.base_url, api_key=self.config.api_key)

    async def aclose(self):
        await self.client.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
    async def _chat(self, agent: str, system: str, user: str, max_tokens: int = 3000) -> dict:
        resp = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
            max_tokens=max_tokens,
        )
        usage = resp.usage
        self.tracker.record(
            agent=agent,
            prompt=usage.prompt_tokens if usage else 0,
            completion=usage.completion_tokens if usage else 0,
        )
        choice = resp.choices[0]
        content = choice.message.content or ""
        reasoning = getattr(choice.message, "reasoning_content", None)
        return {"content": content, "reasoning": reasoning}

    @staticmethod
    def _parse_json(text: str) -> dict:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            return {"parse_error": True, "raw": text[:500]}
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return {"parse_error": True, "raw": text[:500]}

    async def tag_address(self, address: str, context: dict) -> dict:
        system = (
            "You classify a source address for forensic investigation. Possible tags: "
            "hack_victim, sanctioned, ransomware, exploiter, mixer_output, normal_user, "
            "exchange_hot, exchange_cold, contract_treasury, unknown. "
            "Output JSON: {tag: string, confidence: 0-1, rationale: short string}."
        )
        r = await self._chat(
            "address_tagger",
            system,
            json.dumps({"address": address, "context": context}, separators=(",", ":")),
        )
        return self._parse_json(r["content"])

    async def walk_hops(self, address: str, outbound_txs: list[dict]) -> dict:
        system = (
            "You walk outbound transactions for a forensic trace. Filter dust (< $50), "
            "deduplicate self-transfers (same address on both sides), and group "
            "near-simultaneous transfers as a single behavioral hop. "
            "Output JSON: {hops: [{tx_hash, to, value_usd, primitive_hint}], pruned_count: int}."
        )
        r = await self._chat(
            "hop_walker",
            system,
            json.dumps({"address": address, "outbound": outbound_txs[:50]}, separators=(",", ":"))[:30_000],
        )
        return self._parse_json(r["content"])

    async def decode_bridge(self, tx: dict) -> dict:
        system = (
            "You decode a cross-chain bridge transaction. Identify the protocol "
            "(LayerZero, Wormhole, Synapse, Across, Stargate, Hop, Connext, cBridge), "
            "destination chain, destination address, and protocol fee. "
            "Output JSON: {protocol, destination_chain, destination_address, fee_usd, confidence: 0-1}."
        )
        r = await self._chat(
            "bridge_decoder",
            system,
            json.dumps(tx, separators=(",", ":"))[:25_000],
        )
        return self._parse_json(r["content"])

    async def detect_mixer(self, tx: dict) -> dict:
        system = (
            "You detect deposits to mixers (Tornado Cash classic, Tornado Nova, Aztec, "
            "Privacy Pools, Railway, etc). Identify the pool denomination, deposit commitment, "
            "and protocol. Output JSON: {is_mixer: bool, protocol, denomination_eth, commitment_hash, confidence: 0-1}."
        )
        r = await self._chat(
            "mixer_detector",
            system,
            json.dumps(tx, separators=(",", ":"))[:25_000],
        )
        return self._parse_json(r["content"])

    async def decode_swap(self, tx: dict) -> dict:
        system = (
            "You decode DEX swap calldata. Identify input token, output token, "
            "DEX (Uniswap v2/v3/v4, Curve, Balancer, Sushi, Maverick, etc), amount in/out, "
            "and whether the swap is a likely token-laundering hop (e.g. swap into "
            "lower-tracked stablecoin). Output JSON: {dex, input_token, output_token, "
            "amount_in_usd, amount_out_usd, laundering_confidence: 0-1}."
        )
        r = await self._chat(
            "swap_decoder",
            system,
            json.dumps(tx, separators=(",", ":"))[:25_000],
        )
        return self._parse_json(r["content"])

    async def resolve_exchange(self, address: str, recent_activity: list[dict]) -> dict:
        system = (
            "You cluster CEX deposit addresses to known exchanges. Use heuristics: "
            "single-source funder (hot wallet), known label (Etherscan tags), "
            "deposit pattern. Possible exchanges: Binance, Bybit, OKX, Coinbase, "
            "Kraken, Kucoin, Gate, Bitget, MEXC. Output JSON: "
            "{address, exchange, confidence: 0-1, basis: string}."
        )
        r = await self._chat(
            "exchange_resolver",
            system,
            json.dumps({"address": address, "recent": recent_activity[:30]}, separators=(",", ":"))[:25_000],
        )
        return self._parse_json(r["content"])

    async def synthesize(self, source: str, hops: list[dict], terminals: list[dict]) -> dict:
        system = (
            "You are the synthesis reasoner for a forensic fund-tracing pipeline. "
            "Given the source address, the multi-hop trace, and the terminal addresses, "
            "produce a unified attribution document. Output JSON: "
            "{summary: short paragraph, terminal_destinations: [{exchange, share_of_funds_pct}], "
            "key_hops: [hop_index numbers worth investigator attention], "
            "next_actions: [strings]}. Use chain-of-thought reasoning."
        )
        payload = {"source": source, "hops": hops[:60], "terminals": terminals[:30]}
        r = await self._chat(
            "synthesis_reasoner",
            system,
            json.dumps(payload, separators=(",", ":"))[:30_000],
            max_tokens=2000,
        )
        out = self._parse_json(r["content"])
        out["reasoning_trace"] = r.get("reasoning")
        return out
