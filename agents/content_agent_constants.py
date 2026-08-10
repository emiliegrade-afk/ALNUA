"""Content agent — platform and content-type constants."""

from __future__ import annotations

VALID_PLATFORMS = frozenset({"instagram", "tiktok", "x", "youtube", "linkedin", "website_blog"})
VALID_CONTENT_TYPES = frozenset({
    "announcement", "teaser", "tutorial", "behind_scenes", "short_video",
})

PLATFORM_RULES: dict[str, str] = {
    "instagram": (
        "Instagram : texte 150-300 mots, émojis naturels, 20-25 hashtags en fin de post."
    ),
    "tiktok": (
        "TikTok : hook percutant en 1ère ligne, texte court (caption), 5-8 hashtags tendance."
    ),
    "x": "X (Twitter) : max 280 caractères, punch direct, 2-3 hashtags max.",
    "youtube": (
        "YouTube Shorts : titre accrocheur en 1ère ligne, puis description + tags/hashtags."
    ),
    "linkedin": (
        "LinkedIn : ton professionnel, 100-200 mots, pas d'émojis excessifs, 3-5 hashtags."
    ),
}

CONTENT_TYPE_HINTS: dict[str, str] = {
    "announcement": "Annonce de feature — clair, enthousiaste, orienté bénéfice utilisateur.",
    "teaser": "Teaser mystère — intrigue sans tout révéler, crée de la curiosité.",
    "behind_scenes": "Behind the scenes — authenticité solo dev, coulisses du build.",
    "tutorial": "Tutoriel court — une astuce actionnable, étapes concises.",
    "short_video": "Hype / engagement — énergie, question à la communauté, CTA.",
    "lore": "Lore / univers (Wyrdheim) — immersion, worldbuilding, ton épique.",
}
