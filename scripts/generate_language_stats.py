#!/usr/bin/env python3
"""Generate a most-used-languages SVG card from the GitHub REST API.

Replaces github-readme-stats' top-langs card with a self-hosted equivalent:
aggregates language bytes across the owner's non-fork public repositories
and renders a compact dark card matching the profile README theme.
"""
import json
import os
import urllib.request

USER = "FethiOmur"
LIMIT = 8
OUT = "language-stats.svg"

# Markup/styling drowns out actual programming languages by byte count
# (the RouteRush landing pages alone contribute >1MB of generated HTML).
IGNORED_LANGUAGES = {"HTML", "CSS"}

# GitHub linguist colors for languages likely to appear; gray fallback below.
COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "HTML": "#e34c26", "CSS": "#563d7c", "C#": "#178600", "Dart": "#00B4AB",
    "Jupyter Notebook": "#DA5B0B", "Swift": "#F05138", "Shell": "#89e051",
    "C++": "#f34b7d", "Java": "#b07219", "Go": "#00ADD8", "Rust": "#dea584",
    "Kotlin": "#A97BFF", "Ruby": "#701516", "PHP": "#4F5D95", "C": "#555555",
    "Vue": "#41b883", "SCSS": "#c6538c",
}
FALLBACK = "#8b949e"


def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def collect():
    totals = {}
    repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
    for repo in repos:
        if repo.get("fork"):
            continue
        for lang, size in api(repo["languages_url"]).items():
            if lang in IGNORED_LANGUAGES:
                continue
            totals[lang] = totals.get(lang, 0) + size
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:LIMIT]
    total = sum(size for _, size in ranked) or 1
    return [(lang, size / total * 100) for lang, size in ranked]


def render(langs):
    width, pad = 500, 25
    bar_y, bar_h = 60, 10
    bar_w = width - 2 * pad
    rows_y, row_h = 95, 25
    cols = 2
    col_w = bar_w // cols

    parts, x = [], pad
    for lang, pct in langs:
        w = bar_w * pct / 100
        parts.append(
            f'<rect x="{x:.1f}" y="{bar_y}" width="{w:.1f}" height="{bar_h}" '
            f'fill="{COLORS.get(lang, FALLBACK)}" />'
        )
        x += w

    for i, (lang, pct) in enumerate(langs):
        cx = pad + (i % cols) * col_w
        cy = rows_y + (i // cols) * row_h
        parts.append(
            f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{COLORS.get(lang, FALLBACK)}" />'
            f'<text x="{cx + 18}" y="{cy}" class="lang">{lang} '
            f'<tspan class="pct">{pct:.1f}%</tspan></text>'
        )

    rows = (len(langs) + cols - 1) // cols
    height = rows_y + rows * row_h + 5
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Most used languages">
  <style>
    .title {{ font: 600 18px 'Segoe UI', Ubuntu, sans-serif; fill: #ffffff; }}
    .lang {{ font: 400 13px 'Segoe UI', Ubuntu, sans-serif; fill: #c9d1d9; }}
    .pct {{ fill: #8b949e; }}
  </style>
  <rect width="{width}" height="{height}" rx="8" fill="#0D1117" />
  <text x="{pad}" y="35" class="title">Most Used Languages</text>
  <clipPath id="bar"><rect x="{pad}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="5" /></clipPath>
  <g clip-path="url(#bar)">{''.join(p for p in parts if p.startswith('<rect'))}</g>
  {''.join(p for p in parts if not p.startswith('<rect'))}
</svg>
"""


def main():
    langs = collect()
    if not langs:
        raise SystemExit("no language data collected — refusing to write an empty card")
    with open(OUT, "w") as f:
        f.write(render(langs))
    print(f"wrote {OUT}: " + ", ".join(f"{l} {p:.1f}%" for l, p in langs))


if __name__ == "__main__":
    main()
