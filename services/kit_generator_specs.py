"""Brand kit format specifications and constants."""

from __future__ import annotations

# All 19 PNG formats + logo_horizontal; BRAND_KIT.md is produced by report_generator.
FORMAT_SPECS: dict[str, dict[str, object]] = {
    # Profiles
    "instagram_profile": {"size": (320, 320), "category": "profiles", "layout": "centered"},
    "tiktok_profile": {"size": (200, 200), "category": "profiles", "layout": "centered"},
    "x_profile": {"size": (400, 400), "category": "profiles", "layout": "centered"},
    "youtube_profile": {"size": (800, 800), "category": "profiles", "layout": "centered"},
    "linkedin_profile": {"size": (300, 300), "category": "profiles", "layout": "centered"},
    "favicon": {"size": (32, 32), "category": "profiles", "layout": "centered"},
    "app_icon": {"size": (1024, 1024), "category": "profiles", "layout": "centered"},
    # Banners
    "x_header": {"size": (1500, 500), "category": "banners", "layout": "banner"},
    "youtube_banner": {"size": (2560, 1440), "category": "banners", "layout": "banner"},
    "linkedin_banner": {"size": (1128, 191), "category": "banners", "layout": "banner"},
    "facebook_cover": {"size": (820, 312), "category": "banners", "layout": "banner"},
    # Posts
    "instagram_post": {"size": (1080, 1080), "category": "posts", "layout": "centered"},
    "instagram_story": {"size": (1080, 1920), "category": "posts", "layout": "vertical"},
    "tiktok_cover": {"size": (1080, 1920), "category": "posts", "layout": "vertical"},
    # Isolated assets
    "symbol_transparent": {"size": (1000, 1000), "category": "isolated", "layout": "isolated"},
    "wordmark_transparent": {"size": (2000, 500), "category": "isolated", "layout": "isolated"},
    "logo_dark_bg": {"size": (1000, 1000), "category": "isolated", "layout": "isolated"},
    "logo_light_bg": {"size": (1000, 1000), "category": "isolated", "layout": "isolated"},
    "logo_horizontal": {"size": (2000, 600), "category": "isolated", "layout": "horizontal"},
}

ALL_FORMAT_NAMES: list[str] = list(FORMAT_SPECS.keys())
ISOLATED_FORMAT_NAMES = frozenset(
    name for name, spec in FORMAT_SPECS.items() if spec["category"] == "isolated"
)

PADDING_RATIO = 0.15
