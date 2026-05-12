"""Seed universities with Pakistan-relevant metadata (PRD §4).

Coverage: 10 UK + 8 US + 7 CA + 5 DE = 30 universities.
"""

from __future__ import annotations


UK_UNIVERSITIES = [
    ("University of Manchester", "Manchester", 6.5, 6.0, 3.0, True, 0.78, 75, False),
    ("University of Birmingham", "Birmingham", 6.5, 6.0, 3.0, True, 0.74, 75, False),
    ("University of Sheffield", "Sheffield", 6.5, 6.0, 3.0, True, 0.76, 75, False),
    ("University of Leeds", "Leeds", 6.5, 6.0, 3.0, True, 0.77, 75, False),
    ("King's College London", "London", 7.0, 6.5, 3.3, True, 0.72, 100, False),
    ("University of Nottingham", "Nottingham", 6.5, 6.0, 3.0, True, 0.73, 75, False),
    ("University of Edinburgh", "Edinburgh", 6.5, 6.0, 3.3, True, 0.75, 75, False),
    ("University of Glasgow", "Glasgow", 6.5, 6.0, 3.0, True, 0.78, 50, False),
    ("Brunel University London", "London", 6.5, 5.5, 3.0, True, 0.70, 50, True),
    ("Coventry University", "Coventry", 6.5, 5.5, 3.0, True, 0.81, 0, True),
]

US_UNIVERSITIES = [
    ("University of Texas Arlington", "Arlington", 6.5, 6.0, 3.0, False, 0.65, 80, True, True),
    ("Arizona State University", "Tempe", 6.5, 6.0, 3.0, False, 0.68, 70, True, True),
    ("University of Central Florida", "Orlando", 6.5, 6.0, 3.0, False, 0.66, 60, True, True),
    ("Wayne State University", "Detroit", 6.5, 6.0, 3.0, False, 0.62, 50, True, True),
    ("University of Illinois Chicago", "Chicago", 6.5, 6.0, 3.0, True, 0.68, 70, False, False),
    ("George Mason University", "Fairfax", 6.5, 6.0, 3.0, False, 0.70, 65, True, False),
    ("University of Houston", "Houston", 6.5, 6.0, 3.0, False, 0.67, 75, True, True),
    ("Missouri University of Science and Technology", "Rolla", 6.5, 6.0, 3.0, False, 0.65, 60, True, True),
]

CA_UNIVERSITIES = [
    ("University of Windsor", "Windsor", 6.5, 6.0, 3.0, False, 0.79, 100, True),
    ("York University", "Toronto", 6.5, 6.0, 3.0, False, 0.77, 110, False),
    ("Concordia University", "Montreal", 6.5, 6.0, 3.0, False, 0.78, 100, True),
    ("University of Manitoba", "Winnipeg", 6.5, 6.0, 3.0, False, 0.80, 100, False),
    ("University of Regina", "Regina", 6.5, 6.0, 3.0, False, 0.78, 100, True),
    ("Lakehead University", "Thunder Bay", 6.5, 6.0, 3.0, False, 0.79, 100, True),
    ("Toronto Metropolitan University", "Toronto", 6.5, 6.0, 3.0, False, 0.76, 130, False),
]

DE_UNIVERSITIES = [
    ("TU Munich", "Munich", 6.5, 6.0, 3.2, True, 0.85, 0, True),
    ("RWTH Aachen", "Aachen", 6.5, 6.0, 3.2, True, 0.83, 0, True),
    ("Karlsruhe Institute of Technology", "Karlsruhe", 6.5, 6.0, 3.0, True, 0.84, 0, True),
    ("University of Stuttgart", "Stuttgart", 6.5, 6.0, 3.0, True, 0.83, 0, True),
    ("TU Berlin", "Berlin", 6.5, 6.0, 3.0, True, 0.82, 0, True),
]


def _row(name, city, country, min_ielts, min_band, min_cgpa, requires_gre, visa_rate,
         fee_usd, fee_waiver, *, gta_gra=True, alumni=True, fields=None,
         intakes=("january", "september")) -> dict:
    return {
        "name": name,
        "city": city,
        "country": country,
        "website_url": None,
        "accepts_hec_degrees": True,
        "has_pakistani_alumni_network": alumni,
        "offers_gta_gra": gta_gra,
        "avg_visa_approval_rate_pk": visa_rate,
        "requires_gre": requires_gre,
        "accepts_ielts": True,
        "accepts_toefl": True,
        "min_ielts_overall": min_ielts,
        "min_ielts_each_band": min_band,
        "min_cgpa": min_cgpa,
        "application_fee_usd": fee_usd,
        "application_fee_waiver_available": fee_waiver,
        "intake_months": list(intakes),
        "fields_offered": list(fields or ("cs", "ds_ai", "engineering")),
        "notes": None,
    }


def all_university_seed() -> list[dict]:
    rows: list[dict] = []
    for name, city, ielts, band, cgpa, alumni, visa, fee, fee_waiver in UK_UNIVERSITIES:
        rows.append(_row(name, city, "GB", ielts, band, cgpa, False, visa, fee, fee_waiver,
                         gta_gra=False, alumni=alumni, intakes=("september",)))
    for name, city, ielts, band, cgpa, requires_gre, visa, fee, gta, fee_waiver in US_UNIVERSITIES:
        rows.append(_row(name, city, "US", ielts, band, cgpa, requires_gre, visa, fee, fee_waiver,
                         gta_gra=gta, alumni=True, intakes=("january", "august")))
    for name, city, ielts, band, cgpa, requires_gre, visa, fee, fee_waiver in CA_UNIVERSITIES:
        rows.append(_row(name, city, "CA", ielts, band, cgpa, requires_gre, visa, fee, fee_waiver,
                         gta_gra=True, alumni=True, intakes=("january", "september")))
    for name, city, ielts, band, cgpa, alumni, visa, fee, fee_waiver in DE_UNIVERSITIES:
        rows.append(_row(name, city, "DE", ielts, band, cgpa, False, visa, fee, fee_waiver,
                         gta_gra=False, alumni=alumni, intakes=("april", "october")))
    return rows


UNIVERSITIES_SEED = all_university_seed()
