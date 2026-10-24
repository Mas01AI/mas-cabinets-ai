"""Agent orchestration: intake -> score -> draft -> optional HubSpot push."""

from __future__ import annotations

import json
from pathlib import Path

from .config import Settings, load_settings
from .followup import EmailDraft, draft_followup
from .hubspot import HubSpotClient
from .models import Lead, ScoreResult
from .scoring import score_lead


class MasAgent:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or load_settings()
        self.profile = self.settings.business
        self.hubspot = HubSpotClient(
            access_token=self.settings.hubspot_access_token,
            portal_id=self.settings.hubspot_portal_id,
        )

    # -- intake ---------------------------------------------------------------
    @staticmethod
    def load_leads(path: str | Path) -> list[Lead]:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = [data]
        return [Lead.from_dict(item) for item in data]

    # -- pipeline ---------------------------------------------------------------
    def process_lead(self, lead: Lead, push: bool = False) -> dict:
        score: ScoreResult = score_lead(lead, self.profile)
        draft: EmailDraft = draft_followup(
            lead, score, self.profile, from_addr=self.settings.work_email
        )

        hubspot_result = None
        if push:
            note = (
                f"Mas Agent: scored {score.score}/100 ({score.grade}). "
                f"Flags: {', '.join(score.flags) or 'none'}. "
                f"Service: {lead.service or 'n/a'}; "
                f"Location: {lead.city}, {lead.state}; "
                f"Source: {lead.source or 'n/a'}. "
                f"Follow-up draft generated from {self.settings.work_email}."
            )
            hubspot_result = self.hubspot.push_lead(lead, score, note)

        return {
            "lead": lead,
            "score": score,
            "draft": draft,
            "hubspot": hubspot_result,
        }

    def process_leads(self, leads: list[Lead], push: bool = False) -> list[dict]:
        return [self.process_lead(lead, push=push) for lead in leads]
