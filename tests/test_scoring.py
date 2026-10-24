"""Scoring tests — runnable with plain python or pytest.

Plain:  PYTHONPATH=src python tests/test_scoring.py
Pytest: PYTHONPATH=src python -m pytest tests/
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mas_agent.config import BusinessProfile
from mas_agent.models import Lead
from mas_agent.scoring import in_focus_area, matched_service, score_lead

PROFILE = BusinessProfile()


def test_strong_fl_kitchen_lead_is_hot():
    lead = Lead.from_dict({
        "name": "Sarah Mitchell", "email": "sarah@example.com",
        "phone": "(407) 555-0148", "city": "Apopka", "county": "Orange",
        "state": "FL", "service": "custom kitchen cabinets",
        "message": "Ready to start this month, water damage, need it done ASAP.",
        "budget": 35000, "timeline": "ASAP - this month", "source": "google",
    })
    result = score_lead(lead, PROFILE)
    assert result.grade == "hot", result
    assert result.score >= 75, result
    assert result.in_focus_area


def test_ny_lead_is_out_of_area_and_capped():
    lead = Lead.from_dict({
        "name": "Vinny Russo", "email": "v@example.com",
        "phone": "(631) 555-0173", "city": "Dix Hills", "county": "Suffolk",
        "state": "NY", "service": "custom kitchen cabinets",
        "message": "Want a quote.", "budget": 28000, "timeline": "this month",
    })
    result = score_lead(lead, PROFILE)
    assert result.grade == "out_of_area", result
    assert "out_of_area" in result.flags
    assert result.score <= 40, result
    assert not in_focus_area(lead, PROFILE)


def test_fl_bathroom_lead_scores_at_least_warm_or_reasonable():
    lead = Lead.from_dict({
        "name": "David Okafor", "email": "d@example.com",
        "phone": "(352) 555-0119", "city": "Mount Dora", "county": "Lake",
        "state": "FL", "service": "bathroom vanities",
        "message": "Custom double vanity for a master bathroom remodel.",
        "budget": 6500, "timeline": "within 2 months", "source": "website",
    })
    result = score_lead(lead, PROFILE)
    # 30 area + 25 service + 6 budget + 20 contact = 81 -> hot/warm, never cold.
    assert result.score >= 50, result
    assert result.grade in ("hot", "warm"), result


def test_service_aliases_match():
    lead = Lead(name="A", service="kitchen remodel")
    assert matched_service(lead, PROFILE) == "kitchen remodeling"
    lead = Lead(name="B", service="closet")
    assert matched_service(lead, PROFILE) == "custom closets"
    lead = Lead(name="C", service="roofing")
    assert matched_service(lead, PROFILE) is None


def test_no_contact_details_flagged():
    lead = Lead.from_dict({
        "city": "Orlando", "state": "FL", "service": "custom closets",
        "message": "Interested in a quote.",
    })
    result = score_lead(lead, PROFILE)
    assert "hard_to_reach" in result.flags
    assert result.score < 75


def test_focus_area_by_city_when_no_county():
    lead = Lead(city="Clermont", state="FL", service="cabinets")
    assert in_focus_area(lead, PROFILE)
    lead = Lead(city="Tampa", state="FL", service="cabinets", county="Hillsborough")
    assert not in_focus_area(lead, PROFILE)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL {test.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} tests passed")
    sys.exit(1 if failures else 0)
