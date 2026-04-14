from enum import Enum


class ConversationState(str, Enum):
    NEW = "new"
    ONBOARDING_BASIC = "onboarding_basic"
    ONBOARDING_BIO = "onboarding_bio"
    ONBOARDING_PREFERENCES = "onboarding_prefs"
    ONBOARDING_LIFESTYLE = "onboarding_life"
    ONBOARDING_VALUES = "onboarding_values"
    ONBOARDING_INTERESTS = "onboarding_interests"
    ONBOARDING_PHOTOS = "onboarding_photos"
    PROFILE_COMPLETE = "profile_complete"
    BROWSING = "browsing"
    AWAITING_ACTION = "awaiting_action"
