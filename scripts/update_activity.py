"""Render a daily SVG from public personal-repository metadata.

No third-party packages or personal token are needed. On API failure the
existing image is kept, and the workflow reports a failure instead of publishing
made-up activity. The profile repository is excluded from project activity.
"""

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
USER = "roebssie"


def public_repositories():
    repositories = []
    page = 1
    while True:
        request = Request(
            f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "roebssie-profile"},
        )
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        repositories.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return [r for r in repositories if not r["fork"] and r["name"].lower() != USER]


def render(repositories, today, mobile=False):
    recent = sorted(
        (r for r in repositories if r.get("pushed_at")),
        key=lambda r: r["pushed_at"],
        reverse=True,
    )[:2]
    rows = []
    for i, repository in enumerate(recent):
        y = 88 + i * 49
        name = repository["name"]
        limit = 28 if mobile else 45
        name = name if len(name) <= limit else name[:limit - 3] + "…"
        pushed = datetime.fromisoformat(repository["pushed_at"].replace("Z", "+00:00"))
        date = pushed.strftime("%d %b %Y")
        language = repository.get("language") or "Source code"
        rows.append(
            f'<circle cx="28" cy="{y - 5}" r="3" fill="#9edfc1"/>'
            f'<text x="43" y="{y}" class="name">{escape(name)}</text>'
            f'<text x="43" y="{y + 19}" class="meta">'
            f'{escape(language)} · last pushed {date}</text>'
        )
    if not recent:
        rows.append('<text x="28" y="90" class="name">New experiments start here.</text>')
    stamp = today.strftime("%d %b %Y")
    width, height = (480, 235) if mobile else (900, 195)
    stats = (
        f'<text x="28" y="190" class="meta">{len(repositories):02d} public personal repos</text>'
        f'<text x="28" y="213" class="meta">Refreshed {stamp} UTC · daily</text>'
        if mobile else
        f'<text x="872" y="93" text-anchor="end" fill="#b2f5d7" font-size="37" font-weight="700">{len(repositories):02d}</text>'
        '<text x="872" y="114" text-anchor="end" class="meta">public personal repos</text>'
        f'<text x="872" y="168" text-anchor="end" class="meta">Refreshed {stamp} UTC · daily</text>'
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">From the workbench</title>
  <desc id="desc">Public personal repositories, refreshed {stamp} UTC. {len(repositories)} repositories, excluding forks and the profile repository.</desc>
  <style>
    text {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; }}
    .name {{ fill:#e9eff7; font-size:{20 if mobile else 17}px; font-weight:600; }}
    .meta {{ fill:#9bacc3; font-size:{15 if mobile else 13}px; }}
  </style>
  <rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="16" fill="#111c2b" stroke="#314155"/>
  <text x="28" y="37" fill="#bcafff" font-size="12" font-weight="600" letter-spacing="2">RECENT PERSONAL ACTIVITY</text>
  <line x1="28" y1="52" x2="{width - 28}" y2="52" stroke="#314155"/>
  {''.join(rows)}
  {stats}
</svg>
'''


def main():
    repositories = public_repositories()
    today = datetime.now(timezone.utc)
    for mobile, filename in [(False, "activity.svg"), (True, "activity-mobile.svg")]:
        target = ROOT / "assets" / filename
        target.parent.mkdir(exist_ok=True)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(render(repositories, today, mobile), encoding="utf-8")
        temporary.replace(target)
    print("Updated the public activity card.")


if __name__ == "__main__":
    main()
