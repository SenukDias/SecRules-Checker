from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, findings, jobs, reports, stats, topology, upload
from app.db import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RuleScope", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(jobs.router)
app.include_router(findings.router)
app.include_router(topology.router)
app.include_router(reports.router)
app.include_router(admin.router)
app.include_router(stats.router)


@app.get("/health")
def health():
    return {"status": "ok"}
