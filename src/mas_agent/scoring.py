"""Lead scoring for Mas Cabinets.

Score is 0-100, built from four signals:

* Focus area (0-30): Florida only — Apopka/Orlando + Lake, Orange, Osceola,
  Polk, Seminole counties. Out-of-area leads are flagged and capped.
* Service match (0-25): does the lead want something Mas actually does?
* Intent signals (0-25): urgency words, timeline, and a realistic budget.
* Contact completeness (0-20): name / email / phone — can we reach them today?
"""

from __future__ import annotations

from .config import BusinessProfile
from .models import Lead, ScoreResult

# Keywords that suggest a lead is ready to move, not just browsing.
URGENCY_WORDS = (
    "asap", "urgent", "immediately", "right away", "this week", "this month",
    "ready to start", "ready to move", "need it done", "contractor fell through",
    "water damage", "leak", "broken", "closing", "moving in", "before the holidays",
)

# Map loose lead wording onto the canonical Mas services.
SERVICE_ALIASES = {
    "kitchen cabinets": "custom kitchen cabinets",
    "cabinets": "custom kitchen cabinets",
    "kitchen": "custom kitchen cabinets",
    "kitchen remodel": "kitchen remodeling",
    "kitchen renovation": "kitchen remodeling",
    "remodel": "kitchen remodeling",
    "vanity": "bathroom vanities",
    "bathroom": "bathroom vanities",
    "closet": "custom closets",
    "closets": "custom closets",
    "built-in": "built-in storage",
    "builtin": "built-in storage",
    "storage": "built-in storage",
    "shelving": "built-in storage",
    "general contractor": "general contracting",
    "contracting": "general contracting",
    "renovation": "general contracting",
}


def _normalise(text: str) -> str:
    return " ".join(text.lower().replace("-", " ").split())


def matched_service(lead: Lead, profile: BusinessProfile) -> str | None:
    """Return the canonical Mas service the lead is asking for, if any."""
    wanted = _normalise(lead.service)
    haystack = wanted + " " + _normalise(lead.message)
    for service in profile.services:
        if _normalise(service) in wanted:
            return service
    # Longest alias first, so "kitchen remodel" beats the shorter "kitchen".
    for alias, canonical in sorted(
        SERVICE_ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True
    ):
        if alias in wanted or (not wanted and alias in haystack):
            return canonical
    return None


def in_focus_area(lead: Lead, profile: BusinessProfile) -> bool:
    """True when the lead is in the Florida focus area."""
    if lead.state and lead.state != profile.focus_state:
        return False
    county = lead.county.strip().title().removesuffix(" County").strip()
    if county:
        return county in profile.focus_counties
    city = lead.city.strip().title()
    if city:
        return city in profile.focus_cities
    # No location at all: cannot confirm focus area.
    return False


def score_lead(lead: Lead, profile: BusinessProfile | None = None) -> ScoreResult:
    profile = profile or BusinessProfile()
    reasons: list[str] = []
    flags: list[str] = []
    score = 0

    # --- Focus area (0-30) -------------------------------------------------
    if in_focus_area(lead, profile):
        score += 30
        where = lead.county or lead.city or profile.focus_state
        reasons.append(f"In Florida focus area ({where}): +30")
    else:
        flags.append("out_of_area")
        if lead.state and lead.state != profile.focus_state:
            reasons.append(
                f"Outside Florida focus area (state: {lead.state}): +0 — "
                "New York / out-of-state work is not a current focus"
            )
        elif lead.city or lead.county:
            reasons.append(
                f"{lead.city or lead.county} is outside the focus counties/cities: +0"
            )
        else:
            reasons.append("No location given — focus area unconfirmed: +0")

    # --- Service match (0-25) ----------------------------------------------
    service = matched_service(lead, profile)
    if service:
        score += 25
        reasons.append(f"Service match — {service}: +25")
    elif lead.service:
        flags.append("service_unclear")
        reasons.append(f"Service '{lead.service}' is not a listed Mas service: +0")
    else:
        flags.append("service_unclear")
        reasons.append("No service specified: +0")

    # --- Intent: urgency + budget (0-25) ------------------------------------
    intent = 0
    text = _normalise(f"{lead.message} {lead.timeline}")
    hits = [w for w in URGENCY_WORDS if w in text]
    if hits:
        intent += 10
        reasons.append(f"Urgency signals ({', '.join(hits[:3])}): +10")
    timeline = _normalise(lead.timeline)
    if any(w in timeline for w in ("asap", "immediately", "this month", "this week", "ready")):
        intent += 5
        reasons.append("Timeline is near-term: +5")
    if lead.budget is not None:
        if lead.budget >= 10_000:
            intent += 10
            reasons.append(f"Budget stated (${lead.budget:,.0f}, project-scale): +10")
        elif lead.budget >= 3_000:
            intent += 6
            reasons.append(f"Budget stated (${lead.budget:,.0f}): +6")
        elif lead.budget > 0:
            intent += 2
            flags.append("low_budget")
            reasons.append(f"Budget stated (${lead.budget:,.0f}, small for custom work): +2")
    score += min(intent, 25)

    # --- Contact completeness (0-20) ----------------------------------------
    contact = 0
    if lead.name:
        contact += 6
    if lead.email and "@" in lead.email:
        contact += 7
    if lead.phone and sum(ch.isdigit() for ch in lead.phone) >= 7:
        contact += 7
    score += contact
    reasons.append(f"Contact completeness: +{contact} of 20")
    if contact < 14:
        flags.append("hard_to_reach")

    score = max(0, min(100, score))

    # --- Grade ---------------------------------------------------------------
    if "out_of_area" in flags:
        grade = "out_of_area"
        score = min(score, 40)  # out-of-focus leads never grade hot/warm
    elif score >= 75:
        grade = "hot"
    elif score >= 50:
        grade = "warm"
    else:
        grade = "cold"

    return ScoreResult(score=score, grade=grade, reasons=reasons, flags=flags)
