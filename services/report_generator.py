"""Markdown brand report generation (BRAND_KIT.md)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from services.brand_schemas import BrandAnalysis
from services.kit_generator import ALL_FORMAT_NAMES, FORMAT_SPECS

REPORT_FILENAME = "BRAND_KIT.md"


def _color_block(hex_color: str) -> str:
    return f'<span style="color:{hex_color}">██</span>'


def _format_dimensions(format_name: str) -> str:
    spec = FORMAT_SPECS.get(format_name)
    if not spec:
        return "—"
    size = spec["size"]
    if isinstance(size, tuple):
        return f"{size[0]}×{size[1]}"
    return "—"


def _parse_dos_and_donts(usage_notes: str) -> tuple[list[str], list[str]]:
    """Split usage notes into do's and don'ts when possible."""
    dos: list[str] = []
    donts: list[str] = []
    current: list[str] | None = None

    for raw_line in usage_notes.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("do") and ("don't" not in lower[:6]):
            current = dos
            if ":" in line:
                line = line.split(":", 1)[1].strip()
                if line:
                    dos.append(line)
            continue
        if "don't" in lower or "dont" in lower or "ne pas" in lower:
            current = donts
            if ":" in line:
                line = line.split(":", 1)[1].strip()
                if line:
                    donts.append(line)
            continue
        if line.startswith(("-", "•", "*")):
            item = line.lstrip("-•* ").strip()
            if item:
                (current or dos).append(item)
        elif current is not None:
            current.append(line)
        else:
            dos.append(line)

    if not dos and not donts and usage_notes.strip():
        dos.append(usage_notes.strip())

    return dos, donts


def _suggested_next_steps(brand_data: BrandAnalysis, assets: dict[str, str]) -> list[str]:
    steps: list[str] = []
    if "favicon" not in assets:
        steps.append("Générer le favicon et l'app icon pour le site web.")
    if not brand_data.components.get("has_wordmark"):
        steps.append("Créer une wordmark dédiée si le logo combiné manque de lisibilité.")
    steps.append("Valider les contrastes WCAG sur fond clair et fond sombre.")
    steps.append("Exporter les assets en SVG vectoriel pour le print et le merch.")
    if len(assets) < len(ALL_FORMAT_NAMES):
        steps.append("Compléter les formats réseaux sociaux manquants.")
    steps.append("Documenter les règles d'espacement minimum autour du logo.")
    return steps


def generate_brand_report(
    brand_data: BrandAnalysis,
    assets: dict[str, str],
    output_dir: str,
) -> str:
    """Write BRAND_KIT.md and return its repo-relative path."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / REPORT_FILENAME

    now = datetime.now(timezone.utc).strftime("%d/%m/%Y")
    mood = ", ".join(brand_data.mood) if brand_data.mood else "—"
    dos, donts = _parse_dos_and_donts(brand_data.usage_notes)

    lines: list[str] = [
        f"# Brand Kit — {brand_data.brand_name}  [{now}]",
        "",
    ]

    if brand_data.tagline:
        lines.extend([f"> {brand_data.tagline}", ""])

    lines.extend([
        "## Identité visuelle",
        "",
        f"- **Style** : {brand_data.style}",
        f"- **Mood** : {mood}",
        f"- **Typographie** : {brand_data.typography_style or '—'}",
        "",
        "## Palette de couleurs",
        "",
    ])

    for color in brand_data.colors:
        block = _color_block(color.hex)
        lines.append(f"- {block} `{color.hex}` — **{color.name}** ({color.role}, {color.source})")

    lines.extend(["", "## Composants détectés", ""])
    if brand_data.elements:
        for element in brand_data.elements:
            lines.append(f"- **{element.label}** ({element.type}) — {element.description}")
    else:
        lines.append("- Aucun composant segmenté.")

    if brand_data.components:
        flags = ", ".join(
            f"{key}: {'oui' if value else 'non'}"
            for key, value in sorted(brand_data.components.items())
        )
        lines.extend(["", f"Flags : {flags}"])

    lines.extend(["", "## Notes d'usage", ""])
    lines.extend(["### Do's", ""])
    if dos:
        lines.extend(f"- {item}" for item in dos)
    else:
        lines.append("- Respecter les marges de respiration autour du logo.")

    lines.extend(["", "### Don'ts", ""])
    if donts:
        lines.extend(f"- {item}" for item in donts)
    else:
        lines.append("- Ne pas déformer, recolorer ou placer le logo sur un fond peu contrasté.")

    lines.extend(["", "## Assets générés", ""])
    lines.append("| Format | Dimensions | Chemin |")
    lines.append("| --- | --- | --- |")

    for format_name in ALL_FORMAT_NAMES:
        if format_name in assets:
            lines.append(
                f"| {format_name} | {_format_dimensions(format_name)} | `{assets[format_name]}` |"
            )

    for format_name, file_path in sorted(assets.items()):
        if format_name not in ALL_FORMAT_NAMES:
            lines.append(f"| {format_name} | — | `{file_path}` |")

    lines.extend(["", "## Prochaines étapes suggérées", ""])
    for step in _suggested_next_steps(brand_data, assets):
        lines.append(f"- {step}")

    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")

    repo_root = Path(__file__).resolve().parent.parent
    return str(report_path.relative_to(repo_root)).replace("\\", "/")
