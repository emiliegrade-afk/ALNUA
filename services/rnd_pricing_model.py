"""Product pricing + subscriber-based revenue for R&D dossier business cases."""

from __future__ import annotations

from typing import Any

from services.rnd_pricing_defaults import (
    BASE_PAYING_SUBSCRIBERS,
    DOMAIN_TIER_DEFAULTS,
    EFFORT_M12_SCALE,
    EFFORT_M3_SCALE,
    PRICE_RE,
    RANGE_RE,
    TIER_LINE_RE,
    parse_price,
)


def _blended_arpu(tiers: list[dict[str, Any]]) -> float:
    total_mix = sum(float(t.get("mix_pct") or 0) for t in tiers) or 1.0
    weighted = 0.0
    for tier in tiers:
        price = float(tier["price_eur"])
        billing = tier.get("billing", "monthly")
        if billing == "yearly":
            price = price / 12.0
        elif billing == "one_time":
            price = price * 0.08  # amortized monthly attach over ~12 mo
        mix = float(tier.get("mix_pct") or 0) / total_mix
        weighted += price * mix
    return round(weighted, 2)


def _tiers_from_extracted_prices(prices: list[float], domain: str) -> list[dict[str, Any]]:
    """Build 3-4 tiers from prices found in dossier text."""
    unique = sorted(set(p for p in prices if 1 <= p <= 500))
    if not unique:
        return []
    if len(unique) == 1:
        p = unique[0]
        return [
            {"name": "Solo", "price_eur": round(p * 0.6, 2), "mix_pct": 0.45},
            {"name": "Pro", "price_eur": p, "mix_pct": 0.35},
            {"name": "Team", "price_eur": round(p * 2.2, 2), "mix_pct": 0.20},
        ]
    if len(unique) == 2:
        low, high = unique[0], unique[-1]
        mid = round((low + high) / 2, 2)
        return [
            {"name": "Starter", "price_eur": low, "mix_pct": 0.45},
            {"name": "Pro", "price_eur": mid, "mix_pct": 0.35},
            {"name": "Business", "price_eur": high, "mix_pct": 0.20},
        ]
    picks = unique[:4] if len(unique) >= 4 else unique
    names = ["Starter", "Pro", "Studio", "Business"][: len(picks)]
    mixes = [0.42, 0.32, 0.18, 0.08][: len(picks)]
    return [
        {"name": names[i], "price_eur": round(picks[i], 2), "mix_pct": mixes[i]}
        for i in range(len(picks))
    ]


def infer_pricing_model(
    *,
    domain: str | None,
    title: str = "",
    description: str = "",
    section_text: str = "",
) -> dict[str, Any]:
    """Infer subscription tiers from dossier content or domain defaults."""
    dom = (domain or "autre").lower()
    blob = f"{title}\n{description}\n{section_text}"
    source = "domain_default"

    tiers: list[dict[str, Any]] = []
    range_match = RANGE_RE.search(blob)
    if range_match:
        low = parse_price(range_match.group(1))
        high = parse_price(range_match.group(2))
        mid = round((low + high) / 2, 2)
        tiers = [
            {"name": "Starter", "price_eur": low, "mix_pct": 0.42},
            {"name": "Pro", "price_eur": mid, "mix_pct": 0.33},
            {"name": "Business", "price_eur": high, "mix_pct": 0.25},
        ]
        source = "extracted_range"

    if not tiers:
        for m in TIER_LINE_RE.finditer(blob):
            tiers.append(
                {"name": m.group(1).capitalize(), "price_eur": parse_price(m.group(2)), "mix_pct": 0.0}
            )
        if tiers:
            even = round(1.0 / len(tiers), 2)
            for t in tiers:
                t["mix_pct"] = even
            source = "extracted_tiers"

    if not tiers:
        prices = []
        for m in PRICE_RE.finditer(blob):
            raw = m.group(1) or m.group(2)
            if raw:
                prices.append(parse_price(raw))
        tiers = _tiers_from_extracted_prices(prices, dom)
        if tiers:
            source = "extracted_prices"

    if not tiers:
        tiers = [dict(t) for t in DOMAIN_TIER_DEFAULTS.get(dom, DOMAIN_TIER_DEFAULTS["autre"])]
        source = f"domain_default_{dom}"

    arpu = _blended_arpu(tiers)
    is_subscription = dom in ("saas", "ia", "app", "autre") or any(
        t.get("billing", "monthly") == "monthly" for t in tiers
    )

    return {
        "model_type": "subscription_tiers" if is_subscription else "mixed",
        "currency": "EUR",
        "tiers": tiers,
        "blended_arpu_eur": arpu,
        "price_range_eur": {
            "min": min(float(t["price_eur"]) for t in tiers),
            "max": max(float(t["price_eur"]) for t in tiers),
        },
        "source": source,
        "promo_note": (
            "Scénario médian sans promo payante — early-bird -20% possible sur Starter "
            "pour accélérer les 20 premiers clients."
        ),
    }


def _subscriber_counts(
    domain: str | None,
    effort: str | None,
    *,
    constraint: str | None = None,
) -> dict[str, int]:
    dom = (domain or "autre").lower()
    base = BASE_PAYING_SUBSCRIBERS.get(dom, BASE_PAYING_SUBSCRIBERS["autre"])
    eff = (effort or "M").upper()
    m3_scale = EFFORT_M3_SCALE.get(eff, 1.0)
    m12_scale = EFFORT_M12_SCALE.get(eff, 1.0)

    subs = {
        "m3": max(1, int(base["m3"] * m3_scale)),
        "m6": max(1, int(base["m6"] * ((m3_scale + m12_scale) / 2))),
        "m12": max(1, int(base["m12"] * m12_scale)),
    }
    if constraint and "reduce" in constraint.lower():
        if "50" in constraint:
            subs = {k: max(1, int(v * 0.5)) for k, v in subs.items()}
        elif "30" in constraint:
            subs = {k: max(1, int(v * 0.7)) for k, v in subs.items()}
    return subs


def _mrr_from_subscribers(subscribers: int, arpu: float) -> float:
    return round(subscribers * arpu, 2)


def _monthly_mrr_curve(m3: float, m6: float, m12: float) -> list[float]:
    """12-month MRR ramp — realistic solo-founder acquisition curve."""
    curve: list[float] = []
    for month in range(1, 13):
        if month <= 3:
            factor = {1: 0.4, 2: 0.72, 3: 1.0}[month]
            curve.append(round(m3 * factor, 2))
        elif month <= 6:
            t = (month - 3) / 3.0
            curve.append(round(m3 + (m6 - m3) * t, 2))
        else:
            t = (month - 6) / 6.0
            curve.append(round(m6 + (m12 - m6) * t, 2))
    return curve


def revenue_from_pricing(
    *,
    domain: str | None,
    effort: str | None,
    title: str = "",
    description: str = "",
    section_text: str = "",
    constraint: str | None = None,
    portfolio_monthly: float = 0.0,
    per_app_monthly: float = 0.0,
    active_apps: int = 0,
) -> dict[str, Any]:
    """Build revenue_hypothesis from product pricing × paying subscribers."""
    pricing = infer_pricing_model(
        domain=domain,
        title=title,
        description=description,
        section_text=section_text,
    )
    arpu = float(pricing["blended_arpu_eur"])
    subs = _subscriber_counts(domain, effort, constraint=constraint)

    m3_mrr = _mrr_from_subscribers(subs["m3"], arpu)
    m6_mrr = _mrr_from_subscribers(subs["m6"], arpu)
    m12_mrr = _mrr_from_subscribers(subs["m12"], arpu)

    curve = _monthly_mrr_curve(m3_mrr, m6_mrr, m12_mrr)
    cumulative_6m = round(sum(curve[:6]), 2)
    cumulative_12m = round(sum(curve), 2)

    cons_factor = 0.35
    opt_sub_factor = 1.85
    opt_arpu_factor = 1.12  # slightly higher tier mix when traction

    return {
        "pricing_model": pricing,
        "paying_subscribers": subs,
        "blended_arpu_eur": arpu,
        "m3_monthly_run_rate_eur": m3_mrr,
        "m6_monthly_run_rate_eur": m6_mrr,
        "m12_monthly_run_rate_eur": m12_mrr,
        "monthly_mrr_curve": curve,
        "cumulative_6m_eur": cumulative_6m,
        "cumulative_12m_eur": cumulative_12m,
        "conservative_m3_monthly_eur": round(m3_mrr * cons_factor, 2),
        "conservative_m6_monthly_eur": round(m6_mrr * cons_factor, 2),
        "conservative_m12_monthly_eur": round(m12_mrr * cons_factor, 2),
        "optimistic_m3_monthly_eur": round(m3_mrr * opt_sub_factor, 2),
        "optimistic_m6_monthly_eur": round(m6_mrr * opt_sub_factor * opt_arpu_factor, 2),
        "optimistic_m12_monthly_eur": round(m12_mrr * opt_sub_factor * opt_arpu_factor, 2),
        "conservative_cumulative_12m_eur": round(cumulative_12m * cons_factor, 2),
        "optimistic_cumulative_12m_eur": round(cumulative_12m * opt_sub_factor * opt_arpu_factor, 2),
        "portfolio_baseline_monthly_eur": portfolio_monthly,
        "per_app_baseline_monthly_eur": per_app_monthly,
        "active_apps_count": active_apps,
        "pricing_eur": arpu,
        "users_m6": subs["m6"],
        "users_m12": subs["m12"],
        "revenue_m6_eur": m6_mrr,
        "revenue_m12_eur": m12_mrr,
    }
