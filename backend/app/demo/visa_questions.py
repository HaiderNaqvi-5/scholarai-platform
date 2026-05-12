"""Visa interview question bank (Feature 8, PRD §8).

70 questions total:
  - UK Student Visa: 20
  - US F-1: 20
  - Canada Study Permit: 15
  - Germany Student Visa: 15
"""

from __future__ import annotations


def _q(country: str, visa_type: str, category: str, text: str, *,
       difficulty: str = "medium",
       notes: str | None = None) -> dict:
    return {
        "country": country,
        "visa_type": visa_type,
        "category": category,
        "question_text": text,
        "ideal_answer_notes": notes,
        "difficulty": difficulty,
    }


def _uk_questions() -> list[dict]:
    return [
        _q("GB", "student_uk", "motivation", "Why do you want to study in the UK?", difficulty="easy"),
        _q("GB", "student_uk", "program", "Why did you choose this specific university?"),
        _q("GB", "student_uk", "program", "Why this course or program specifically?"),
        _q("GB", "student_uk", "finances", "How will you fund your studies?"),
        _q("GB", "student_uk", "finances", "Can you explain your bank statement / show of funds?", difficulty="hard"),
        _q("GB", "student_uk", "ties", "Do you have any relatives in the UK?"),
        _q("GB", "student_uk", "future_plans", "What do you plan to do after your studies?"),
        _q("GB", "student_uk", "ties", "Do you intend to return to Pakistan after graduation?"),
        _q("GB", "student_uk", "ties", "What ties do you have to Pakistan?", difficulty="hard"),
        _q("GB", "student_uk", "motivation", "Have you applied to other universities? Why the UK over them?"),
        _q("GB", "student_uk", "ties", "What is your current job in Pakistan?"),
        _q("GB", "student_uk", "motivation", "Why are you leaving a job to study?"),
        _q("GB", "student_uk", "finances", "Who is sponsoring your studies?"),
        _q("GB", "student_uk", "finances", "What is your sponsor's occupation and income?", difficulty="hard"),
        _q("GB", "student_uk", "program", "Do you have a confirmed accommodation in the UK?"),
        _q("GB", "student_uk", "program", "What is your English proficiency? (IELTS/TOEFL)", difficulty="easy"),
        _q("GB", "student_uk", "ties", "Have you ever been refused a visa to any country?", difficulty="hard"),
        _q("GB", "student_uk", "finances", "What do you know about living costs in the UK?"),
        _q("GB", "student_uk", "motivation", "Why did you not pursue a Master's in Pakistan?"),
        _q("GB", "student_uk", "future_plans", "What is your long-term career plan?"),
    ]


def _us_questions() -> list[dict]:
    return [
        _q("US", "f1_us", "motivation", "Why do you want to study in the United States?", difficulty="easy"),
        _q("US", "f1_us", "program", "Why did you choose this university specifically?"),
        _q("US", "f1_us", "program", "Did you apply to other universities? Why this one?"),
        _q("US", "f1_us", "program", "What is your program and how long is it?", difficulty="easy"),
        _q("US", "f1_us", "finances", "How will you finance your education?"),
        _q("US", "f1_us", "finances", "Who is paying for your studies?"),
        _q("US", "f1_us", "future_plans", "What are your plans after graduation?"),
        _q("US", "f1_us", "ties", "Do you plan to return to Pakistan?"),
        _q("US", "f1_us", "ties", "What ties do you have to Pakistan that will bring you back?", difficulty="hard"),
        _q("US", "f1_us", "ties", "Do you have relatives in the USA?"),
        _q("US", "f1_us", "ties", "Have you ever been to the USA before?"),
        _q("US", "f1_us", "ties", "Have you been denied a US visa before?", difficulty="hard"),
        _q("US", "f1_us", "finances", "What does your father / sponsor do for a living?"),
        _q("US", "f1_us", "program", "What is your undergraduate CGPA?", difficulty="easy"),
        _q("US", "f1_us", "program", "Do you have a GRE score?"),
        _q("US", "f1_us", "program", "Tell me about your academic background.", difficulty="easy"),
        _q("US", "f1_us", "future_plans", "What will you do with this degree in Pakistan?"),
        _q("US", "f1_us", "motivation", "Why didn't you pursue MS in Pakistan?"),
        _q("US", "f1_us", "program", "What is your IELTS / TOEFL score?", difficulty="easy"),
        _q("US", "f1_us", "finances", "Are you on an assistantship or scholarship?"),
    ]


def _ca_questions() -> list[dict]:
    return [
        _q("CA", "study_ca", "motivation", "Why Canada for your studies?", difficulty="easy"),
        _q("CA", "study_ca", "program", "Why this specific Canadian university?"),
        _q("CA", "study_ca", "finances", "How will you fund your studies and living expenses?"),
        _q("CA", "study_ca", "future_plans", "What are your plans after graduation?"),
        _q("CA", "study_ca", "ties", "Do you have family in Canada?"),
        _q("CA", "study_ca", "ties", "Have you ever been refused a Canadian visa?", difficulty="hard"),
        _q("CA", "study_ca", "program", "Describe your academic background.", difficulty="easy"),
        _q("CA", "study_ca", "ties", "What is your work experience in Pakistan?"),
        _q("CA", "study_ca", "finances", "Who is your financial sponsor?"),
        _q("CA", "study_ca", "finances", "Do you have proof of funds?"),
        _q("CA", "study_ca", "program", "Do you have an acceptance letter? Tell me about the program."),
        _q("CA", "study_ca", "motivation", "Why not study in Pakistan or another country?"),
        _q("CA", "study_ca", "future_plans", "What will you contribute to Canada during your studies?"),
        _q("CA", "study_ca", "ties", "What ties to Pakistan will ensure you return?", difficulty="hard"),
        _q("CA", "study_ca", "ties", "Do you have travel history to other countries?"),
    ]


def _de_questions() -> list[dict]:
    return [
        _q("DE", "student_de", "motivation", "Why Germany for your studies?", difficulty="easy"),
        _q("DE", "student_de", "program", "Do you speak German? Will you take German language classes?"),
        _q("DE", "student_de", "program", "Which university and program have you been accepted to?"),
        _q("DE", "student_de", "finances", "How will you fund your studies in Germany?"),
        _q("DE", "student_de", "finances", "Do you have a blocked account (Sperrkonto)?"),
        _q("DE", "student_de", "finances", "What is the blocked account amount and which bank?", difficulty="hard"),
        _q("DE", "student_de", "future_plans", "What are your career plans after your German degree?"),
        _q("DE", "student_de", "ties", "Will you return to Pakistan after graduation?"),
        _q("DE", "student_de", "program", "Do you have health insurance arranged?"),
        _q("DE", "student_de", "program", "Do you have accommodation arranged?"),
        _q("DE", "student_de", "program", "What do you know about the German university system?"),
        _q("DE", "student_de", "program", "Why this program specifically?"),
        _q("DE", "student_de", "ties", "Have you been to Germany or Europe before?"),
        _q("DE", "student_de", "finances", "Who is your financial sponsor in Pakistan?"),
        _q("DE", "student_de", "ties", "Have you ever been refused a Schengen visa?", difficulty="hard"),
    ]


VISA_INTERVIEW_QUESTION_BANK: list[dict] = (
    _uk_questions() + _us_questions() + _ca_questions() + _de_questions()
)


VISA_TYPE_BY_COUNTRY = {
    "GB": "student_uk",
    "US": "f1_us",
    "CA": "study_ca",
    "DE": "student_de",
}
