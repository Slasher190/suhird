import re

VALID_GENDERS = {"male", "female", "non-binary", "other"}
VALID_RELATIONSHIP_TYPES = {"serious", "casual", "friends", "not sure"}
VALID_LIFESTYLE_OPTIONS = {
    "smoking": {"never", "sometimes", "regularly"},
    "drinking": {"never", "socially", "regularly"},
    "diet": {"vegetarian", "vegan", "non-vegetarian", "eggetarian", "jain", "no preference"},
    "exercise": {"never", "sometimes", "regularly", "daily"},
    "sleep_schedule": {"early bird", "night owl", "flexible"},
    "social_style": {"introvert", "extrovert", "ambivert"},
    "living_situation": {"alone", "with family", "with roommates", "other"},
    "pets": {"none", "dog", "cat", "both", "other"},
    "want_children": {"yes", "no", "maybe", "have children"},
}
VALID_VALUES_OPTIONS = {
    "religious_level": {"not religious", "somewhat religious", "very religious"},
    "politics": {"liberal", "moderate", "conservative", "not political", "other"},
    "career_ambition": {"relaxed", "balanced", "ambitious", "very ambitious"},
    "financial_habits": {"saver", "spender", "balanced"},
}
VALID_INTERESTS = {
    "sports", "fitness", "outdoor", "arts", "music", "movies", "books",
    "food", "cooking", "gaming", "tech", "fashion", "photography",
    "writing", "volunteering", "travel", "dance", "comedy",
    "spirituality", "science",
}


def validate_age(value: str) -> tuple[bool, int | None]:
    try:
        age = int(value.strip())
        if 18 <= age <= 100:
            return True, age
        return False, None
    except ValueError:
        return False, None


def validate_gender(value: str) -> tuple[bool, str | None]:
    g = value.strip().lower()
    if g in VALID_GENDERS:
        return True, g
    return False, None


def validate_phone(value: str) -> bool:
    return bool(re.match(r"^\+\d{10,15}$", value.strip()))


def validate_name(value: str) -> tuple[bool, str | None]:
    name = value.strip()
    if 1 <= len(name) <= 100 and re.match(r"^[a-zA-Z\s\.\-']+$", name):
        return True, name.title()
    return False, None


def validate_location(value: str) -> tuple[bool, str | None]:
    loc = value.strip()
    if 2 <= len(loc) <= 200:
        return True, loc.title()
    return False, None


def validate_relationship_type(value: str) -> tuple[bool, str | None]:
    rt = value.strip().lower()
    if rt in VALID_RELATIONSHIP_TYPES:
        return True, rt
    return False, None


def validate_age_range(value: str) -> tuple[bool, dict | None]:
    """Parse age range like '25-35'."""
    m = re.match(r"^(\d{2})\s*[-–]\s*(\d{2,3})$", value.strip())
    if m:
        low, high = int(m.group(1)), int(m.group(2))
        if 18 <= low < high <= 100:
            return True, {"min": low, "max": high}
    return False, None


def validate_interests(values: list[str]) -> tuple[bool, list[str]]:
    cleaned = [v.strip().lower() for v in values if v.strip().lower() in VALID_INTERESTS]
    return len(cleaned) > 0, cleaned
