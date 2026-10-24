"""Mas Cabinets AI Agent — lead intake, scoring, follow-up drafts, HubSpot."""

from .agent import MasAgent
from .config import BusinessProfile, Settings, load_settings
from .models import Lead, ScoreResult
from .scoring import score_lead

__version__ = "0.1.0"
__all__ = [
    "MasAgent",
    "BusinessProfile",
    "Settings",
    "load_settings",
    "Lead",
    "ScoreResult",
    "score_lead",
]
