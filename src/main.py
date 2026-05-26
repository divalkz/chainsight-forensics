"""Chainsight Forensics — FastAPI gateway."""
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from src.engine import Engine
from src.tracker import TokenTracker

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("chainsight")

engine: Engine | None = None
tracker = TokenTracker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    engine = Engine(tracker=tracker)
    logger.info("Chainsight ready (model=%s, max_depth=%d)", engine.config.model, engine.config.max_depth)
    yield
    await engine.stop()


app = FastAPI(
    title="Chainsight Forensics",
    description="On-chain fund tracing and exit-route reconstruction",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "provider": "xiaomi-mimo",
        "model": engine.config.model,
        "max_depth": engine.config.max_depth,
        "uptime_seconds": engine.uptime_seconds(),
    }


@app.get("/api/agents")
async def agents():
    return {"agents": engine.agent_descriptors()}


@app.get("/api/stats")
async def stats():
    return tracker.snapshot()


@app.post("/api/trace/{address}")
async def trace(address: str):
    try:
        return await engine.trace(address)
    except Exception as e:
        raise HTTPException(500, str(e))
