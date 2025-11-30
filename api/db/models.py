from sqlalchemy import Column, DateTime, Float, Integer, String, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class RouterRun(Base):
    __tablename__ = "router_runs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    band = Column(String(20), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    latency_ms = Column(Float, nullable=False)
    router_latency_ms = Column(Float, nullable=True)
    provider_latency_ms = Column(Float, nullable=True)
    processing_latency_ms = Column(Float, nullable=True)

    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    cost_usd = Column(Float, nullable=False)
    baseline_cost_usd = Column(Float, nullable=False)
    savings_usd = Column(Float, nullable=False)
    alri_score = Column(Float, nullable=True)
    alri_tier = Column(String(50), nullable=True)
    status = Column(String(32), nullable=True, index=True)
    query_category = Column(String(50), nullable=True)
    query_category_conf = Column(Float, nullable=True)
    routing_efficient = Column(Boolean, nullable=True)
    counterfactual_cost_usd = Column(Float, nullable=True)
