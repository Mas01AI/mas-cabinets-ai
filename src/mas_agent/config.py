"""Configuration for the Mas Cabinets AI agent.

Loads settings from the process environment (and an optional local ``.env``
file) and holds the baked-in Mas Cabinets business profile. No secrets live
in this file — tokens come from the environment only.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv() -> None:
    """Minimal .env loader (stdlib only). Existing env vars win."""
    for candidate in (Path.cwd() / ".env", Path(__file__).resolve().parents[2] / ".env"):
        if candidate.is_file():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)
            break


@dataclass(frozen=True)
class BusinessProfile:
    """Everything the agent needs to know about Mas Cabinets."""

    legal_name: str = "MAS Remodeling and Construction LLC"
    aka: str = "Mas Cabinets"
    address: str = "535 Cooper Commerce Dr Ste 380, Apopka, FL 32703"
    city: str = "Apopka"
    state: str = "FL"
    phone: str = "(631) 710-1202"
    website: str = "mascabinets.com"
    work_email: str = "mseeriram@aol.com"
    hours: str = "Mon-Fri 8am-5pm, Sat 8am-2pm"
    offer: str = "free consultation and free estimate"
    differentiator: str = "CAD design and CNC precision fabrication"

    services: tuple[str, ...] = (
        "custom kitchen cabinets",
        "bathroom vanities",
        "custom closets",
        "built-in storage",
        "kitchen remodeling",
        "general contracting",
    )

    # Florida focus area only (New York is explicitly out of focus for now).
    focus_state: str = "FL"
    focus_counties: tuple[str, ...] = (
        "Lake",
        "Orange",
        "Osceola",
        "Polk",
        "Seminole",
    )
    focus_cities: tuple[str, ...] = (
        "Apopka", "Orlando", "Winter Park", "Altamonte Springs", "Ocoee",
        "Winter Garden", "Mount Dora", "Eustis", "Tavares", "Leesburg",
        "Clermont", "Sanford", "Lake Mary", "Oviedo", "Winter Springs",
        "Kissimmee", "St. Cloud", "Lakeland", "Winter Haven", "Auburndale",
        "Maitland", "Longwood", "Casselberry", "Forest City", "Wekiwa Springs",
    )

    hubspot_portal_name: str = "MAS Remodeling and Construction"
    hubspot_portal_id: str = "247703427"


@dataclass
class Settings:
    """Runtime settings sourced from the environment."""

    hubspot_access_token: str = ""
    work_email: str = "mseeriram@aol.com"
    openai_api_key: str = ""
    hubspot_portal_id: str = "247703427"
    business: BusinessProfile = field(default_factory=BusinessProfile)

    @property
    def hubspot_dry_run(self) -> bool:
        return not self.hubspot_access_token


def load_settings() -> Settings:
    _load_dotenv()
    business = BusinessProfile()
    return Settings(
        hubspot_access_token=os.environ.get("HUBSPOT_ACCESS_TOKEN", "").strip(),
        work_email=os.environ.get("WORK_EMAIL", business.work_email).strip()
        or business.work_email,
        openai_api_key=os.environ.get("OPENAI_API_KEY", "").strip(),
        hubspot_portal_id=os.environ.get(
            "MAS_HUBSPOT_PORTAL_ID", business.hubspot_portal_id
        ).strip(),
        business=business,
    )
