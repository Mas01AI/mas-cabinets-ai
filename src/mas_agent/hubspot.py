"""HubSpot CRM client for the Mas Cabinets agent.

Uses only the standard library (urllib) against the HubSpot CRM v3 API for
portal "MAS Remodeling and Construction" (portal ID 247703427).

If no HUBSPOT_ACCESS_TOKEN is configured, every method runs in DRY-RUN mode:
it prints/returns exactly what it would do and makes no network calls, so the
whole agent works end-to-end with zero credentials.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

API_BASE = "https://api.hubapi.com"


class HubSpotClient:
    def __init__(self, access_token: str = "", portal_id: str = "247703427"):
        self.access_token = access_token.strip()
        self.portal_id = portal_id
        self.dry_run = not self.access_token

    # -- internals -----------------------------------------------------------
    def _dry(self, action: str, payload: dict) -> dict:
        print(
            f"[hubspot:dry-run] No HUBSPOT_ACCESS_TOKEN set — would {action}: "
            f"{json.dumps(payload)[:300]}"
        )
        return {"dry_run": True, "action": action, "payload": payload, "id": None}

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(
            f"{API_BASE}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise RuntimeError(f"HubSpot API {method} {path} -> {exc.code}: {detail}") from exc

    # -- public API ------------------------------------------------------------
    def search_contact_by_email(self, email: str) -> dict | None:
        """Return the HubSpot contact for an email, or None if not found."""
        if not email:
            return None
        if self.dry_run:
            self._dry("search contacts by email", {"email": email})
            return None
        body = {
            "filterGroups": [
                {"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}
            ],
            "properties": ["firstname", "lastname", "email", "phone"],
            "limit": 1,
        }
        result = self._request("POST", "/crm/v3/objects/contacts/search", body)
        results = result.get("results", [])
        return results[0] if results else None

    def create_contact(self, lead, score: int | None = None) -> dict:
        parts = lead.name.split()
        properties = {
            "email": lead.email,
            "firstname": parts[0] if parts else "",
            "lastname": " ".join(parts[1:]) if len(parts) > 1 else "",
            "phone": lead.phone,
            "city": lead.city,
            "state": lead.state,
        }
        properties = {k: v for k, v in properties.items() if v}
        payload = {"properties": properties}
        if self.dry_run:
            return self._dry("create contact", payload)
        return self._request("POST", "/crm/v3/objects/contacts", payload)

    def create_deal(self, lead, score_result=None, contact_id: str | None = None) -> dict:
        service = lead.service or "Custom cabinetry"
        name = f"{lead.name or 'New lead'} — {service}"
        amount = f"{lead.budget:.0f}" if lead.budget else ""
        properties = {
            "dealname": name,
            "pipeline": "default",
            "dealstage": "appointmentscheduled",
        }
        if amount:
            properties["amount"] = amount
        payload: dict = {"properties": properties}
        if contact_id:
            payload["associations"] = [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {"associationCategory": "HUBSPOT_DEFINED",
                         "associationTypeId": 3}  # deal -> contact
                    ],
                }
            ]
        if self.dry_run:
            return self._dry("create deal", payload)
        return self._request("POST", "/crm/v3/objects/deals", payload)

    def log_note(self, body: str, contact_id: str | None = None) -> dict:
        payload: dict = {"properties": {"hs_note_body": body}}
        if contact_id:
            payload["associations"] = [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {"associationCategory": "HUBSPOT_DEFINED",
                         "associationTypeId": 202}  # note -> contact
                    ],
                }
            ]
        if self.dry_run:
            return self._dry("log note", payload)
        return self._request("POST", "/crm/v3/objects/notes", payload)

    def update_deal_description(self, deal_id: str, text: str) -> dict:
        payload = {"properties": {"description": text}}
        if self.dry_run:
            return self._dry(f"set description on deal {deal_id}", payload)
        return self._request("PATCH", f"/crm/v3/objects/deals/{deal_id}", payload)

    def push_lead(self, lead, score_result, note_body: str) -> dict:
        """Full push: find-or-create contact, create deal, log a note.

        In dry-run mode returns a summary of everything it would have done.

        Notes fallback: HubSpot service keys offer no notes scopes, so if the
        note call is rejected the score summary is written to the deal's
        description instead (covered by the deals scopes) and the result
        records note_mode="deal_description".
        """
        existing = self.search_contact_by_email(lead.email)
        contact = existing or self.create_contact(lead, score_result.score)
        contact_id = contact.get("id") if isinstance(contact, dict) else None
        deal = self.create_deal(lead, score_result, contact_id=contact_id)
        note_mode = "note"
        try:
            note = self.log_note(note_body, contact_id=contact_id)
        except RuntimeError as exc:
            note = {"error": str(exc), "fallback": "deal_description"}
            note_mode = "deal_description"
            deal_id = deal.get("id") if isinstance(deal, dict) else None
            if deal_id:
                self.update_deal_description(deal_id, note_body)
        return {
            "dry_run": self.dry_run,
            "portal_id": self.portal_id,
            "contact_id": contact_id,
            "deal": deal,
            "note": note,
            "note_mode": note_mode,
        }
