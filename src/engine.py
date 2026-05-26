"""Tracer engine — orchestrates trace pipeline."""
import asyncio
import logging
import os
import time
from dataclasses import dataclass

from src.agents import AgentRunner, AGENT_DESCRIPTORS, AgentConfig
from src.tracker import TokenTracker

logger = logging.getLogger("engine")


@dataclass
class EngineConfig:
    model: str
    max_depth: int
    min_hop_usd: float
    dust_threshold_usd: float

    @classmethod
    def from_env(cls):
        return cls(
            model=os.getenv("MIMO_MODEL", "mimo-v2.5-pro"),
            max_depth=int(os.getenv("MAX_DEPTH", "6")),
            min_hop_usd=float(os.getenv("MIN_HOP_USD", "100")),
            dust_threshold_usd=float(os.getenv("DUST_THRESHOLD_USD", "50")),
        )


class Engine:
    def __init__(self, tracker: TokenTracker):
        self.config = EngineConfig.from_env()
        self.tracker = tracker
        self.agent = AgentRunner(tracker=tracker, config=AgentConfig.from_env())
        self._started = time.time()

    async def stop(self):
        await self.agent.aclose()

    def uptime_seconds(self) -> int:
        return int(time.time() - self._started)

    def agent_descriptors(self) -> list:
        return AGENT_DESCRIPTORS

    async def trace(self, address: str) -> dict:
        # Stage 1 — tag the source
        tag = await self.agent.tag_address(address, context={})

        # Stage 2 — fetch outbound activity (stub; production calls RPC eth_getLogs etc)
        outbound = self._stub_outbound(address)

        # Stage 3 — walk the hop graph (BFS, depth-bounded)
        all_hops = []
        terminals = []
        frontier = [(address, 0)]
        seen = {address}

        while frontier and len(all_hops) < 100:
            current, depth = frontier.pop(0)
            if depth >= self.config.max_depth:
                terminals.append({"address": current, "depth": depth, "reason": "max_depth"})
                continue

            walk = await self.agent.walk_hops(current, outbound)
            hops = walk.get("hops", [])

            for hop in hops:
                hop_with_depth = {**hop, "depth": depth + 1, "from": current}

                # Classify each hop's primitive
                primitive_hint = hop.get("primitive_hint", "transfer")
                if primitive_hint == "bridge":
                    bridge = await self.agent.decode_bridge(hop)
                    hop_with_depth["bridge"] = bridge
                elif primitive_hint == "mixer":
                    mixer = await self.agent.detect_mixer(hop)
                    hop_with_depth["mixer"] = mixer
                    terminals.append({**hop_with_depth, "reason": "mixer_terminal"})
                elif primitive_hint == "swap":
                    swap = await self.agent.decode_swap(hop)
                    hop_with_depth["swap"] = swap

                all_hops.append(hop_with_depth)

                target = hop.get("to")
                if target and target not in seen:
                    seen.add(target)
                    frontier.append((target, depth + 1))

        # Stage 4 — resolve exchange terminals
        for t in terminals:
            if "address" in t:
                resolved = await self.agent.resolve_exchange(t["address"], [])
                t["exchange"] = resolved

        # Stage 5 — synthesize the trace
        synthesis = await self.agent.synthesize(address, all_hops, terminals)

        return {
            "source": address,
            "tag": tag,
            "hops": all_hops,
            "terminals": terminals,
            "synthesis": synthesis,
            "stats": {"hops_explored": len(all_hops), "terminals_found": len(terminals)},
        }

    @staticmethod
    def _stub_outbound(address: str) -> list[dict]:
        # Placeholder. Production code reads eth_getLogs and constructs the outbound list.
        return [
            {"tx_hash": f"0x{i:064x}", "to": f"0x{(i+1):040x}", "value_usd": 1000 * i}
            for i in range(1, 6)
        ]
