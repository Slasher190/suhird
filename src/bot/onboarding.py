"""
Onboarding question engine for Suhird.

Defines 25+ questions organized by section. Each question specifies its text,
how to validate the answer, and where to store the result in the user profile.
"""
from dataclasses import dataclass, field
from typing import Any, Callable

from src.bot import messages as msg


@dataclass
class Question:
    key: str
    text: str
    section: str
    validate: Callable[[str], tuple[bool, Any]]
    error_hint: str = "Please try again."
    # Where to store in profile: (top-level-field, nested-key-or-None)
    store_field: str = ""
    store_key: str | None = None


# --- Validators ---

def _accept_any(val: str) -> tuple[bool, str]:
    v = val.strip()
    return (True, v) if v else (False, None)


def _validate_name(val: str) -> tuple[bool, str | None]:
    import re
    name = val.strip()
    if 1 <= len(name) <= 100 and re.match(r"^[a-zA-Z\s\.\-']+$", name):
        return True, name.title()
    return False, None


def _validate_age(val: str) -> tuple[bool, int | None]:
    try:
        age = int(val.strip())
        return (True, age) if 18 <= age <= 100 else (False, None)
    except ValueError:
        return False, None


def _validate_gender_choice(val: str) -> tuple[bool, str | None]:
    mapping = {"1": "male", "2": "female", "3": "non-binary", "4": "other",
               "male": "male", "female": "female", "non-binary": "non-binary", "other": "other"}
    v = val.strip().lower()
    return (True, mapping[v]) if v in mapping else (False, None)


def _validate_location(val: str) -> tuple[bool, str | None]:
    loc = val.strip()
    return (True, loc.title()) if 2 <= len(loc) <= 200 else (False, None)


def _validate_pref_gender(val: str) -> tuple[bool, str | None]:
    mapping = {"1": "men", "2": "women", "3": "everyone",
               "men": "men", "women": "women", "everyone": "everyone"}
    v = val.strip().lower()
    return (True, mapping[v]) if v in mapping else (False, None)


def _validate_age_range(val: str) -> tuple[bool, dict | None]:
    import re
    m = re.match(r"^(\d{2})\s*[-–]\s*(\d{2,3})$", val.strip())
    if m:
        low, high = int(m.group(1)), int(m.group(2))
        if 18 <= low < high <= 100:
            return True, {"min": low, "max": high}
    return False, None


def _validate_distance(val: str) -> tuple[bool, str | None]:
    v = val.strip().lower()
    valid = {"same city", "same state", "anywhere", "city", "state"}
    if v in valid:
        if v == "city":
            v = "same city"
        elif v == "state":
            v = "same state"
        return True, v
    return False, None


def _validate_relationship(val: str) -> tuple[bool, str | None]:
    mapping = {"1": "serious", "2": "casual", "3": "friends", "4": "not sure",
               "serious": "serious", "casual": "casual", "friends": "friends", "not sure": "not sure"}
    v = val.strip().lower()
    return (True, mapping[v]) if v in mapping else (False, None)


def _choice_3(val: str) -> tuple[bool, str | None]:
    """Generic 3-option validator. Returns the number as string."""
    v = val.strip()
    return (True, v) if v in {"1", "2", "3"} else (False, None)


def _choice_4(val: str) -> tuple[bool, str | None]:
    v = val.strip()
    return (True, v) if v in {"1", "2", "3", "4"} else (False, None)


def _choice_5(val: str) -> tuple[bool, str | None]:
    v = val.strip()
    return (True, v) if v in {"1", "2", "3", "4", "5"} else (False, None)


def _choice_6(val: str) -> tuple[bool, str | None]:
    v = val.strip()
    return (True, v) if v in {"1", "2", "3", "4", "5", "6"} else (False, None)


def _validate_interests(val: str) -> tuple[bool, list[str] | None]:
    numbers = [n.strip() for n in val.replace(" ", ",").split(",") if n.strip()]
    interests = []
    for n in numbers:
        if n in msg.INTERESTS_MAP:
            interests.append(msg.INTERESTS_MAP[n])
        elif n.lower() in msg.INTERESTS_MAP.values():
            interests.append(n.lower())
    return (True, interests) if interests else (False, None)


# Lifestyle option mappings for numbered choices
SMOKING_MAP = {"1": "never", "2": "sometimes", "3": "regularly"}
DRINKING_MAP = {"1": "never", "2": "socially", "3": "regularly"}
DIET_MAP = {"1": "vegetarian", "2": "vegan", "3": "non-vegetarian", "4": "eggetarian", "5": "jain", "6": "no preference"}
EXERCISE_MAP = {"1": "never", "2": "sometimes", "3": "regularly", "4": "daily"}
SLEEP_MAP = {"1": "early bird", "2": "night owl", "3": "flexible"}
SOCIAL_MAP = {"1": "introvert", "2": "extrovert", "3": "ambivert"}
LIVING_MAP = {"1": "alone", "2": "with family", "3": "with roommates", "4": "other"}
PETS_MAP = {"1": "none", "2": "dog", "3": "cat", "4": "both", "5": "other"}
CHILDREN_MAP = {"1": "yes", "2": "no", "3": "maybe", "4": "have children"}
RELIGIOUS_LEVEL_MAP = {"1": "not religious", "2": "somewhat religious", "3": "very religious"}
POLITICS_MAP = {"1": "liberal", "2": "moderate", "3": "conservative", "4": "not political", "5": "other"}
AMBITION_MAP = {"1": "relaxed", "2": "balanced", "3": "ambitious", "4": "very ambitious"}
FINANCE_MAP = {"1": "saver", "2": "spender", "3": "balanced"}


def _make_mapped_validator(mapping: dict):
    def validator(val: str) -> tuple[bool, str | None]:
        v = val.strip().lower()
        if v in mapping:
            return True, mapping[v]
        if v in mapping.values():
            return True, v
        return False, None
    return validator


# --- Question definitions ---

QUESTIONS: list[Question] = [
    # === BASIC INFO (4 questions) ===
    Question("name", msg.Q_NAME, "basic", _validate_name, "Please enter a valid name (letters only).", "name"),
    Question("age", msg.Q_AGE, "basic", _validate_age, "Please enter a number between 18 and 100.", "age"),
    Question("gender", msg.Q_GENDER, "basic", _validate_gender_choice, "Please pick 1, 2, 3, or 4.", "gender"),
    Question("location", msg.Q_LOCATION, "basic", _validate_location, "Please enter your city (2-200 chars).", "location"),

    # === BIO PROMPTS (8 questions) ===
    Question("simple_pleasures", msg.Q_BIO_SIMPLE_PLEASURES, "bio", _accept_any, "Tell us something!", "bio_prompts", "simple_pleasures"),
    Question("how_i_relax", msg.Q_BIO_HOW_I_RELAX, "bio", _accept_any, "Just tell us how!", "bio_prompts", "how_i_relax"),
    Question("what_if", msg.Q_BIO_WHAT_IF, "bio", _accept_any, "Finish the sentence!", "bio_prompts", "what_if"),
    Question("travel_story", msg.Q_BIO_TRAVEL_STORY, "bio", _accept_any, "Share a story!", "bio_prompts", "travel_story"),
    Question("two_truths", msg.Q_BIO_TWO_TRUTHS, "bio", _accept_any, "Give us three statements!", "bio_prompts", "two_truths"),
    Question("strength", msg.Q_BIO_STRENGTH, "bio", _accept_any, "What makes you strong?", "bio_prompts", "strength"),
    Question("green_flags", msg.Q_BIO_GREEN_FLAGS, "bio", _accept_any, "What do you love to see?", "bio_prompts", "green_flags"),
    Question("dating_me", msg.Q_BIO_DATING_ME, "bio", _accept_any, "Finish the sentence!", "bio_prompts", "dating_me"),

    # === PREFERENCES (4 questions) ===
    Question("pref_gender", msg.Q_PREF_GENDER, "prefs", _validate_pref_gender, "Pick 1, 2, or 3.", "preferences", "looking_for_gender"),
    Question("pref_age", msg.Q_PREF_AGE_RANGE, "prefs", _validate_age_range, "Use format like 25-35.", "preferences", "age_range"),
    Question("pref_distance", msg.Q_PREF_DISTANCE, "prefs", _validate_distance, "Try: same city, same state, or anywhere.", "preferences", "max_distance"),
    Question("pref_rel", msg.Q_PREF_RELATIONSHIP, "prefs", _validate_relationship, "Pick 1, 2, 3, or 4.", "relationship_type"),

    # === LIFESTYLE (12 questions) ===
    Question("work", msg.Q_LIFE_WORK, "lifestyle", _accept_any, "What do you do?", "lifestyle", "work"),
    Question("education", msg.Q_LIFE_EDUCATION, "lifestyle", _accept_any, "Your education?", "lifestyle", "education"),
    Question("smoking", msg.Q_LIFE_SMOKING, "lifestyle", _make_mapped_validator(SMOKING_MAP), "Pick 1, 2, or 3.", "lifestyle", "smoking"),
    Question("drinking", msg.Q_LIFE_DRINKING, "lifestyle", _make_mapped_validator(DRINKING_MAP), "Pick 1, 2, or 3.", "lifestyle", "drinking"),
    Question("diet", msg.Q_LIFE_DIET, "lifestyle", _make_mapped_validator(DIET_MAP), "Pick a number 1-6.", "lifestyle", "diet"),
    Question("exercise", msg.Q_LIFE_EXERCISE, "lifestyle", _make_mapped_validator(EXERCISE_MAP), "Pick 1, 2, 3, or 4.", "lifestyle", "exercise"),
    Question("sleep", msg.Q_LIFE_SLEEP, "lifestyle", _make_mapped_validator(SLEEP_MAP), "Pick 1, 2, or 3.", "lifestyle", "sleep_schedule"),
    Question("social", msg.Q_LIFE_SOCIAL, "lifestyle", _make_mapped_validator(SOCIAL_MAP), "Pick 1, 2, or 3.", "lifestyle", "social_style"),
    Question("living", msg.Q_LIFE_LIVING, "lifestyle", _make_mapped_validator(LIVING_MAP), "Pick 1, 2, 3, or 4.", "lifestyle", "living_situation"),
    Question("pets", msg.Q_LIFE_PETS, "lifestyle", _make_mapped_validator(PETS_MAP), "Pick a number 1-5.", "lifestyle", "pets"),
    Question("children", msg.Q_LIFE_CHILDREN, "lifestyle", _make_mapped_validator(CHILDREN_MAP), "Pick 1, 2, 3, or 4.", "lifestyle", "want_children"),

    # === VALUES (5 questions) ===
    Question("religion", msg.Q_VALUES_RELIGION, "values", _accept_any, "What's your faith?", "values_data", "religion"),
    Question("religious_level", msg.Q_VALUES_RELIGIOUS_LEVEL, "values", _make_mapped_validator(RELIGIOUS_LEVEL_MAP), "Pick 1, 2, or 3.", "values_data", "religious_level"),
    Question("politics", msg.Q_VALUES_POLITICS, "values", _make_mapped_validator(POLITICS_MAP), "Pick a number 1-5.", "values_data", "politics"),
    Question("ambition", msg.Q_VALUES_AMBITION, "values", _make_mapped_validator(AMBITION_MAP), "Pick 1, 2, 3, or 4.", "values_data", "career_ambition"),
    Question("finance", msg.Q_VALUES_FINANCE, "values", _make_mapped_validator(FINANCE_MAP), "Pick 1, 2, or 3.", "values_data", "financial_habits"),

    # === INTERESTS (1 question, multi-select) ===
    Question("interests", msg.Q_INTERESTS, "interests", _validate_interests, "Send numbers separated by commas (e.g., 1, 5, 7, 16).", "interests"),
]

TOTAL_QUESTIONS = len(QUESTIONS)


def get_question(index: int) -> Question | None:
    if 0 <= index < TOTAL_QUESTIONS:
        return QUESTIONS[index]
    return None


def get_section_for_index(index: int) -> str:
    q = get_question(index)
    return q.section if q else "complete"


def state_for_section(section: str) -> str:
    from src.bot.states import ConversationState
    mapping = {
        "basic": ConversationState.ONBOARDING_BASIC,
        "bio": ConversationState.ONBOARDING_BIO,
        "prefs": ConversationState.ONBOARDING_PREFERENCES,
        "lifestyle": ConversationState.ONBOARDING_LIFESTYLE,
        "values": ConversationState.ONBOARDING_VALUES,
        "interests": ConversationState.ONBOARDING_INTERESTS,
    }
    return mapping.get(section, ConversationState.ONBOARDING_PHOTOS)
