"""
InstaVest — SQLAlchemy ORM Models
Complete schema for the AI-native investment intelligence operating system.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Float, Boolean, Date, DateTime,
    ForeignKey, Index, JSON, Numeric, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.core.database import Base


# ============================================
# USERS
# ============================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    firebase_uid = Column(String(255), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    watchlists = relationship("Watchlist", back_populates="user")
    portfolios = relationship("Portfolio", back_populates="user")
    thesis_boards = relationship("ThesisBoard", back_populates="user")
    reports = relationship("Report", back_populates="user")
    checklist_items = relationship("BriefingChecklistItem", back_populates="user")


# ============================================
# COMPANIES
# ============================================

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    cik = Column(String(20), index=True)
    name = Column(String(500), nullable=False)
    exchange = Column(String(50))
    sector = Column(String(200))
    industry = Column(String(200))
    description = Column(Text)
    website = Column(String(500))
    country = Column(String(100))
    market_cap = Column(BigInteger)
    shares_outstanding = Column(BigInteger)
    source = Column(String(50))
    last_refreshed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================
# COMPANY METRICS
# ============================================

class CompanyMetric(Base):
    __tablename__ = "company_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    metric_key = Column(String(100), nullable=False)
    metric_value = Column(Float)
    period = Column(String(20))  # TTM, Q1-2026, FY-2025, etc.
    source = Column(String(50))  # fmp, sec, fred, computed
    source_priority = Column(Integer, default=50)  # lower = higher priority
    fetched_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_company_metrics_ticker_key", "ticker", "metric_key"),
        UniqueConstraint("ticker", "metric_key", "period", "source", name="uq_company_metric"),
    )


# ============================================
# MARKET DATA
# ============================================

class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    date = Column(Date, nullable=False)
    open = Column(Numeric(12, 4))
    high = Column(Numeric(12, 4))
    low = Column(Numeric(12, 4))
    close = Column(Numeric(12, 4))
    adjusted_close = Column(Numeric(12, 4))
    volume = Column(BigInteger)
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_market_prices_ticker_date"),
        Index("ix_market_prices_ticker_date", "ticker", "date"),
    )


class FinancialStatement(Base):
    __tablename__ = "financial_statements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    fiscal_year = Column(Integer, nullable=False)
    fiscal_period = Column(String(10), nullable=False)  # Q1, Q2, Q3, Q4, FY
    period_end_date = Column(Date)
    statement_type = Column(String(50), nullable=False)  # income, balance_sheet, cash_flow
    metric = Column(String(200), nullable=False)
    value = Column(Numeric(20, 4))
    unit = Column(String(20), default="USD")
    source = Column(String(50))
    filing_id = Column(Integer, ForeignKey("filings.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_fin_stmt_ticker_type", "ticker", "statement_type"),
        Index("ix_fin_stmt_ticker_year", "ticker", "fiscal_year"),
    )


class Filing(Base):
    __tablename__ = "filings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    cik = Column(String(20))
    accession_number = Column(String(50), unique=True)
    form_type = Column(String(20), nullable=False)  # 10-K, 10-Q, 8-K
    filing_date = Column(Date, nullable=False)
    report_date = Column(Date)
    filing_url = Column(String(1000))
    raw_text_path = Column(String(500))
    source = Column(String(50), default="sec_edgar")
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================
# DATA CACHE
# ============================================

class RawApiResponse(Base):
    __tablename__ = "raw_api_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False)
    endpoint = Column(String(200), nullable=False)
    cache_key = Column(String(500), nullable=False, unique=True, index=True)
    response_json = Column(JSON)
    response_hash = Column(String(64))
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)


# ============================================
# COMPANY BRAIN & INTELLIGENCE SNAPSHOTS
# ============================================

class CompanyBrain(Base):
    __tablename__ = "company_brains"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    profile_json = Column(JSON)          # company metadata
    financials_json = Column(JSON)       # key financial data
    valuation_json = Column(JSON)        # model outputs
    signals_json = Column(JSON)          # signal stack
    peers_json = Column(JSON)            # peer comparison
    risks_json = Column(JSON)            # risk factors
    catalysts_json = Column(JSON)        # growth catalysts
    ai_summary = Column(Text)            # AI executive summary
    ai_what_changed = Column(Text)       # AI what changed
    ai_synthesis = Column(Text)          # AI deep synthesis
    market_expectations_json = Column(JSON)  # reverse DCF output
    scenarios_json = Column(JSON)        # bull/base/bear
    health_score_json = Column(JSON)     # financial health
    confidence_score = Column(Float)
    thesis_status = Column(String(50))   # strengthening, stable, weakening
    last_refreshed = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CompanyBrainSnapshot(Base):
    __tablename__ = "company_brain_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    snapshot_json = Column(JSON, nullable=False)
    snapshot_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CompanyIntelligenceSnapshot(Base):
    __tablename__ = "company_intelligence_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    snapshot_payload_json = Column(JSON, nullable=False)
    data_sources_json = Column(JSON)
    source_confidence = Column(Float)
    source_discrepancies_json = Column(JSON)
    financial_version = Column(String(100))
    signal_version = Column(String(100))
    ai_version = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyIntelligenceSnapshot(Base):
    __tablename__ = "daily_intelligence_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(Date, nullable=False, unique=True, index=True)
    snapshot_payload_json = Column(JSON, nullable=False)
    macro_state = Column(String(100))
    top_signals_json = Column(JSON)
    top_thesis_changes_json = Column(JSON)
    top_portfolio_changes_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Evolving temporal intelligence extensions
    macro_summary = Column(Text, nullable=True)
    top_signal_changes_json = Column(JSON, nullable=True)
    intelligence_feed_json = Column(JSON, nullable=True)


# ============================================
# MODELS & SIGNALS
# ============================================

class ModelOutput(Base):
    __tablename__ = "model_outputs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    model_type = Column(String(50), nullable=False)  # reverse_dcf, peer_comp, health_score, scenario
    assumptions_json = Column(JSON)
    output_json = Column(JSON, nullable=False)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_model_output_ticker_type", "ticker", "model_type"),
    )


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(50), nullable=False)  # valuation_risk, peer_divergence, etc.
    severity = Column(String(20), nullable=False)      # low, medium, high, critical
    direction = Column(String(20), nullable=False)     # positive, negative, neutral
    title = Column(String(500), nullable=False)
    explanation = Column(Text)
    underlying_metrics_json = Column(JSON)
    model_output_id = Column(Integer, ForeignKey("model_outputs.id"), nullable=True)
    priority_score = Column(Float)                     # prioritization engine output
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_signals_ticker_type", "ticker", "signal_type"),
        Index("ix_signals_priority", "priority_score"),
    )


class SignalStateHistory(Base):
    """Tracks signal evolution over time — not isolated alerts but evolving conditions."""
    __tablename__ = "signal_state_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(50), nullable=False)
    prior_signal_strength = Column(Float)
    current_signal_strength = Column(Float)
    change_direction = Column(String(20))  # strengthening, weakening, stable, newly_emerged, resolved
    interpretation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_signal_history_ticker_type", "ticker", "signal_type"),
    )


# ============================================
# WATCHLISTS
# ============================================

class Watchlist(Base):
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="watchlists")
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=False)
    ticker = Column(String(20), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    watchlist = relationship("Watchlist", back_populates="items")

    __table_args__ = (
        UniqueConstraint("watchlist_id", "ticker", name="uq_watchlist_ticker"),
    )


# ============================================
# PORTFOLIOS
# ============================================

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio")


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    ticker = Column(String(20), nullable=False)
    shares = Column(Numeric(12, 4), nullable=False)
    average_cost = Column(Numeric(12, 4), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    portfolio = relationship("Portfolio", back_populates="holdings")

    __table_args__ = (
        UniqueConstraint("portfolio_id", "ticker", name="uq_holding_ticker"),
    )


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    snapshot_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_value = Column(Numeric(16, 4))
    risk_metrics_json = Column(JSON)
    ai_commentary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    portfolio = relationship("Portfolio", back_populates="snapshots")


# ============================================
# THESIS BOARDS
# ============================================

class ThesisBoard(Base):
    __tablename__ = "thesis_boards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="stable")  # strengthening, stable, weakening, broken
    conviction_score = Column(Float, default=50.0)
    time_horizon = Column(String(50))  # short, medium, long
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="thesis_boards")
    stocks = relationship("ThesisStock", back_populates="thesis_board", cascade="all, delete-orphan")
    assumptions = relationship("ThesisAssumption", back_populates="thesis_board", cascade="all, delete-orphan")
    timeline_events = relationship("ThesisTimelineEvent", back_populates="thesis_board", order_by="ThesisTimelineEvent.created_at.desc()")
    conviction_snapshots = relationship("ThesisConvictionSnapshot", back_populates="thesis_board", order_by="ThesisConvictionSnapshot.created_at.desc()")


class ThesisStock(Base):
    __tablename__ = "thesis_stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thesis_board_id = Column(Integer, ForeignKey("thesis_boards.id"), nullable=False)
    ticker = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    thesis_board = relationship("ThesisBoard", back_populates="stocks")

    __table_args__ = (
        UniqueConstraint("thesis_board_id", "ticker", name="uq_thesis_stock_ticker"),
    )


class ThesisAssumption(Base):
    __tablename__ = "thesis_assumptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thesis_board_id = Column(Integer, ForeignKey("thesis_boards.id"), nullable=False)
    ticker = Column(String(20), nullable=True)  # specific ticker this assumption applies to
    metric_key = Column(String(100), nullable=True)  # revenue_growth, operating_margin, fcf_yield, etc.
    operator = Column(String(10), nullable=True)  # >, >=, <, <=, =, between
    threshold_value = Column(Float, nullable=True)
    assumption_text = Column(Text, nullable=False)
    current_value = Column(Float, nullable=True)
    status = Column(String(50), default="passing")  # passing, warning, failing, unavailable
    last_evaluated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    thesis_board = relationship("ThesisBoard", back_populates="assumptions")

    __table_args__ = (
        Index("ix_thesis_assumption_board", "thesis_board_id"),
    )


class ThesisTimelineEvent(Base):
    __tablename__ = "thesis_timeline_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thesis_board_id = Column(Integer, ForeignKey("thesis_boards.id"), nullable=False)
    ticker = Column(String(20))
    event_type = Column(String(50), nullable=False)  # assumption_change, conviction_shift, signal, filing, earnings
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    what_changed = Column(Text)
    why_it_matters = Column(Text)
    impacted_assumptions_json = Column(JSON)
    severity = Column(String(20))  # low, medium, high, critical
    created_at = Column(DateTime, default=datetime.utcnow)

    thesis_board = relationship("ThesisBoard", back_populates="timeline_events")


class ThesisConvictionSnapshot(Base):
    """Point-in-time conviction score record for tracking thesis evolution."""
    __tablename__ = "thesis_conviction_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thesis_board_id = Column(Integer, ForeignKey("thesis_boards.id"), nullable=False)
    conviction_score = Column(Float, nullable=False)
    confidence_delta = Column(Float)  # change from prior snapshot
    supporting_signals_json = Column(JSON)
    weakening_signals_json = Column(JSON)
    regime_alignment = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    thesis_board = relationship("ThesisBoard", back_populates="conviction_snapshots")

    __table_args__ = (
        Index("ix_conviction_snapshot_board", "thesis_board_id"),
    )


# ============================================
# STATE CHANGE ENGINE
# ============================================

class StateChangeEvent(Base):
    """Generic state-change detector output — tracks accelerations, deteriorations, reversals."""
    __tablename__ = "state_change_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # thesis_board, assumption, signal, company
    entity_id = Column(Integer, nullable=False)
    prior_state_json = Column(JSON)
    current_state_json = Column(JSON)
    delta_summary = Column(Text)
    why_it_matters = Column(Text)
    severity = Column(String(20))  # low, medium, high, critical
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_state_change_entity", "entity_type", "entity_id"),
        Index("ix_state_change_created", "created_at"),
    )


# ============================================
# BRIEFING & CHECKLIST
# ============================================

class BriefingChecklistItem(Base):
    """Persisted morning briefing checklist items — state survives refresh."""
    __tablename__ = "briefing_checklist_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    briefing_date = Column(Date, nullable=False)
    item_key = Column(String(200), nullable=False)  # unique key for this checklist item
    title = Column(Text, nullable=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="checklist_items")

    __table_args__ = (
        UniqueConstraint("user_id", "briefing_date", "item_key", name="uq_checklist_item"),
        Index("ix_checklist_user_date", "user_id", "briefing_date"),
    )


# ============================================
# ASSUMPTION GRAPH (Future moat — placeholder)
# ============================================

class AssumptionNode(Base):
    __tablename__ = "assumption_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_type = Column(String(50), nullable=False)  # macro_factor, company_metric, industry_trend
    label = Column(String(500), nullable=False)
    description = Column(Text)
    current_value = Column(Float)
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AssumptionEdge(Base):
    __tablename__ = "assumption_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_node_id = Column(Integer, ForeignKey("assumption_nodes.id"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("assumption_nodes.id"), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # depends_on, impacts, correlated_with
    weight = Column(Float, default=1.0)
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================
# REPORTS
# ============================================

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String(20))
    report_type = Column(String(50), nullable=False)  # stock_memo, bull_bear, earnings, portfolio_risk, thesis_update
    title = Column(String(500), nullable=False)
    content_markdown = Column(Text)
    sources_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reports")


# ============================================
# EVENTS
# ============================================

class InternalEvent(Base):
    __tablename__ = "internal_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(100), nullable=False, index=True)
    ticker = Column(String(20), index=True)
    payload_json = Column(JSON)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_events_type_processed", "event_type", "processed"),
    )


# ============================================
# MARKET REGIME
# ============================================

class MarketRegimeSnapshot(Base):
    __tablename__ = "market_regime_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    regime = Column(String(50), nullable=False)  # risk_on, risk_off, growth_led, etc.
    confidence = Column(Float)
    factors_json = Column(JSON)
    snapshot_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class MacroIndicator(Base):
    __tablename__ = "macro_indicators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(String(50), nullable=False)  # FRED series ID
    name = Column(String(200), nullable=False)
    date = Column(Date, nullable=False)
    value = Column(Float)
    source = Column(String(50), default="FRED")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("series_id", "date", name="uq_macro_series_date"),
    )


# ============================================
# NARRATIVES (placeholder)
# ============================================

class Narrative(Base):
    __tablename__ = "narratives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="active")  # active, fading, dominant
    relevance_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NarrativeSnapshot(Base):
    __tablename__ = "narrative_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    narrative_id = Column(Integer, ForeignKey("narratives.id"), nullable=False)
    strength = Column(Float)
    snapshot_date = Column(Date, nullable=False)
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class CompanyNarrative(Base):
    __tablename__ = "company_narratives"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    narrative_id = Column(Integer, ForeignKey("narratives.id"), nullable=False)
    relevance = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================
# TEMPORAL INTELLIGENCE & EVOLUTION
# ============================================

class TemporalIntelligenceEvent(Base):
    """Tracks state evolution over time (change acceleration, weakening, strengthening, reversing, etc.)."""
    __tablename__ = "temporal_intelligence_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False, index=True)  # e.g., 'ticker', 'macro', 'thesis', 'portfolio'
    entity_id = Column(String(100), nullable=False, index=True)    # e.g., 'TSLA', 'US_INFLATION', board_id, portfolio_id
    prior_state_summary = Column(Text)
    current_state_summary = Column(Text, nullable=False)
    evolution_type = Column(String(50), nullable=False, index=True)  # accelerating, weakening, strengthening, reversing, diverging, stabilizing, deteriorating, improving
    acceleration_score = Column(Float, default=0.0)
    importance_score = Column(Float, default=0.0, index=True)
    why_it_matters = Column(Text)
    implication_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class ThesisEvolutionHistory(Base):
    """Tracks point-in-time thesis evolution and conviction change histories."""
    __tablename__ = "thesis_evolution_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thesis_board_id = Column(Integer, ForeignKey("thesis_boards.id"), nullable=False, index=True)
    prior_conviction = Column(Float)
    current_conviction = Column(Float, nullable=False)
    evolution_summary = Column(Text, nullable=False)
    strongest_supporting_signal = Column(Text)
    strongest_weakening_signal = Column(Text)
    macro_alignment = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    thesis_board = relationship("ThesisBoard")


class SignalTemporalAnalysis(Base):
    """Tracks signal recurrence, sensitivity, persistence, and regime sensitivity over time."""
    __tablename__ = "signal_temporal_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(100), nullable=False, index=True)
    persistence_score = Column(Float, default=0.0)
    acceleration_score = Column(Float, default=0.0)
    regime_sensitivity = Column(String(100))
    confidence_trend = Column(String(50))  # e.g., 'improving', 'stable', 'deteriorating'
    interpretation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
