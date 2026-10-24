"""Data models for the Mas Cabinets AI agent."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Lead:
    """A single inbound lead, whatever the source (web form, ad, referral)."""

    name: str = ""
    email: str = ""
    phone: str = ""
    city: str = ""
    county: str = ""
    state: str = ""
    service: str = ""          # what they want, e.g. "custom kitchen cabinets"
    message: str = ""          # free-text from the lead
    budget: float | None = None  # stated budget in USD, if any
    timeline: str = ""         # e.g. "ASAP", "within a month", "just researching"
    source: str = ""           # e.g. "website", "google", "facebook", "referral"

    @classmethod
    def from_dict(cls, data: dict) -> "Lead":
        budget = data.get("budget")
        if budget in ("", None):
            budget = None
        else:
            try:
                budget = float(str(budget).replace("$", "").replace(",", ""))
            except ValueError:
                budget = None
        return cls(
            name=str(data.get("name", "")).strip(),
            email=str(data.get("email", "")).strip(),
            phone=str(data.get("phone", "")).strip(),
            city=str(data.get("city", "")).strip(),
            county=str(data.get("county", "")).strip(),
            state=str(data.get("state", "")).strip().upper(),
            service=str(data.get("service", "")).strip(),
            message=str(data.get("message", "")).strip(),
            budget=budget,
            timeline=str(data.get("timeline", "")).strip(),
            source=str(data.get("source", "")).strip(),
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "city": self.city,
            "county": self.county,
            "state": self.state,
            "service": self.service,
            "message": self.message,
            "budget": self.budget,
            "timeline": self.timeline,
            "source": self.source,
        }

    @property
    def first_name(self) -> str:
        return self.name.split()[0] if self.name.split() else "there"


@dataclass
class ScoreResult:
    """Outcome of scoring a lead (see scoring.py)."""

    score: int                      # 0-100
    grade: str                      # "hot" | "warm" | "cold" | "out_of_area"
    reasons: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    @property
    def in_focus_area(self) -> bool:
        return "out_of_area" not in self.flags
