"""Same-day follow-up email drafts.

Drafts only — nothing is ever sent by this module. A human (or a future,
explicitly approved sending step) decides what goes out. Drafts are written
from the Mas Cabinets work email and always carry the free-consultation offer.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import BusinessProfile
from .models import Lead, ScoreResult
from .scoring import matched_service


@dataclass
class EmailDraft:
    to: str
    from_addr: str
    subject: str
    body: str

    def render(self) -> str:
        return (
            f"From: {self.from_addr}\nTo: {self.to}\n"
            f"Subject: {self.subject}\n\n{self.body}"
        )


def _signature(profile: BusinessProfile) -> str:
    return (
        f"{profile.legal_name} ({profile.aka})\n"
        f"{profile.address}\n"
        f"Phone: {profile.phone}  |  {profile.website}\n"
        f"Hours: {profile.hours}"
    )


def draft_followup(
    lead: Lead,
    score: ScoreResult,
    profile: BusinessProfile,
    from_addr: str,
) -> EmailDraft:
    service = matched_service(lead, profile) or lead.service or "your project"
    first = lead.first_name

    if not score.in_focus_area:
        subject = f"Thanks for reaching out to Mas Cabinets, {first}"
        body = (
            f"Hi {first},\n\n"
            f"Thanks for contacting Mas Cabinets about {service}. "
            f"Right now our crews are focused on Central Florida "
            f"(Apopka/Orlando and the surrounding counties), so we wouldn't be "
            f"the right team to take on a project in "
            f"{lead.city}{', ' if lead.city and lead.state else ''}{lead.state} "
            f"at our normal standard.\n\n"
            f"If the project location changes — or if you have anything coming "
            f"up in Central Florida — we'd be glad to help with a "
            f"{profile.offer}.\n\n"
            f"Thanks again for thinking of us,\n"
            f"Mas Cabinets\n\n{_signature(profile)}"
        )
        return EmailDraft(lead.email, from_addr, subject, body)

    urgency = ""
    lead_text = f"{lead.message} {lead.timeline}".lower()
    if any(w in lead_text for w in ("asap", "urgent", "this month", "this week",
                                    "ready to start", "ready to move")):
        urgency = (
            "It sounds like you're ready to move, so we'll prioritize getting "
            "you booked in. "
        )

    subject = f"Your {service} project — free consultation from Mas Cabinets"
    body = (
        f"Hi {first},\n\n"
        f"Thanks for reaching out to Mas Cabinets about {service}"
        f"{f' in {lead.city}' if lead.city else ''}. "
        f"We design and build everything with {profile.differentiator}, so you "
        f"get a precise fit and a finish that lasts.\n\n"
        f"{urgency}The next step is a {profile.offer}. We'll measure, talk "
        f"through design and materials, and give you a clear written estimate "
        f"— no pressure and no obligation.\n\n"
        f"Reply to this email or call us at {profile.phone} and we'll find a "
        f"time that suits you. We're open {profile.hours}.\n\n"
        f"Looking forward to it,\n"
        f"Mas Cabinets\n\n{_signature(profile)}"
    )
    return EmailDraft(lead.email, from_addr, subject, body)
