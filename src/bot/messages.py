"""Pre-formatted WhatsApp message templates for Suhird bot."""

WELCOME = (
    "Namaste! 🙏 I'm *Suhird* (सुहृद्) — your good-hearted friend.\n\n"
    "I'm here to help you find meaningful connections. Let's build your profile "
    "step by step — it only takes a few minutes!\n\n"
    "Ready? Let's start with the basics. 😊"
)

WELCOME_BACK = (
    "Welcome back! 👋 Looks like you were in the middle of setting up your profile.\n"
    "Let's continue where we left off!"
)

ONBOARDING_COMPLETE = (
    "🎉 *Your profile is complete!*\n\n"
    "You're all set to start meeting people. Type *\"show matches\"* to see "
    "your top recommendations, or *\"my profile\"* to review your profile."
)

PROFILE_SUMMARY = (
    "📋 *Your Profile*\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "👤 *Name:* {name}\n"
    "🎂 *Age:* {age}\n"
    "⚧ *Gender:* {gender}\n"
    "📍 *Location:* {location}\n"
    "💝 *Looking for:* {relationship_type}\n"
    "🎯 *Interests:* {interests}\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "📸 *Photos:* {photo_count}/6\n\n"
    "Type *\"show matches\"* to browse profiles!"
)

MATCH_CARD = (
    "━━━━━━━━━━━━━━━━━━\n"
    "#{index} 👤 *{name}*, {age}\n"
    "📍 {location}\n"
    "💝 {relationship_type}\n"
    "🎯 {interests}\n"
    "{bio_highlight}\n"
    "━━━━━━━━━━━━━━━━━━"
)

MATCH_BATCH_HEADER = (
    "💕 *Here are your top matches!*\n"
    "━━━━━━━━━━━━━━━━━━\n"
)

MATCH_BATCH_FOOTER = (
    "\n━━━━━━━━━━━━━━━━━━\n"
    "Reply with:\n"
    "• *Like 1* — to like profile #1\n"
    "• *Pass 1* — to skip profile #1\n"
    "• *Like all* — to like all shown\n"
    "• *Pass all* — to skip all shown\n"
    "• *More* — to see next batch\n"
    "• *Stop* — to stop browsing"
)

MUTUAL_MATCH = (
    "🎉✨ *It's a Match!* ✨🎉\n\n"
    "You and *{match_name}* both liked each other!\n\n"
    "📱 Their number: {match_phone}\n\n"
    "Go ahead and say hi — your good-hearted friend is cheering for you! 💕"
)

MUTUAL_MATCH_OTHER = (
    "🎉✨ *It's a Match!* ✨🎉\n\n"
    "*{match_name}* liked you back!\n\n"
    "📱 Their number: {match_phone}\n\n"
    "They'll be reaching out — or feel free to message first! 💕"
)

NO_MATCHES = (
    "😔 No matches available right now. Check back later — "
    "new people join every day!"
)

NO_MORE_MATCHES = (
    "You've seen all available profiles for now. "
    "Check back later for new ones! 🔄"
)

LIKED = "❤️ You liked *{name}*!"
PASSED = "⏭️ You passed on *{name}*."

PHOTO_REQUEST = (
    "📸 Time to add your photos! Upload up to 6 photos.\n"
    "Send a photo now, or type *skip* to continue without photos."
)

PHOTO_RECEIVED = "📸 Photo {n}/6 saved! Send another or type *done* to finish."
PHOTO_LIMIT = "📸 You've reached the 6-photo limit! Type *done* to continue."

INVALID_INPUT = "🤔 I didn't quite get that. {hint}"
HELP_TEXT = (
    "📖 *Suhird Commands*\n"
    "━━━━━━━━━━━━━━━━━━\n"
    "• *show matches* — See your recommendations\n"
    "• *my profile* — View your profile\n"
    "• *edit profile* — Update your info\n"
    "• *help* — Show this menu\n"
    "• *block* — Block the last shown profile\n"
    "• *report* — Report inappropriate behavior"
)

BLOCKED = "🚫 You've blocked this user. They won't appear in your matches."
REPORTED = "🚨 Thank you for reporting. We'll review this profile."

# --- Onboarding question templates ---

Q_NAME = "What's your name? ✍️"
Q_AGE = "How old are you? 🎂 (must be 18+)"
Q_GENDER = (
    "What's your gender?\n"
    "1️⃣ Male\n"
    "2️⃣ Female\n"
    "3️⃣ Non-binary\n"
    "4️⃣ Other"
)
Q_LOCATION = "Where are you based? 📍 (city, state)"

# Bio prompts
Q_BIO_SIMPLE_PLEASURES = "🌸 *Simple pleasures:* What's something small that makes your day?"
Q_BIO_HOW_I_RELAX = "🧘 *How I relax:* What do you do to unwind?"
Q_BIO_WHAT_IF = "🤫 *What if I told you...* Finish this sentence!"
Q_BIO_TRAVEL_STORY = "✈️ *Best travel story:* Share your favorite adventure!"
Q_BIO_TWO_TRUTHS = "🎭 *Two truths and a lie:* Give us three statements!"
Q_BIO_STRENGTH = "💪 *Greatest strength:* What are you most proud of?"
Q_BIO_GREEN_FLAGS = "🟢 *Green flags you love:* What makes you swipe right?"
Q_BIO_DATING_ME = "💕 *Dating me is like...* Finish this sentence!"

# Preferences
Q_PREF_GENDER = (
    "Who are you looking for?\n"
    "1️⃣ Men\n"
    "2️⃣ Women\n"
    "3️⃣ Everyone"
)
Q_PREF_AGE_RANGE = "What age range? (e.g., *25-35*)"
Q_PREF_DISTANCE = "Maximum distance? (e.g., *same city*, *same state*, *anywhere*)"
Q_PREF_RELATIONSHIP = (
    "What kind of relationship?\n"
    "1️⃣ Serious\n"
    "2️⃣ Casual\n"
    "3️⃣ Friends\n"
    "4️⃣ Not sure"
)

# Lifestyle
Q_LIFE_WORK = "💼 What do you do for work?"
Q_LIFE_EDUCATION = "🎓 Your education level?"
Q_LIFE_SMOKING = (
    "🚬 Smoking?\n"
    "1️⃣ Never\n"
    "2️⃣ Sometimes\n"
    "3️⃣ Regularly"
)
Q_LIFE_DRINKING = (
    "🍷 Drinking?\n"
    "1️⃣ Never\n"
    "2️⃣ Socially\n"
    "3️⃣ Regularly"
)
Q_LIFE_DIET = (
    "🍽️ Diet preference?\n"
    "1️⃣ Vegetarian\n"
    "2️⃣ Vegan\n"
    "3️⃣ Non-vegetarian\n"
    "4️⃣ Eggetarian\n"
    "5️⃣ Jain\n"
    "6️⃣ No preference"
)
Q_LIFE_EXERCISE = (
    "🏋️ Exercise?\n"
    "1️⃣ Never\n"
    "2️⃣ Sometimes\n"
    "3️⃣ Regularly\n"
    "4️⃣ Daily"
)
Q_LIFE_SLEEP = (
    "😴 Sleep schedule?\n"
    "1️⃣ Early bird\n"
    "2️⃣ Night owl\n"
    "3️⃣ Flexible"
)
Q_LIFE_SOCIAL = (
    "🗣️ Social style?\n"
    "1️⃣ Introvert\n"
    "2️⃣ Extrovert\n"
    "3️⃣ Ambivert"
)
Q_LIFE_LIVING = (
    "🏠 Living situation?\n"
    "1️⃣ Alone\n"
    "2️⃣ With family\n"
    "3️⃣ With roommates\n"
    "4️⃣ Other"
)
Q_LIFE_PETS = (
    "🐾 Pets?\n"
    "1️⃣ None\n"
    "2️⃣ Dog\n"
    "3️⃣ Cat\n"
    "4️⃣ Both\n"
    "5️⃣ Other"
)
Q_LIFE_CHILDREN = (
    "👶 Want children?\n"
    "1️⃣ Yes\n"
    "2️⃣ No\n"
    "3️⃣ Maybe\n"
    "4️⃣ Have children"
)

# Values
Q_VALUES_RELIGION = "🛕 What's your religion/spiritual path? (or type *none*)"
Q_VALUES_RELIGIOUS_LEVEL = (
    "🙏 How religious are you?\n"
    "1️⃣ Not religious\n"
    "2️⃣ Somewhat religious\n"
    "3️⃣ Very religious"
)
Q_VALUES_POLITICS = (
    "🏛️ Political leaning?\n"
    "1️⃣ Liberal\n"
    "2️⃣ Moderate\n"
    "3️⃣ Conservative\n"
    "4️⃣ Not political\n"
    "5️⃣ Other"
)
Q_VALUES_AMBITION = (
    "📈 Career ambition?\n"
    "1️⃣ Relaxed\n"
    "2️⃣ Balanced\n"
    "3️⃣ Ambitious\n"
    "4️⃣ Very ambitious"
)
Q_VALUES_FINANCE = (
    "💰 Financial habits?\n"
    "1️⃣ Saver\n"
    "2️⃣ Spender\n"
    "3️⃣ Balanced"
)

# Interests
Q_INTERESTS = (
    "🎯 *Pick your interests!* (send the numbers separated by commas)\n\n"
    "1️⃣ Sports  2️⃣ Fitness  3️⃣ Outdoor\n"
    "4️⃣ Arts  5️⃣ Music  6️⃣ Movies\n"
    "7️⃣ Books  8️⃣ Food  9️⃣ Cooking\n"
    "🔟 Gaming  1️⃣1️⃣ Tech  1️⃣2️⃣ Fashion\n"
    "1️⃣3️⃣ Photography  1️⃣4️⃣ Writing  1️⃣5️⃣ Volunteering\n"
    "1️⃣6️⃣ Travel  1️⃣7️⃣ Dance  1️⃣8️⃣ Comedy\n"
    "1️⃣9️⃣ Spirituality  2️⃣0️⃣ Science"
)

INTERESTS_MAP = {
    "1": "sports", "2": "fitness", "3": "outdoor",
    "4": "arts", "5": "music", "6": "movies",
    "7": "books", "8": "food", "9": "cooking",
    "10": "gaming", "11": "tech", "12": "fashion",
    "13": "photography", "14": "writing", "15": "volunteering",
    "16": "travel", "17": "dance", "18": "comedy",
    "19": "spirituality", "20": "science",
}
