#!/usr/bin/env python3
"""Example client for Chainsight Forensics.

Usage:
    python examples/client.py trace 0x1234...
    python examples/client.py hop 0xabc...txhash
    python examples/client.py stats
"""
from __future__ import annotations

import argparse
import json
import sys

import httpx

DEFAULT_BASE = "http://localhost:8000"


def main() -> int:
    parser = argparse.ArgumentParser(description="Chainsight Forensics client")
    sub = parser.add_subparsers(dest="cmd", required=True)

    tr = sub.add_parser("trace")
    tr.add_argument("address")
    tr.add_argument("--chain", default="ethereum")
    tr.add_argument("--max-depth", type=int, default=6)

    hp = sub.add_parser("hop")
    hp.add_argument("tx_hash")
    hp.add_argument("--chain", default="ethereum")

    sub.add_parser("stats")

    parser.add_argument("--base", default=DEFAULT_BASE)
    args = parser.parse_args()

    if args.cmd == "trace":
        r = httpx.get(
            f"{args.base}/api/trace/{args.address}",
            params={"chain": args.chain, "max_depth": args.max_depth},
            timeout=300,
        )
    elif args.cmd == "hop":
        r = httpx.get(f"{args.base}/api/hop/{args.tx_hash}",
                      params={"chain": args.chain}, timeout=120)
    elif args.cmd == "stats":
        r = httpx.get(f"{args.base}/api/stats", timeout=10)
    else:
        parser.print_help()
        return 2

    r.raise_for_status()
    print(json.dumps(r.json(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
