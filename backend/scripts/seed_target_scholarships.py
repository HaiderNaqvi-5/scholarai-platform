"""Seed verified target scholarships (PK -> UK / US / CA / DE / AU) as PUBLISHED.

Curated companion to seed_pakistan_scholarships.py. Real awards, real
providers, official source URLs. Volatile fields (exact deadline / amount)
are intentionally left null + qualitative — deadlines change yearly and must
be verified on the official site (project rule: validated data is the
authority for deadlines/funding). Provenance marks each row "verify on
official site".

Idempotent: upserts on source_url, keeps record_state=PUBLISHED. Also
promotes any kept genuine RAW rows (UofT AI Entrance Bursary / Data Sciences
Doctoral Fellowship) to PUBLISHED.

Run in-container (host shell can't resolve the DB host):
    docker compose exec -T backend sh -c 'cat > /app/scripts/seed_target_scholarships.py' < backend/scripts/seed_target_scholarships.py
    docker compose exec -T backend python scripts/seed_target_scholarships.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select, update  # noqa: E402

from app.core.database import async_session_factory  # noqa: E402
from app.models import RecordState, Scholarship, SourceRegistry  # noqa: E402

SEED_DATE = datetime(2026, 6, 5, tzinfo=timezone.utc)
REVIEW_NOTE = "Curated target-scholarship seed. Verify deadline & funding on the official site."


def S(src, key, title, provider, cc, url, degrees, ftype, funding_summary, summary, tags):
    """Build one scholarship payload. Volatile fields left null on purpose."""
    return {
        "src": src,
        "source_key": key,
        "external_source_id": key,
        "title": title,
        "provider_name": provider,
        "country_code": cc,
        "source_url": url,
        "source_document_ref": url,
        "degree_levels": list(degrees),
        "funding_type": ftype,
        "funding_summary": funding_summary,
        "summary": summary,
        "field_tags": list(tags),
        "citizenship_rules": ["PK"],
        "min_gpa_value": None,
        "funding_amount_min": None,
        "funding_amount_max": None,
        "deadline_at": None,
    }


ALL = ["all_fields"]
_FULL = "full"
_PART = "partial"

SCHOLARSHIPS = [
    # ---------------- United Kingdom ----------------
    S("chevening", "tg-chevening", "Chevening Scholarship", "UK FCDO", "GB", "https://www.chevening.org/scholarship/", ["masters"], _FULL, "Fully funded: tuition, living stipend, return airfare.", "UK government global scholarship for one-year master's; open to Pakistani nationals.", ALL),
    S("csc-uk", "tg-cwealth-masters", "Commonwealth Master's Scholarship", "Commonwealth Scholarship Commission", "GB", "https://cscuk.fcdo.gov.uk/scholarships/commonwealth-masters-scholarships/", ["masters"], _FULL, "Fully funded: tuition, stipend, airfare.", "For students from low/middle-income Commonwealth countries incl. Pakistan.", ALL),
    S("csc-uk", "tg-cwealth-phd", "Commonwealth PhD Scholarship", "Commonwealth Scholarship Commission", "GB", "https://cscuk.fcdo.gov.uk/scholarships/commonwealth-phd-scholarships/", ["phd"], _FULL, "Fully funded doctoral study in the UK.", "Doctoral scholarship for Commonwealth-country nationals incl. Pakistan.", ALL),
    S("csc-uk", "tg-cwealth-shared", "Commonwealth Shared Scholarship", "Commonwealth Scholarship Commission", "GB", "https://cscuk.fcdo.gov.uk/scholarships/commonwealth-shared-scholarships/", ["masters"], _FULL, "Fully funded master's, jointly with UK universities.", "For students who could not otherwise afford UK study.", ALL),
    S("british-council", "tg-great", "GREAT Scholarships", "British Council", "GB", "https://study-uk.britishcouncil.org/scholarships/great-scholarships", ["masters"], _PART, "GBP 10,000 toward tuition.", "British Council + UK universities; Pakistan is an eligible country.", ALL),
    S("cambridge", "tg-gates-cambridge", "Gates Cambridge Scholarship", "University of Cambridge", "GB", "https://www.gatescambridge.org/", ["masters", "phd"], _FULL, "Full cost of study + maintenance.", "Highly competitive postgraduate award at Cambridge for non-UK students.", ALL),
    S("oxford", "tg-clarendon", "Clarendon Scholarship", "University of Oxford", "GB", "https://www.ox.ac.uk/clarendon", ["masters", "phd"], _FULL, "Full tuition + generous grant for living costs.", "Oxford's flagship graduate scholarship, all nationalities.", ALL),
    S("oxford", "tg-weidenfeld", "Weidenfeld-Hoffmann Scholarship", "University of Oxford", "GB", "https://www.oxfordweidenfeld.org/", ["masters"], _FULL, "Full tuition + living costs + leadership programme.", "For graduates from developing/transition economies incl. Pakistan.", ALL),
    S("soas", "tg-felix", "Felix Scholarship", "SOAS / University of Reading", "GB", "https://www.soas.ac.uk/admissions/scholarships/felix-scholarships", ["masters", "phd"], _FULL, "Full tuition, maintenance grant, airfare.", "For citizens of developing countries incl. Pakistan; need + merit.", ALL),
    S("edinburgh", "tg-edin-global", "Edinburgh Global Research Scholarship", "University of Edinburgh", "GB", "https://www.ed.ac.uk/student-funding/postgraduate/international", ["phd"], _PART, "Covers difference between home and international tuition.", "Doctoral tuition support for international students.", ALL),
    S("manchester", "tg-manchester", "Manchester Global Futures Scholarship", "University of Manchester", "GB", "https://www.manchester.ac.uk/study/masters/funding/", ["masters"], _PART, "Partial tuition reduction.", "International master's scholarship.", ALL),
    S("warwick", "tg-warwick-chancellor", "Warwick Chancellor's International Scholarship", "University of Warwick", "GB", "https://warwick.ac.uk/services/dc/schols_fund/scholarships_and_funding/chancellors_int/", ["phd"], _FULL, "Full tuition + stipend.", "Doctoral scholarship for outstanding international applicants.", ALL),
    S("nottingham", "tg-nottingham-ds", "Developing Solutions Master's Scholarship", "University of Nottingham", "GB", "https://www.nottingham.ac.uk/studywithus/international-applicants/scholarships-fees-and-finance/scholarships/developing-solutions-masters-scholarship.aspx", ["masters"], _PART, "50% or full tuition.", "For students from Africa, India and other developing Commonwealth nations.", ALL),
    S("westminster", "tg-westminster-full", "Westminster Full International Scholarship", "University of Westminster", "GB", "https://www.westminster.ac.uk/study/fees-and-funding/scholarships", ["masters"], _FULL, "Full tuition + accommodation + living costs.", "For international students from developing countries.", ALL),
    S("sheffield", "tg-sheffield-pg", "Sheffield Postgraduate Scholarship", "University of Sheffield", "GB", "https://www.sheffield.ac.uk/postgraduate/fees/scholarships", ["masters"], _PART, "GBP 5,000+ tuition discount.", "Merit scholarship for international master's students.", ALL),
    S("leeds", "tg-leeds-excellence", "Leeds International Excellence Scholarship", "University of Leeds", "GB", "https://www.leeds.ac.uk/scholarships", ["masters"], _PART, "Partial tuition award.", "Merit-based scholarship for international students.", ALL),
    S("ucl", "tg-ucl-global", "UCL Global Masters Scholarship", "University College London", "GB", "https://www.ucl.ac.uk/scholarships/", ["masters"], _PART, "GBP 15,000 living costs.", "Need-based scholarship for low-income international students.", ALL),
    S("imperial", "tg-imperial-phd", "Imperial College President's PhD Scholarship", "Imperial College London", "GB", "https://www.imperial.ac.uk/study/fees-and-funding/", ["phd"], _FULL, "Full tuition + stipend for 3.5 years.", "Doctoral scholarship for top applicants in science/engineering.", ALL),
    S("bristol", "tg-bristol-io", "Bristol University International Scholarship", "University of Bristol", "GB", "https://www.bristol.ac.uk/students/support/finances/scholarships/", ["masters"], _PART, "Partial tuition award.", "International postgraduate merit scholarship.", ALL),
    S("glasgow", "tg-glasgow-leadership", "Glasgow International Leadership Scholarship", "University of Glasgow", "GB", "https://www.gla.ac.uk/scholarships/", ["masters"], _PART, "GBP 10,000 tuition.", "Merit award for international master's students.", ALL),
    S("cardiff", "tg-cardiff-vc", "Cardiff University Vice-Chancellor's International Scholarship", "Cardiff University", "GB", "https://www.cardiff.ac.uk/study/international/scholarships", ["masters"], _PART, "GBP 3,000-5,000 tuition.", "International student merit scholarship.", ALL),
    S("birmingham", "tg-birmingham", "Birmingham International Scholarship", "University of Birmingham", "GB", "https://www.birmingham.ac.uk/postgraduate/funding", ["masters"], _PART, "Partial tuition support.", "Postgraduate international scholarship.", ALL),
    S("kcl", "tg-kcl-intl", "King's College London International Scholarship", "King's College London", "GB", "https://www.kcl.ac.uk/study/postgraduate-taught/fees-and-funding", ["masters"], _PART, "Partial tuition.", "Merit scholarship for international postgraduates.", ALL),
    S("durham", "tg-durham-global", "Durham University Global Scholarship", "Durham University", "GB", "https://www.durham.ac.uk/study/scholarships/", ["masters"], _PART, "Partial tuition.", "International master's scholarship.", ALL),
    S("qmul", "tg-qmul-principal", "Queen Mary Principal's Postgraduate Research Studentship", "Queen Mary University of London", "GB", "https://www.qmul.ac.uk/scholarships/", ["phd"], _FULL, "Full tuition + stipend.", "Doctoral studentship for international applicants.", ALL),
    S("southampton", "tg-soton-presidential", "Southampton Presidential International Scholarship", "University of Southampton", "GB", "https://www.southampton.ac.uk/study/fees-funding", ["phd"], _FULL, "Full tuition + stipend.", "Doctoral scholarship for outstanding international students.", ALL),

    # ---------------- United States ----------------
    S("usefp", "tg-fulbright-fsp", "Fulbright Foreign Student Program", "USEFP / IIE", "US", "https://www.usefpakistan.org/", ["masters", "phd"], _FULL, "Fully funded: tuition, stipend, airfare, health.", "US Department of State flagship; administered for Pakistan by USEFP.", ALL),
    S("us-state", "tg-humphrey", "Hubert H. Humphrey Fellowship", "US Department of State", "US", "https://www.humphreyfellowship.org/", ["masters"], _FULL, "Fully funded non-degree academic year.", "Mid-career professional development fellowship.", ALL),
    S("aauw", "tg-aauw-intl", "AAUW International Fellowship", "American Association of University Women", "US", "https://www.aauw.org/resources/programs/fellowships-grants/", ["masters", "phd"], _PART, "USD 20,000-30,000 stipend.", "For women pursuing graduate study in the US.", ALL),
    S("stanford", "tg-knight-hennessy", "Knight-Hennessy Scholars", "Stanford University", "US", "https://knight-hennessy.stanford.edu/", ["masters", "phd"], _FULL, "Full funding for any Stanford graduate degree.", "Highly selective multidisciplinary graduate fellowship.", ALL),
    S("worldbank", "tg-jj-wbgsp", "Joint Japan/World Bank Graduate Scholarship", "World Bank", "US", "https://www.worldbank.org/en/programs/scholarships", ["masters"], _FULL, "Tuition, stipend, travel, insurance.", "For development-related master's; from World Bank member countries.", ALL),
    S("eastwest", "tg-ewc-gdf", "East-West Center Graduate Degree Fellowship", "East-West Center", "US", "https://www.eastwestcenter.org/education/student-programs", ["masters", "phd"], _FULL, "Tuition + stipend at University of Hawai'i.", "For Asia-Pacific graduate students incl. Pakistan.", ALL),
    S("rotary", "tg-rotary-peace", "Rotary Peace Fellowship", "Rotary Foundation", "US", "https://www.rotary.org/en/our-programs/peace-fellowships", ["masters"], _FULL, "Tuition, room, board, travel.", "Master's in peace and conflict studies.", ALL),
    S("mit", "tg-mit-fellowships", "MIT Graduate Fellowships", "Massachusetts Institute of Technology", "US", "https://oge.mit.edu/finances/fellowships/", ["masters", "phd"], _FULL, "Department/institute funding for admitted PhD students.", "Funded graduate study in science, engineering and management.", ALL),
    S("harvard", "tg-harvard-gsas", "Harvard GSAS Fellowships", "Harvard University", "US", "https://gsas.harvard.edu/financial-support", ["phd"], _FULL, "Full tuition, stipend, health for PhD students.", "Doctoral funding at Harvard Graduate School of Arts & Sciences.", ALL),
    S("columbia", "tg-columbia-fellowship", "Columbia University Graduate Fellowships", "Columbia University", "US", "https://www.gsas.columbia.edu/student-guide/financing-your-education", ["phd"], _FULL, "Multi-year tuition + stipend.", "Doctoral funding package for admitted PhD students.", ALL),
    S("berkeley", "tg-berkeley-intl", "UC Berkeley International Doctoral Funding", "University of California, Berkeley", "US", "https://grad.berkeley.edu/financial/", ["phd"], _FULL, "Tuition + stipend for doctoral study.", "Funded PhD admission support for international students.", ALL),
    S("nyu", "tg-nyu-wagner", "NYU Wagner International Scholarship", "New York University", "US", "https://wagner.nyu.edu/admissions/financial-aid", ["masters"], _PART, "Partial tuition scholarship.", "Public policy master's scholarship.", ALL),
    S("cornell", "tg-cornell-fellowship", "Cornell University Graduate Fellowships", "Cornell University", "US", "https://gradschool.cornell.edu/financial-support/", ["phd"], _FULL, "Tuition + stipend for PhD students.", "Doctoral funding at Cornell.", ALL),
    S("princeton", "tg-princeton-fellowship", "Princeton Graduate Fellowship", "Princeton University", "US", "https://gradschool.princeton.edu/costs-funding", ["phd"], _FULL, "Full tuition + stipend.", "Guaranteed funding for admitted PhD students.", ALL),
    S("umich", "tg-umich-rackham", "Michigan Rackham Graduate Funding", "University of Michigan", "US", "https://rackham.umich.edu/funding/", ["phd"], _FULL, "Tuition + stipend for doctoral study.", "Funded PhD study at the University of Michigan.", ALL),
    S("uchicago", "tg-uchicago-fellowship", "University of Chicago Graduate Fellowships", "University of Chicago", "US", "https://grad.uchicago.edu/funding/", ["phd"], _FULL, "Multi-year tuition + stipend.", "Doctoral funding package.", ALL),
    S("cmu", "tg-cmu-fellowship", "Carnegie Mellon Graduate Fellowships", "Carnegie Mellon University", "US", "https://www.cmu.edu/graduate/funding/", ["phd"], _FULL, "Tuition + stipend for PhD students.", "Funded doctoral study in tech and engineering.", ALL),
    S("usc", "tg-usc-annenberg", "USC Annenberg International Scholarship", "University of Southern California", "US", "https://annenberg.usc.edu/admissions/financial-aid", ["masters"], _PART, "Partial tuition.", "Communication/journalism master's scholarship.", ALL),
    S("bu", "tg-bu-presidential", "Boston University Presidential Scholarship", "Boston University", "US", "https://www.bu.edu/admissions/tuition-aid/scholarships-financial-aid/", ["masters"], _PART, "Partial tuition.", "Merit scholarship for graduate students.", ALL),
    S("clark", "tg-clark-global", "Clark University Global Scholars Program", "Clark University", "US", "https://www.clarku.edu/admissions/", ["masters"], _PART, "USD 5,000+ and paid internship.", "Merit award for international students.", ALL),

    # ---------------- Canada ----------------
    S("canada-gov", "tg-vanier", "Vanier Canada Graduate Scholarship", "Government of Canada", "CA", "https://vanier.gc.ca/", ["phd"], _FULL, "CAD 50,000/year for three years.", "Doctoral scholarship for world-class students studying in Canada.", ALL),
    S("trudeau", "tg-trudeau", "Trudeau Foundation Doctoral Scholarship", "Pierre Elliott Trudeau Foundation", "CA", "https://www.trudeaufoundation.ca/", ["phd"], _FULL, "Up to CAD 60,000/year + travel.", "Doctoral scholarship in humanities and social sciences.", ALL),
    S("ontario", "tg-ots", "Ontario Trillium Scholarship", "Government of Ontario", "CA", "https://www.ontario.ca/page/graduate-scholarships", ["phd"], _FULL, "CAD 40,000/year for four years.", "Doctoral scholarship for international students in Ontario.", ALL),
    S("uoft", "tg-uoft-pearson", "Lester B. Pearson International Scholarship", "University of Toronto", "CA", "https://future.utoronto.ca/pearson/", ["bachelors"], _FULL, "Full tuition, books, fees, residence.", "Prestigious undergraduate award for international students.", ALL),
    S("ubc", "tg-ubc-ilot", "UBC International Leader of Tomorrow Award", "University of British Columbia", "CA", "https://you.ubc.ca/financial-planning/scholarships-awards-international-students/", ["bachelors"], _FULL, "Covers tuition and living, need-based.", "Undergraduate award for international leaders.", ALL),
    S("waterloo", "tg-waterloo-intl", "Waterloo International Master's/Doctoral Award", "University of Waterloo", "CA", "https://uwaterloo.ca/graduate-studies-postdoctoral-affairs/awards", ["masters", "phd"], _PART, "CAD 2,500-7,500/term.", "Graduate funding for international students.", ALL),
    S("mcgill", "tg-mcgill-grad", "McGill Graduate Excellence Award", "McGill University", "CA", "https://www.mcgill.ca/gps/funding", ["masters", "phd"], _PART, "Partial tuition/stipend support.", "Graduate merit funding at McGill.", ALL),
    S("alberta", "tg-alberta-grad", "University of Alberta Graduate Recruitment Scholarship", "University of Alberta", "CA", "https://www.ualberta.ca/graduate-studies/awards-and-funding/", ["masters", "phd"], _PART, "CAD 5,000+ recruitment award.", "Graduate funding for incoming students.", ALL),
    S("york", "tg-york-intl", "York University International Student Scholarship", "York University", "CA", "https://www.yorku.ca/scholarships/", ["masters"], _PART, "Partial tuition.", "International graduate merit scholarship.", ALL),
    S("concordia", "tg-concordia-tuition", "Concordia International Tuition Award of Excellence", "Concordia University", "CA", "https://www.concordia.ca/students/financial-support.html", ["masters", "phd"], _PART, "Covers part of international tuition.", "Award reducing international tuition to domestic rate.", ALL),
    S("uottawa", "tg-uottawa-intl", "University of Ottawa International Scholarship", "University of Ottawa", "CA", "https://www.uottawa.ca/study/graduate-studies/scholarships", ["masters", "phd"], _PART, "Tuition differential exemption.", "Graduate scholarship for international students.", ALL),
    S("calgary", "tg-calgary-eyeshigh", "Calgary Eyes High International Scholarship", "University of Calgary", "CA", "https://grad.ucalgary.ca/awards", ["masters", "phd"], _PART, "CAD 5,000+ entrance award.", "Graduate recruitment scholarship.", ALL),
    S("manitoba", "tg-manitoba-gf", "University of Manitoba Graduate Fellowship", "University of Manitoba", "CA", "https://umanitoba.ca/graduate-studies/funding-awards-financial-aid", ["masters", "phd"], _PART, "CAD 14,000-18,000 stipend.", "Graduate fellowship open to international students.", ALL),
    S("sfu", "tg-sfu-grad", "SFU Graduate Fellowship", "Simon Fraser University", "CA", "https://www.sfu.ca/dean-gradstudies/financial/", ["masters", "phd"], _PART, "CAD 6,250/term.", "Merit-based graduate fellowship.", ALL),
    S("mcmaster", "tg-mcmaster-excellence", "McMaster International Excellence Award", "McMaster University", "CA", "https://gs.mcmaster.ca/financial-support/", ["masters", "phd"], _PART, "Partial tuition/stipend.", "Graduate merit award for international students.", ALL),
    S("queens-ca", "tg-queens-grad", "Queen's University Graduate Award", "Queen's University", "CA", "https://www.queensu.ca/sgspa/awards-funding", ["masters", "phd"], _PART, "Tuition/stipend support.", "Graduate funding at Queen's.", ALL),
    S("western", "tg-western-grad", "Western University Graduate Research Scholarship", "Western University", "CA", "https://grad.uwo.ca/finances/", ["masters", "phd"], _PART, "Partial funding package.", "Graduate research funding.", ALL),

    # ---------------- Germany ----------------
    S("daad", "tg-daad-epos", "DAAD EPOS Development-Related Postgraduate Scholarship", "DAAD", "DE", "https://www.daad.de/en/study-and-research-in-germany/scholarships/", ["masters"], _FULL, "Monthly stipend, travel, insurance, tuition.", "Development-related master's for professionals from developing countries.", ALL),
    S("daad", "tg-daad-helmut", "DAAD Helmut-Schmidt Programme (Public Policy)", "DAAD", "DE", "https://www.daad.de/en/", ["masters"], _FULL, "Full stipend + tuition + travel.", "Master's in public policy / good governance.", ALL),
    S("daad", "tg-daad-research", "DAAD Research Grants - Doctoral", "DAAD", "DE", "https://www.daad.de/en/", ["phd"], _FULL, "Monthly doctoral stipend + allowances.", "Doctoral research funding in Germany.", ALL),
    S("erasmus", "tg-erasmus-mundus", "Erasmus Mundus Joint Master's Scholarship", "European Commission", "DE", "https://www.eacea.ec.europa.eu/scholarships/emjmd-catalogue_en", ["masters"], _FULL, "Tuition, travel, monthly allowance.", "Joint master's across European universities; Pakistan eligible.", ALL),
    S("boell", "tg-boell", "Heinrich Boll Foundation Scholarship", "Heinrich Boll Stiftung", "DE", "https://www.boell.de/en/foundation/scholarships", ["masters", "phd"], _FULL, "Monthly stipend + allowances.", "For students of all nationalities studying in Germany.", ALL),
    S("kas", "tg-kas", "Konrad-Adenauer-Stiftung Scholarship", "Konrad-Adenauer-Stiftung", "DE", "https://www.kas.de/en/scholarships", ["masters", "phd"], _FULL, "Monthly stipend + support.", "Scholarship for international graduate students in Germany.", ALL),
    S("fes", "tg-fes", "Friedrich Ebert Stiftung Scholarship", "Friedrich-Ebert-Stiftung", "DE", "https://www.fes.de/en/studienfoerderung", ["masters", "phd"], _FULL, "Monthly stipend.", "Funding for international students committed to social justice.", ALL),
    S("kaad", "tg-kaad", "KAAD Scholarship", "Katholischer Akademischer Auslander-Dienst", "DE", "https://www.kaad.de/en/", ["masters", "phd"], _FULL, "Monthly stipend + tuition support.", "For graduate students from developing countries.", ALL),
    S("deutschland", "tg-deutschlandstip", "Deutschlandstipendium", "German Federal Ministry / Universities", "DE", "https://www.deutschlandstipendium.de/", ["bachelors", "masters"], _PART, "EUR 300/month.", "Merit scholarship at participating German universities.", ALL),
    S("bayer", "tg-bayer", "Bayer Foundation Fellowship", "Bayer Foundation", "DE", "https://www.bayer-foundation.com/bayer-fellowship-program", ["masters"], _PART, "Up to EUR 10,000 project funding.", "Fellowship for STEM and medical students.", ALL),
    S("tum", "tg-tum", "TUM International Scholarship Support", "Technical University of Munich", "DE", "https://www.tum.de/en/studies/fees-and-financial-aid/", ["masters"], _PART, "Partial support / no tuition for many programs.", "Funding guidance for international master's at TUM.", ALL),
    S("rwth", "tg-rwth", "RWTH Aachen International Scholarship", "RWTH Aachen University", "DE", "https://www.rwth-aachen.de/go/id/bvwbg", ["masters"], _PART, "Partial stipend support.", "International student funding at RWTH Aachen.", ALL),
    S("heidelberg", "tg-heidelberg", "Heidelberg University Scholarship", "Heidelberg University", "DE", "https://www.uni-heidelberg.de/en/study/financing-your-studies", ["masters", "phd"], _PART, "Partial funding/stipend.", "Graduate scholarship at Heidelberg.", ALL),

    # ---------------- Australia ----------------
    S("dfat", "tg-australia-awards", "Australia Awards Scholarship", "Australian Government (DFAT)", "AU", "https://www.dfat.gov.au/people-to-people/australia-awards/australia-awards-scholarships", ["masters"], _FULL, "Tuition, airfare, living allowance, health cover.", "Long-term development scholarship; Pakistan is a participating country.", ALL),
    S("melbourne", "tg-melb-research", "Melbourne Research Scholarship", "University of Melbourne", "AU", "https://scholarships.unimelb.edu.au/awards/graduate-research-scholarships", ["phd"], _FULL, "Full fee offset + living allowance.", "Doctoral research scholarship.", ALL),
    S("anu", "tg-anu-chancellor", "ANU Chancellor's International Scholarship", "Australian National University", "AU", "https://www.anu.edu.au/study/scholarships", ["bachelors", "masters"], _PART, "25-50% tuition reduction.", "Merit scholarship for international students.", ALL),
    S("sydney", "tg-sydney-research", "University of Sydney International Research Scholarship", "University of Sydney", "AU", "https://www.sydney.edu.au/scholarships/", ["phd"], _FULL, "Tuition + living allowance.", "Doctoral research funding.", ALL),
    S("unsw", "tg-unsw-intl", "UNSW International Scholarship", "UNSW Sydney", "AU", "https://www.unsw.edu.au/scholarships", ["masters", "phd"], _PART, "Partial to full depending on program.", "Merit and research scholarships for international students.", ALL),
    S("monash", "tg-monash-merit", "Monash International Merit Scholarship", "Monash University", "AU", "https://www.monash.edu/study/fees-scholarships/scholarships", ["masters"], _PART, "AUD 10,000/year.", "Merit scholarship for international students.", ALL),
    S("uq", "tg-uq-rtp", "UQ Research Training Scholarship", "University of Queensland", "AU", "https://scholarships.uq.edu.au/", ["phd"], _FULL, "Tuition + living stipend.", "Doctoral research scholarship.", ALL),
    S("adelaide", "tg-adelaide-asi", "Adelaide Scholarships International", "University of Adelaide", "AU", "https://international.adelaide.edu.au/scholarships", ["phd"], _FULL, "Tuition + stipend + health cover.", "Doctoral research scholarship for international students.", ALL),
    S("uwa", "tg-uwa-fee", "UWA International Fee Scholarship", "University of Western Australia", "AU", "https://www.uwa.edu.au/study/how-to-apply/scholarships-and-fees", ["masters"], _PART, "Partial tuition.", "International student tuition scholarship.", ALL),
    S("macquarie", "tg-macquarie-intl", "Macquarie University International Scholarship", "Macquarie University", "AU", "https://www.mq.edu.au/study/international-students/scholarships", ["masters"], _PART, "Partial tuition reduction.", "Merit scholarship for international students.", ALL),
    S("deakin", "tg-deakin-vc", "Deakin Vice-Chancellor's International Scholarship", "Deakin University", "AU", "https://www.deakin.edu.au/courses/scholarships", ["masters"], _PART, "Up to 100% tuition for top applicants.", "Merit international scholarship.", ALL),
    S("uts", "tg-uts-research", "UTS International Research Scholarship", "University of Technology Sydney", "AU", "https://www.uts.edu.au/research/graduate-research-school/scholarships", ["phd"], _FULL, "Tuition + stipend.", "Doctoral research scholarship.", ALL),
    S("rmit", "tg-rmit-intl", "RMIT International Scholarship", "RMIT University", "AU", "https://www.rmit.edu.au/study-with-us/international-students/scholarships-for-international-students", ["masters"], _PART, "10-30% tuition reduction.", "Merit scholarship for international students.", ALL),
    S("griffith", "tg-griffith-intl", "Griffith University International Student Scholarship", "Griffith University", "AU", "https://www.griffith.edu.au/scholarships", ["masters"], _PART, "25-50% tuition reduction.", "International merit scholarship.", ALL),
]


def _origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


async def _upsert_sources(session, rows):
    by_key = {}
    for r in rows:
        key = r["src"]
        if key in by_key:
            continue
        existing = (await session.execute(
            select(SourceRegistry).where(SourceRegistry.source_key == key)
        )).scalar_one_or_none()
        src = existing or SourceRegistry(source_key=key)
        if existing is None:
            session.add(src)
        src.display_name = r["provider_name"]
        src.base_url = _origin(r["source_url"])
        src.source_type = "official"
        src.is_active = True
        by_key[key] = src
    await session.flush()
    return by_key


async def _upsert(session, payload, sources):
    sc = (await session.execute(
        select(Scholarship).where(Scholarship.source_url == payload["source_url"])
    )).scalar_one_or_none()
    if sc is None:
        sc = Scholarship(
            title=payload["title"], provider_name=payload["provider_name"],
            country_code=payload["country_code"], source_url=payload["source_url"],
            field_tags=[], degree_levels=[], citizenship_rules=[],
        )
        session.add(sc)
    sc.source_registry = sources[payload["src"]]
    sc.external_source_id = payload["external_source_id"]
    sc.title = payload["title"]
    sc.provider_name = payload["provider_name"]
    sc.country_code = payload["country_code"]
    sc.summary = payload["summary"]
    sc.funding_summary = payload["funding_summary"]
    sc.funding_type = payload["funding_type"]
    sc.funding_amount_min = payload["funding_amount_min"]
    sc.funding_amount_max = payload["funding_amount_max"]
    sc.source_document_ref = payload["source_document_ref"]
    sc.field_tags = list(payload["field_tags"])
    sc.degree_levels = list(payload["degree_levels"])
    sc.citizenship_rules = list(payload["citizenship_rules"])
    sc.min_gpa_value = payload["min_gpa_value"]
    sc.deadline_at = payload["deadline_at"]
    sc.record_state = RecordState.PUBLISHED
    sc.imported_at = SEED_DATE
    sc.source_last_seen_at = SEED_DATE
    sc.validated_at = SEED_DATE
    sc.published_at = SEED_DATE
    sc.review_notes = REVIEW_NOTE
    sc.provenance_payload = {
        "dataset_version": "target-scholarships-2026-06",
        "source_kind": "manual_seed",
        "verify": "Confirm deadline and funding on the official source_url before applying.",
    }
    return sc


async def _seed():
    async with async_session_factory() as session:
        sources = await _upsert_sources(session, SCHOLARSHIPS)
        for payload in SCHOLARSHIPS:
            await _upsert(session, payload, sources)
        # Promote the kept genuine RAW rows to PUBLISHED.
        promote = (
            update(Scholarship)
            .where(Scholarship.record_state == RecordState.RAW)
            .where(
                Scholarship.title.ilike("%AI Entrance Bursary%")
                | Scholarship.title.ilike("%Doctoral Student Fellowship%")
            )
            .values(record_state=RecordState.PUBLISHED, validated_at=SEED_DATE, published_at=SEED_DATE)
        )
        promoted = (await session.execute(promote)).rowcount
        await session.commit()
        return len(sources), len(SCHOLARSHIPS), promoted


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    sources, scholarships, promoted = asyncio.run(_seed())
    print(f"target dataset ready: {sources} sources, {scholarships} scholarships seeded, "
          f"{promoted} kept-RAW promoted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
