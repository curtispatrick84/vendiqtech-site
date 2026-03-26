import asyncio
import os
import logging

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import select

from database import engine, get_db, Base
from models import WaitlistEntry, BetaApplication
from email_service import send_notification

logging.basicConfig(level=logging.INFO)

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VendiQ API",
    docs_url="/api/docs" if os.getenv("ENABLE_DOCS", "false") == "true" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://vendiqtech.com",
        "https://www.vendiqtech.com",
        "http://localhost:8080",
    ],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ── Health ──
@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ── Auth (password verification for protected pages) ──
ACCESS_CODES = {
    "beta": os.getenv("BETA_ACCESS_CODE", "atlas1!"),
    "demo": os.getenv("DEMO_ACCESS_CODE", "atlas1!"),
    "compare": os.getenv("COMPARE_ACCESS_CODE", "atlas1!"),
}


class AuthRequest(BaseModel):
    code: str
    scope: str  # "beta" or "demo"


@app.post("/api/auth")
async def verify_access(data: AuthRequest):
    expected = ACCESS_CODES.get(data.scope)
    if not expected or data.code != expected:
        raise HTTPException(status_code=403, detail="Invalid access code.")
    return {"status": "ok"}


# ── Waitlist ──
class WaitlistRequest(BaseModel):
    email: EmailStr
    first_name: str
    role: str
    machine_count: str
    referral_source: str | None = None


@app.post("/api/waitlist", status_code=201)
async def join_waitlist(data: WaitlistRequest, db: Session = Depends(get_db)):
    existing = db.execute(
        select(WaitlistEntry).where(WaitlistEntry.email == data.email)
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=409, detail="This email is already on the waitlist.")

    entry = WaitlistEntry(
        email=data.email,
        first_name=data.first_name,
        role=data.role,
        machine_count=data.machine_count,
        referral_source=data.referral_source,
    )
    db.add(entry)
    db.commit()

    # Fire-and-forget email notification
    asyncio.create_task(
        send_notification(
            subject=f"[Join the Waitlist Lead] {data.first_name} — {data.role} ({data.machine_count} machines)",
            body_html=f"""
            <h2>New Waitlist Signup</h2>
            <table style="border-collapse:collapse;font-family:sans-serif;font-size:14px;">
                <tr><td style="padding:6px 12px;font-weight:bold;">Name</td><td style="padding:6px 12px;">{data.first_name}</td></tr>
                <tr><td style="padding:6px 12px;font-weight:bold;">Email</td><td style="padding:6px 12px;">{data.email}</td></tr>
                <tr><td style="padding:6px 12px;font-weight:bold;">Role</td><td style="padding:6px 12px;">{data.role}</td></tr>
                <tr><td style="padding:6px 12px;font-weight:bold;">Machines</td><td style="padding:6px 12px;">{data.machine_count}</td></tr>
                <tr><td style="padding:6px 12px;font-weight:bold;">Referral</td><td style="padding:6px 12px;">{data.referral_source or 'N/A'}</td></tr>
            </table>
            """,
        )
    )

    return {"status": "ok", "message": "You're on the list!"}


# ── Beta Application ──
class BetaApplicationRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    city: str
    state: str
    makes: str | None = None
    machine_count: str | None = None
    beta_count: str | None = None
    machine_age: str | None = None
    vend_types: str | None = None
    payment_type: str | None = None
    placements: str | None = None
    environment: str | None = None
    traffic: str | None = None
    tech_comfort: str | None = None
    device_type: str | None = None
    vms: str | None = None
    readiness: str | None = None
    revenue_share: str | None = None
    frustration: str | None = None
    prior_solutions: str | None = None
    anything_else: str | None = None
    referral: str | None = None
    deposit_acknowledged: str | None = None


@app.post("/api/beta-apply", status_code=201)
async def beta_apply(data: BetaApplicationRequest, db: Session = Depends(get_db)):
    entry = BetaApplication(**data.model_dump())
    db.add(entry)
    db.commit()

    asyncio.create_task(
        send_notification(
            subject=f"[Beta Application] {data.first_name} {data.last_name} — {data.city}, {data.state}",
            body_html=f"""
            <h2>New Beta Application</h2>
            <table style="border-collapse:collapse;font-family:sans-serif;font-size:14px;">
                <tr><td style="padding:6px 12px;font-weight:bold;">Name</td><td style="padding:6px 12px;">{data.first_name} {data.last_name}</td></tr>
                <tr><td style="padding:6px 12px;font-weight:bold;">Email</td><td style="padding:6px 12px;">{data.email}</td></tr>
                <tr><td style="padding:6px 12px;font-weight:bold;">Location</td><td style="padding:6px 12px;">{data.city}, {data.state}</td></tr>
                <tr><td style="padding:6px 12px;font-weight:bold;">Machines Owned</td><td style="padding:6px 12px;">{data.machine_count}</td></tr>
                <tr><td style="padding:6px 12px;font-weight:bold;">Beta Machines</td><td style="padding:6px 12px;">{data.beta_count}</td></tr>
                <tr><td style="padding:6px 12px;font-weight:bold;">Machine Age</td><td style="padding:6px 12px;">{data.machine_age}</td></tr>
                <tr><td style="padding:6px 12px;font-weight:bold;">Makes/Models</td><td style="padding:6px 12px;">{data.makes}</td></tr>
                <tr><td style="padding:6px 12px;font-weight:bold;">Payment Setup</td><td style="padding:6px 12px;">{data.payment_type}</td></tr>
                <tr><td style="padding:6px 12px;font-weight:bold;">Readiness</td><td style="padding:6px 12px;">{data.readiness}</td></tr>
            </table>
            """,
        )
    )

    return {"status": "ok", "message": "Application received!"}
