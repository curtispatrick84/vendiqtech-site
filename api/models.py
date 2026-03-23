from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text

from database import Base


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    machine_count = Column(String, nullable=False)
    referral_source = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class BetaApplication(Base):
    __tablename__ = "beta_applications"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=True)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    makes = Column(Text, nullable=True)
    machine_count = Column(String, nullable=True)
    beta_count = Column(String, nullable=True)
    machine_age = Column(String, nullable=True)
    vend_types = Column(String, nullable=True)
    payment_type = Column(String, nullable=True)
    placements = Column(String, nullable=True)
    environment = Column(String, nullable=True)
    traffic = Column(String, nullable=True)
    tech_comfort = Column(String, nullable=True)
    device_type = Column(String, nullable=True)
    vms = Column(String, nullable=True)
    readiness = Column(String, nullable=True)
    revenue_share = Column(String, nullable=True)
    frustration = Column(Text, nullable=True)
    prior_solutions = Column(Text, nullable=True)
    anything_else = Column(Text, nullable=True)
    referral = Column(String, nullable=True)
    deposit_acknowledged = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
