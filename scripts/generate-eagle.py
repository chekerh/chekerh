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

targets = sorted(days, key=lambda d: (d["count"], d["date"]))[:14]
high_days = sorted(days, key=lambda d: d["count"], reverse=True)[:3]
path_days = targets + high_days

commits_eaten = sum(d["count"] for d in targets)
total_contributions = sum(d["count"] for d in days)
best_day = max(days, key=lambda d: d["count"])

rects = []
target_dates = {d["date"] for d in targets}

for d in days:
    fill = d["color"] if d["count"] > 0 else "#161b22"
    opacity = "1" if d["count"] > 0 else "0.70"
    stroke = "#38bdf8" if d["date"] in target_dates else "none"
    stroke_width = "0.9" if d["date"] in target_dates else "0"
    rects.append(
        f'<rect x="{d["x"]}" y="{d["y"]}" width="10" height="10" rx="2" '
        f'fill="{fill}" opacity="{opacity}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
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
  <text x="50" y="62" class="subtitle">Hunting the lowest-commit days first, then flying toward high-focus days.</text>

  <g id="gridGroup">
    {''.join(rects)}
  </g>

  <!-- Invisible route only. No bubbles, no dashed guide lines. -->
  <path id="flightPath" d="{path_d}" fill="none" stroke="none" stroke-width="0"/>

  <g filter="url(#softGlow)">
    <text font-size="34" text-anchor="middle" dominant-baseline="middle">🦅
      <animateMotion dur="22s" repeatCount="indefinite" rotate="auto">
        <mpath href="#flightPath"/>
      </animateMotion>
    </text>
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
