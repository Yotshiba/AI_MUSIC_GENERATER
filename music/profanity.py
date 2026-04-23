"""
REQ-5.2.1: Content safety filter for user-submitted text inputs.
Checks against a blocklist of English profanity and Thai-law-sensitive terms.
"""

_BAD_WORDS = frozenset([
    # Common English profanity
    "fuck", "fucking", "fucker", "shit", "shitting", "bitch", "bitches",
    "bastard", "asshole", "ass", "dick", "cock", "cunt", "pussy", "whore",
    "slut", "nigger", "nigga", "faggot", "fag", "retard", "motherfucker",
    "motherfucking", "damn", "crap", "piss", "prick", "twat",
    # Thai-law sensitive (transliterated / common spellings)
    "lese", "majeste", "lesemajeste", "monarchy", "defame", "defamation",
    "terrorist", "terrorism", "bomb", "kill", "murder", "rape",
    "porn", "pornography", "sex", "naked", "nude",
])


def contains_profanity(text: str) -> bool:
    """Return True if text contains any blocked word (case-insensitive)."""
    cleaned = text.lower()
    for char in ".,!?\"'()-_":
        cleaned = cleaned.replace(char, " ")
    return any(word in _BAD_WORDS for word in cleaned.split())
