"""
skill_seo_audit.py — Audit SEO avec Lighthouse CLI

Dépendance : npm install -g lighthouse
"""

from __future__ import annotations

import json
import logging
import subprocess

logger = logging.getLogger(__name__)


def run_seo_audit(url: str) -> str:
    """
    Lance Lighthouse sur une URL et retourne un rapport SEO formaté.
    """
    try:
        result = subprocess.run(
            [
                "lighthouse",
                url,
                "--output=json",
                "--output-path=stdout",
                "--only-categories=seo,performance,best-practices,accessibility",
                "--chrome-flags=--headless --no-sandbox",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            return f"❌ Lighthouse échoué : {result.stderr[:300]}"

        data = json.loads(result.stdout)
        cats = data.get("categories", {})

        def score(cat: str) -> int:
            return int((cats.get(cat, {}).get("score", 0) or 0) * 100)

        report = f"""🔍 **Audit SEO — {url}**

**Scores :**
- SEO : {score('seo')}/100
- Performance : {score('performance')}/100
- Accessibilité : {score('accessibility')}/100
- Best Practices : {score('best-practices')}/100

**Issues critiques :**"""

        audits = data.get("audits", {})
        failed = [
            (k, v.get("title"), v.get("description", "")[:100])
            for k, v in audits.items()
            if v.get("score") is not None
            and v.get("score") < 0.9
            and v.get("scoreDisplayMode") not in ("informative", "not-applicable")
        ]

        for _, title, _desc in failed[:8]:
            report += f"\n⚠️ {title}"

        return report

    except FileNotFoundError:
        return "❌ Lighthouse non installé. Exécute : npm install -g lighthouse"
    except Exception as e:
        return f"❌ Erreur audit : {e}"
