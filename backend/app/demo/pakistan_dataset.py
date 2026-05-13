"""Pakistan-pivot scholarship seed dataset (PRD §3).

Tier 1 — fully funded, high prestige (5):
  Chevening, Fulbright, DAAD, Commonwealth, HEC Overseas

Tier 2 — partial / merit aid, high acceptance (5):
  Edinburgh Global, U Toronto ISA, U Melbourne GRS, TU Delft Excellence,
  UBC ISA

GTA/GRA — 10 funded teaching/research assistantship positions seeded as
scholarships with funding_type='gta_gra'.

All entries land at record_state=PUBLISHED so they appear on the public
browse immediately. Pakistani nationals appear in citizenship_rules.
"""

from datetime import datetime, timezone

from app.models import RecordState


def _utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=timezone.utc)


PAKISTAN_SOURCE_REGISTRY_SEED = [
    {
        "source_key": "chevening-uk",
        "display_name": "Chevening Scholarships",
        "base_url": "https://www.chevening.org",
        "source_type": "official",
    },
    {
        "source_key": "usefp-fulbright-pk",
        "display_name": "USEFP Fulbright Pakistan",
        "base_url": "https://www.usefpakistan.org/fulbright",
        "source_type": "official",
    },
    {
        "source_key": "daad-germany",
        "display_name": "DAAD German Academic Exchange Service",
        "base_url": "https://www.daad.de",
        "source_type": "official",
    },
    {
        "source_key": "commonwealth-uk",
        "display_name": "Commonwealth Scholarship Commission",
        "base_url": "https://cscuk.fcdo.gov.uk",
        "source_type": "official",
    },
    {
        "source_key": "hec-overseas-pk",
        "display_name": "HEC Overseas Scholarship",
        "base_url": "https://www.hec.gov.pk",
        "source_type": "official",
    },
    {
        "source_key": "edinburgh-global",
        "display_name": "University of Edinburgh Global Scholarships",
        "base_url": "https://www.ed.ac.uk/student-funding",
        "source_type": "official",
    },
    {
        "source_key": "utoronto-isa",
        "display_name": "University of Toronto International Student Award",
        "base_url": "https://www.sgs.utoronto.ca/awards",
        "source_type": "official",
    },
    {
        "source_key": "melbourne-grs",
        "display_name": "University of Melbourne Graduate Research Scholarships",
        "base_url": "https://scholarships.unimelb.edu.au",
        "source_type": "official",
    },
    {
        "source_key": "tudelft-excellence",
        "display_name": "TU Delft Excellence Scholarships",
        "base_url": "https://www.tudelft.nl/en/education/practical-matters/scholarships",
        "source_type": "official",
    },
    {
        "source_key": "ubc-isa",
        "display_name": "UBC International Student Award",
        "base_url": "https://students.ubc.ca/enrolment/finances/awards-scholarships-bursaries",
        "source_type": "official",
    },
    {
        "source_key": "pk-gta-gra",
        "display_name": "GTA/GRA Positions for Pakistani Graduate Students",
        "base_url": "https://www.scholarai.pk/gta-gra",
        "source_type": "aggregated",
    },
]


def _tier_one_scholarships() -> list[dict]:
    return [
        {
            "source_key": "chevening-uk",
            "external_source_id": "chevening-pk-main",
            "title": "Chevening Scholarship",
            "provider_name": "UK Foreign, Commonwealth & Development Office",
            "country_code": "GB",
            "summary": (
                "Fully funded one-year UK master's scholarship for emerging leaders. "
                "Open to Pakistani nationals. Covers tuition, monthly living stipend, "
                "flights, and visa fees."
            ),
            "funding_summary": "Full: tuition + ~£18,000 living + flights + visa.",
            "funding_type": "full",
            "funding_amount_min": 25000,
            "funding_amount_max": 35000,
            "source_url": "https://www.chevening.org/scholarship/pakistan/",
            "source_document_ref": "chevening-pk-2026",
            "field_tags": ["all", "leadership"],
            "degree_levels": ["MS"],
            "citizenship_rules": ["PK"],
            "min_gpa_value": 3.0,
            "deadline_at": _utc(2026, 11, 5),
            "tags": ["fully_funded", "uk", "prestigious", "government"],
            "requires_gre": False,
            "requires_ielts": True,
        },
        {
            "source_key": "usefp-fulbright-pk",
            "external_source_id": "fulbright-pk-main",
            "title": "Fulbright Foreign Student Program (Pakistan)",
            "provider_name": "US Department of State / USEFP Pakistan",
            "country_code": "US",
            "summary": (
                "Fully funded master's and PhD program in the United States. "
                "Pakistan-specific cycle administered by USEFP. Covers tuition, "
                "living, health insurance, and round-trip flights."
            ),
            "funding_summary": "Full: ~$35,000/year + tuition + health + travel.",
            "funding_type": "full",
            "funding_amount_min": 35000,
            "funding_amount_max": 60000,
            "source_url": "https://www.usefpakistan.org/fulbright",
            "source_document_ref": "fulbright-pk-2026",
            "field_tags": ["all"],
            "degree_levels": ["MS", "PHD"],
            "citizenship_rules": ["PK"],
            "min_gpa_value": 3.0,
            "deadline_at": _utc(2026, 2, 28),
            "tags": ["fully_funded", "usa", "prestigious", "government", "no_gre_required"],
            "requires_gre": False,
            "requires_ielts": True,
        },
        {
            "source_key": "daad-germany",
            "external_source_id": "daad-pk-main",
            "title": "DAAD Scholarships (Pakistan)",
            "provider_name": "German Academic Exchange Service (DAAD)",
            "country_code": "DE",
            "summary": (
                "Fully funded German master's and PhD scholarships for Pakistani "
                "students in engineering, sciences, and development-related fields. "
                "Includes €934/month stipend, travel allowance, and health insurance."
            ),
            "funding_summary": "Full: €934/month stipend + travel + health.",
            "funding_type": "full",
            "funding_amount_min": 11000,
            "funding_amount_max": 16000,
            "source_url": "https://www.daad.de/en/study-and-research-in-germany/scholarships/",
            "source_document_ref": "daad-pk-2026",
            "field_tags": ["engineering", "sciences", "development"],
            "degree_levels": ["MS", "PHD"],
            "citizenship_rules": ["PK"],
            "min_gpa_value": 3.2,
            "deadline_at": _utc(2026, 10, 31),
            "tags": ["fully_funded", "germany", "stem", "low_tuition_country"],
            "requires_gre": False,
            "requires_ielts": True,
        },
        {
            "source_key": "commonwealth-uk",
            "external_source_id": "commonwealth-pk-main",
            "title": "Commonwealth Scholarship (Pakistan)",
            "provider_name": "Commonwealth Scholarship Commission UK",
            "country_code": "GB",
            "summary": (
                "Fully funded master's and PhD UK scholarships for Pakistani "
                "Commonwealth nationals in development-relevant subjects."
            ),
            "funding_summary": "Full: tuition + monthly living + flights.",
            "funding_type": "full",
            "funding_amount_min": 25000,
            "funding_amount_max": 50000,
            "source_url": "https://cscuk.fcdo.gov.uk/scholarships/commonwealth-scholarships-for-masters-study/",
            "source_document_ref": "commonwealth-pk-2026",
            "field_tags": ["development", "stem", "social_sciences"],
            "degree_levels": ["MS", "PHD"],
            "citizenship_rules": ["PK"],
            "min_gpa_value": 3.0,
            "deadline_at": _utc(2026, 12, 17),
            "tags": ["fully_funded", "uk", "commonwealth", "government"],
            "requires_gre": False,
            "requires_ielts": True,
        },
        {
            "source_key": "hec-overseas-pk",
            "external_source_id": "hec-overseas-main",
            "title": "HEC Overseas Scholarship for PhD",
            "provider_name": "Higher Education Commission, Pakistan",
            "country_code": "ZZ",  # multi-country
            "summary": (
                "Pakistani government PhD scholarship covering studies in approved "
                "host countries (UK, USA, Germany, Australia, others). Includes "
                "service obligation to return to Pakistan after completion."
            ),
            "funding_summary": "Full: tuition + monthly stipend + travel + family allowance.",
            "funding_type": "full",
            "funding_amount_min": 25000,
            "funding_amount_max": 70000,
            "source_url": "https://www.hec.gov.pk/english/scholarships/Pages/overseas.aspx",
            "source_document_ref": "hec-overseas-2026",
            "field_tags": ["stem", "social_sciences"],
            "degree_levels": ["PHD", "MS"],
            "citizenship_rules": ["PK"],
            "min_gpa_value": 3.0,
            "deadline_at": _utc(2026, 8, 31),
            "tags": ["fully_funded", "government", "pakistan_hec", "phd_focused"],
            "requires_gre": False,
            "requires_ielts": True,
        },
    ]


def _tier_two_scholarships() -> list[dict]:
    return [
        {
            "source_key": "edinburgh-global",
            "external_source_id": "edinburgh-global-pk",
            "title": "University of Edinburgh Global Scholarship",
            "provider_name": "University of Edinburgh",
            "country_code": "GB",
            "summary": "Partial tuition reduction for international postgraduate students.",
            "funding_summary": "Partial: £5,000 tuition reduction.",
            "funding_type": "partial",
            "funding_amount_min": 5000,
            "funding_amount_max": 5000,
            "source_url": "https://www.ed.ac.uk/student-funding/postgraduate/international/global",
            "source_document_ref": "edinburgh-global-2026",
            "field_tags": ["all"],
            "degree_levels": ["MS"],
            "citizenship_rules": ["PK"],
            "min_gpa_value": 3.3,
            "deadline_at": _utc(2026, 4, 30),
            "tags": ["partial", "uk", "tuition_award"],
            "requires_gre": False,
            "requires_ielts": True,
        },
        {
            "source_key": "utoronto-isa",
            "external_source_id": "utoronto-isa-pk",
            "title": "University of Toronto International Student Award",
            "provider_name": "University of Toronto",
            "country_code": "CA",
            "summary": "Need-based award for international graduate students.",
            "funding_summary": "Partial: CAD 10,000–40,000.",
            "funding_type": "partial",
            "funding_amount_min": 8000,
            "funding_amount_max": 32000,
            "source_url": "https://www.sgs.utoronto.ca/awards",
            "source_document_ref": "utoronto-isa-2026",
            "field_tags": ["all"],
            "degree_levels": ["MS", "PHD"],
            "citizenship_rules": ["PK"],
            "min_gpa_value": 3.3,
            "deadline_at": _utc(2026, 3, 31),
            "tags": ["partial", "canada", "need_based"],
            "requires_gre": False,
            "requires_ielts": True,
        },
        {
            "source_key": "melbourne-grs",
            "external_source_id": "melbourne-grs-pk",
            "title": "University of Melbourne Graduate Research Scholarship",
            "provider_name": "University of Melbourne",
            "country_code": "AU",
            "summary": "Full tuition + stipend for PhD and research masters students.",
            "funding_summary": "Full: tuition + AUD 28,000/year stipend.",
            "funding_type": "full",
            "funding_amount_min": 18000,
            "funding_amount_max": 30000,
            "source_url": "https://scholarships.unimelb.edu.au/awards/graduate-research-scholarships",
            "source_document_ref": "melbourne-grs-2026",
            "field_tags": ["all", "research"],
            "degree_levels": ["PHD", "MS"],
            "citizenship_rules": ["PK"],
            "min_gpa_value": 3.5,
            "deadline_at": _utc(2026, 10, 31),
            "tags": ["fully_funded", "australia", "research", "phd_focused"],
            "requires_gre": False,
            "requires_ielts": True,
        },
        {
            "source_key": "tudelft-excellence",
            "external_source_id": "tudelft-excellence-pk",
            "title": "TU Delft Excellence Scholarship",
            "provider_name": "Delft University of Technology",
            "country_code": "NL",
            "summary": "Excellence scholarship for international master's students.",
            "funding_summary": "Full: tuition waiver + €12,000/year.",
            "funding_type": "full",
            "funding_amount_min": 18000,
            "funding_amount_max": 25000,
            "source_url": "https://www.tudelft.nl/en/education/practical-matters/scholarships/justus-and-louise-van-effen",
            "source_document_ref": "tudelft-excellence-2026",
            "field_tags": ["engineering", "technology"],
            "degree_levels": ["MS"],
            "citizenship_rules": ["PK"],
            "min_gpa_value": 3.5,
            "deadline_at": _utc(2026, 12, 1),
            "tags": ["fully_funded", "netherlands", "stem"],
            "requires_gre": False,
            "requires_ielts": True,
        },
        {
            "source_key": "ubc-isa",
            "external_source_id": "ubc-isa-pk",
            "title": "UBC International Student Award",
            "provider_name": "University of British Columbia",
            "country_code": "CA",
            "summary": "Need-based award for international students.",
            "funding_summary": "Partial: CAD 5,000–10,000.",
            "funding_type": "partial",
            "funding_amount_min": 4000,
            "funding_amount_max": 8000,
            "source_url": "https://students.ubc.ca/enrolment/finances/awards-scholarships-bursaries/international-student-award",
            "source_document_ref": "ubc-isa-2026",
            "field_tags": ["all"],
            "degree_levels": ["MS"],
            "citizenship_rules": ["PK"],
            "min_gpa_value": 3.0,
            "deadline_at": _utc(2026, 6, 30),
            "tags": ["partial", "canada", "need_based"],
            "requires_gre": False,
            "requires_ielts": True,
        },
    ]


def _gta_gra_positions() -> list[dict]:
    base_url = "https://www.scholarai.pk/gta-gra"
    universities = [
        ("ut-arlington", "University of Texas Arlington", "US"),
        ("asu", "Arizona State University", "US"),
        ("u-minnesota", "University of Minnesota", "US"),
        ("ucf", "University of Central Florida", "US"),
        ("wayne-state", "Wayne State University", "US"),
        ("u-windsor", "University of Windsor", "CA"),
        ("uwaterloo-gta", "University of Waterloo", "CA"),
        ("york-u", "York University", "CA"),
        ("concordia", "Concordia University", "CA"),
        ("u-manitoba", "University of Manitoba", "CA"),
    ]
    entries: list[dict] = []
    for slug, name, country in universities:
        entries.append(
            {
                "source_key": "pk-gta-gra",
                "external_source_id": f"gta-gra-{slug}",
                "title": f"GTA / GRA Positions — {name}",
                "provider_name": name,
                "country_code": country,
                "summary": (
                    f"Graduate teaching and research assistantship positions at {name}. "
                    "Pakistani graduate students are regularly funded through GTA/GRA "
                    "appointments which cover tuition plus a monthly stipend."
                ),
                "funding_summary": "Full: tuition waiver + monthly stipend via GTA/GRA.",
                "funding_type": "gta_gra",
                "funding_amount_min": 18000,
                "funding_amount_max": 30000,
                "source_url": f"{base_url}/{slug}",
                "source_document_ref": f"gta-gra-{slug}-2026",
                "field_tags": ["cs", "engineering", "ds_ai"],
                "degree_levels": ["MS", "PHD"],
                "citizenship_rules": ["PK"],
                "min_gpa_value": 3.2,
                "deadline_at": _utc(2026, 4, 30),
                "tags": ["fully_funded", country.lower(), "teaching_assistantship", "research_assistantship"],
                "requires_gre": country == "US",
                "requires_ielts": True,
            }
        )
    return entries


def _enrich(entry: dict) -> dict:
    """Fill standard provenance / state fields shared by every Pakistan seed row."""
    enriched = dict(entry)
    enriched.setdefault("record_state", RecordState.PUBLISHED)
    enriched.setdefault("imported_at", _utc(2026, 5, 11))
    enriched.setdefault("source_last_seen_at", _utc(2026, 5, 11))
    enriched.setdefault("review_notes", "Seeded by Pakistan pivot dataset (PRD §3).")
    enriched.setdefault("validated_at", _utc(2026, 5, 11))
    enriched.setdefault("published_at", _utc(2026, 5, 11))
    enriched.setdefault(
        "provenance_payload",
        {
            "dataset_version": "pakistan-pivot-2026-05",
            "source_kind": "manual_seed",
            "demo_visibility": "user_facing",
            "tags": list(entry.get("tags", [])),
        },
    )
    enriched.setdefault("requirements", [])
    return enriched


PAKISTAN_SCHOLARSHIP_SEED: list[dict] = [
    _enrich(row)
    for row in (
        _tier_one_scholarships()
        + _tier_two_scholarships()
        + _gta_gra_positions()
    )
]


PAKISTAN_SEED_VERSION = "pakistan-pivot-2026-05"
