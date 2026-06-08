import os
import json
import urllib.request
from datetime import date, timedelta

USERNAME = os.environ.get("GITHUB_USERNAME", "chekerh")
TOKEN = os.environ["GITHUB_TOKEN"]

today = date.today()
start = today - timedelta(days=365)

query = '''
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            color
          }
        }
      }
    }
  }
}
'''

variables = {
    "login": USERNAME,
    "from": f"{start.isoformat()}T00:00:00Z",
    "to": f"{today.isoformat()}T23:59:59Z",
}

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    },
)

with urllib.request.urlopen(request) as response:
    data = json.loads(response.read().decode("utf-8"))

if "errors" in data:
    raise RuntimeError(json.dumps(data["errors"], indent=2))

weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

days = []
for week_index, week in enumerate(weeks):
    for day_index, day in enumerate(week["contributionDays"]):
        days.append({
            "date": day["date"],
            "count": int(day["contributionCount"]),
            "color": day["color"],
            "x": 55 + week_index * 14,
            "y": 88 + day_index * 14,
        })

# Important: use the lowest NON-ZERO commit days first.
# If we target zero-commit days, "commits eaten" will always display 0.
positive_days = [d for d in days if d["count"] > 0]
quiet_days = [d for d in days if d["count"] == 0]

targets = sorted(positive_days, key=lambda d: (d["count"], d["date"]))[:14]

# Fallback only if the account has fewer than 14 positive days in the last year.
if len(targets) < 14:
    targets += sorted(quiet_days, key=lambda d: d["date"])[: 14 - len(targets)]

high_days = sorted(days, key=lambda d: d["count"], reverse=True)[:3]
path_days = targets + high_days

commits_eaten = sum(d["count"] for d in targets)
total_contributions = sum(d["count"] for d in days)
best_day = max(days, key=lambda d: d["count"])

rects = []
target_dates = {d["date"] for d in targets}

for d in days:
    fill = d["color"] if d["count"] > 0 else "#161b22"
    opacity = "1" if d["count"] > 0 else "0.64"

    # No blue target rectangles, no stroke outlines.
    # Targets are marked only by a subtle fill opacity change, not a visible blue box.
    if d["date"] in target_dates:
        opacity = "1"

    rects.append(
        f'<rect x="{d["x"]}" y="{d["y"]}" width="10" height="10" rx="2" '
        f'fill="{fill}" opacity="{opacity}"/>'
    )

path_d = "M " + " L ".join([f'{d["x"] + 5} {d["y"] + 5}' for d in path_days])
target_dates_text = " • ".join([f'{d["date"]}({d["count"]})' for d in targets[:5]])

svg = f'''<svg width="980" height="340" viewBox="0 0 980 340" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#020617"/>
      <stop offset="55%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#0e4a7f"/>
    </linearGradient>

    <linearGradient id="eagleGold" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fde68a"/>
      <stop offset="50%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#92400e"/>
    </linearGradient>

    <filter id="softGlow">
      <feGaussianBlur stdDeviation="2.2" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <style>
      .title {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 28px;
        font-weight: 800;
        fill: #ffffff;
      }}

      .subtitle {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 13px;
        fill: #94a3b8;
      }}

      .metric {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 17px;
        font-weight: 800;
        fill: #38bdf8;
        text-anchor: middle;
      }}

      .label {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 11px;
        fill: #94a3b8;
        font-weight: 700;
        text-anchor: middle;
      }}

      .note {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 11px;
        fill: #64748b;
      }}
    </style>
  </defs>

  <rect width="980" height="340" rx="18" fill="url(#bgGradient)" stroke="#1e293b" stroke-width="1"/>

  <g opacity="0.08">
    <path d="M0 80 Q245 40 490 80 T980 80" fill="none" stroke="#38bdf8" stroke-width="2"/>
    <path d="M0 120 Q245 100 490 120 T980 120" fill="none" stroke="#38bdf8" stroke-width="1.5"/>
  </g>

  <text x="50" y="42" class="title">Contribution Eagle</text>
  <text x="50" y="62" class="subtitle">Flying through the lowest non-zero commit days first, then toward high-focus days.</text>

  <g id="gridGroup">
    {''.join(rects)}
  </g>

  <!-- Invisible route only. No bubbles, no target boxes, no dashed guide lines. -->
  <path id="flightPath" d="{path_d}" fill="none" stroke="none" stroke-width="0"/>

  <!-- Vector eagle points naturally to the right; rotate=auto makes direction accurate along the path. -->
  <g filter="url(#softGlow)">
    <g>
      <animateMotion dur="22s" repeatCount="indefinite" rotate="auto">
        <mpath href="#flightPath"/>
      </animateMotion>

      <!-- Eagle silhouette centered at 0,0 and facing right -->
      <g transform="scale(0.9)">
        <path d="M-30 -4 C-48 -20 -66 -18 -82 -8 C-61 -9 -47 -4 -35 5 Z" fill="#1f2937"/>
        <path d="M-28 4 C-46 22 -65 23 -82 13 C-60 13 -46 8 -34 -2 Z" fill="#111827"/>
        <path d="M-34 -4 C-15 -18 4 -14 19 -2 C2 -6 -13 -3 -30 8 Z" fill="#374151"/>
        <path d="M-32 5 C-12 19 8 16 22 3 C4 7 -12 5 -30 -8 Z" fill="#1f2937"/>
        <ellipse cx="-8" cy="0" rx="25" ry="11" fill="url(#eagleGold)"/>
        <path d="M12 -7 L34 0 L12 7 C18 2 18 -2 12 -7 Z" fill="#fbbf24"/>
        <circle cx="9" cy="-3" r="2" fill="#020617"/>
        <path d="M-9 10 L-17 22 M0 10 L-7 24" stroke="#f59e0b" stroke-width="3" stroke-linecap="round"/>
        <path d="M-18 22 L-25 20 M-7 24 L-14 26" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/>
      </g>
    </g>
  </g>

  <rect x="40" y="263" width="900" height="62" rx="12" fill="#0f172a" stroke="#1e293b" stroke-width="1" opacity="0.92"/>

  <text x="115" y="286" class="label">COMMITS EATEN</text>
  <text x="115" y="311" class="metric">{commits_eaten}</text>

  <text x="300" y="286" class="label">TARGET DAYS</text>
  <text x="300" y="311" class="metric">{len(targets)}</text>

  <text x="500" y="286" class="label">TOTAL CONTRIBUTIONS</text>
  <text x="500" y="311" class="metric">{total_contributions}</text>

  <text x="730" y="286" class="label">BEST DAY</text>
  <text x="730" y="311" class="metric">{best_day["count"]} commits</text>

  <text x="50" y="250" class="note">First targets: {target_dates_text}</text>
</svg>
'''

os.makedirs("dist", exist_ok=True)

with open("dist/github-contribution-eagle.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("✅ Generated dist/github-contribution-eagle.svg")
print(f"🦅 Commits eaten: {commits_eaten}")
print(f"🎯 Target days: {len(targets)}")
print(f"📊 Total contributions: {total_contributions}")
print(f"🏆 Best day: {best_day['date']} with {best_day['count']} commits")
