# Chainsight Forensics — Production Deploy

## Quick deploy (Docker)

```bash
docker build -t chainsight-forensics .
docker run -d --name chainsight \
  --restart unless-stopped \
  -p 8000:8000 \
  -e MIMO_API_KEY="$MIMO_API_KEY" \
  -e ETH_RPC="$ETH_RPC" \
  -e BASE_RPC="$BASE_RPC" \
  -e ARB_RPC="$ARB_RPC" \
  -e OP_RPC="$OP_RPC" \
  chainsight-forensics
```

Health check:

```bash
curl -s http://localhost:8000/api/health | jq
```

## systemd unit (Linux VPS)

`/etc/systemd/system/chainsight.service`:

```ini
[Unit]
Description=Chainsight Forensics
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=chainsight
Group=chainsight
WorkingDirectory=/opt/chainsight
EnvironmentFile=/opt/chainsight/.env
ExecStart=/opt/chainsight/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## RPC notes

- Use paid RPC (Alchemy, QuickNode, Infura) for trace_call and debug_traceTransaction
- Free public RPC tiers usually disable trace methods
- For BFS hop walker depth >= 4, you will hit rate limits without paid tier
- Recommended budget: 1 paid RPC per chain at the $50/mo tier covers single-analyst load

## Investigation export

Each completed trace is persisted to SQLite for audit:

```bash
sqlite3 data/traces.db "SELECT id, source, terminal_clusters, confidence, created_at FROM traces ORDER BY created_at DESC LIMIT 20"
```

Export to CSV for compliance handoff:

```bash
sqlite3 -header -csv data/traces.db "SELECT * FROM traces" > export.csv
```
