"""
skill_browser_use.py — Navigation web automatisée avec Playwright

Utilisé par Marketing Agent pour veille concurrentielle et scraping public.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def browse_url(url: str, wait_for: str | None = None) -> str:
    """
    Navigue sur une URL et retourne le contenu textuel.
    """
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            if wait_for:
                page.wait_for_selector(wait_for, timeout=5000)
            content = page.inner_text("body")
            browser.close()
            return content[:3000]
    except ModuleNotFoundError:
        return "❌ Playwright non installé — exécute : pip install playwright && playwright install chromium"
    except Exception as e:
        return f"❌ Erreur navigation {url} : {e}"


def search_web(query: str, limit: int = 5) -> list[dict[str, str]]:
    """
    Recherche sur DuckDuckGo (privacy-friendly, pas de clé API).
    """
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}")
            results: list[dict[str, str]] = []
            items = page.query_selector_all(".result")
            for item in items[:limit]:
                try:
                    title_el = item.query_selector(".result__title")
                    url_el = item.query_selector(".result__url")
                    snippet_el = item.query_selector(".result__snippet")
                    results.append(
                        {
                            "title": title_el.inner_text() if title_el else "",
                            "url": url_el.inner_text() if url_el else "",
                            "snippet": snippet_el.inner_text() if snippet_el else "",
                        }
                    )
                except Exception:
                    continue
            browser.close()
            return results
    except ModuleNotFoundError:
        logger.error("Playwright non installé — exécute : pip install playwright && playwright install chromium")
        return []
    except Exception as e:
        logger.error("Erreur search_web : %s", e)
        return []
