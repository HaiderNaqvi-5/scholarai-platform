from enum import Enum

class ScholarshipCategory(Enum):
    STEM = "stem"
    HUMANITIES = "humanities"
    RESEARCH = "research"
    LEADERSHIP = "leadership"
    GENERAL = "general"

PROMPT_BANK = {
    ScholarshipCategory.STEM: {
        "system_instruction": "You are a STEM scholarship panelist. Focus on technical rigor, problem-solving methodology, and the potential for scientific impact.",
        "themes": ["methodology", "scalability", "innovation", "quantitative impact"]
    },
    ScholarshipCategory.HUMANITIES: {
        "system_instruction": "You are a Humanities scholarship panelist. Focus on critical thinking, societal impact, and the depth of humanistic inquiry.",
        "themes": ["perspective", "societal change", "narrative", "originality"]
    },
    ScholarshipCategory.RESEARCH: {
        "system_instruction": "You are a Research panelist. Focus on the feasibility of the proposal, literature grounding, and contribution to the field.",
        "themes": ["methodology", "literature", "novelty", "ethics"]
    },
    ScholarshipCategory.LEADERSHIP: {
        "system_instruction": "You are a Leadership panelist. Focus on ownership, teamwork, vision, and demonstrated impact on communities.",
        "themes": ["vision", "resilience", "collaboration", "ownership"]
    },
    ScholarshipCategory.GENERAL: {
        "system_instruction": "You are a scholarship panelist. Focus on personal growth, academic fit, and future potential.",
        "themes": ["fit", "potential", "clarity", "motivation"]
    }
}

def get_prompts_for_category(category_name: str) -> dict:
    try:
        category = ScholarshipCategory(category_name.lower())
    except ValueError:
        category = ScholarshipCategory.GENERAL
    return PROMPT_BANK[category]
