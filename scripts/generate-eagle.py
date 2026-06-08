import os
import json
import urllib.request
from datetime import date, timedelta

USERNAME = os.environ.get("GITHUB_USERNAME", "chekerh")
TOKEN = os.environ["GITHUB_TOKEN"]

today = date.today()
start = today - timedelta(days=365)

query = """
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
"""

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

weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

days = []
for week_index, week in enumerate(weeks):
    for day_index, day in enumerate(week["contributionDays"]):
        days.append({
            "date": day["date"],
            "count": day["contributionCount"],
            "color": day["color"],
            "x": 55 + week_index * 14,
            "y": 85 + day_index * 14,
        })

# Get lowest-commit days (targets to eat)
targets = sorted(days, key=lambda d: (d["count"], d["date"]))[:12]

# Add a few high-activity days for celebration
high_days = sorted(days, key=lambda d: d["count"], reverse=True)[:4]
path_days = targets + high_days

rects = []
for d in days:
    fill = d["color"] if d["count"] > 0 else "#161b22"
    opacity = "1" if d["count"] > 0 else "0.75"
    rects.append(
        f'<rect x="{d["x"]}" y="{d["y"]}" width="10" height="10" rx="2" fill="{fill}" opacity="{opacity}"/>'
    )

# SVG with professional design - NO BUBBLES/CIRCLES
svg = f'''<svg width="980" height="340" viewBox="0 0 980 340" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#020617;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#0f172a;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#0e4a7f;stop-opacity:1" />
    </linearGradient>

    <filter id="glow">
      <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
      
      .title {{
        font-family: 'Inter', Arial, sans-serif;
        font-size: 28px;
        font-weight: 800;
        fill: #ffffff;
        letter-spacing: -0.5px;
      }}

      .subtitle {{
        font-family: 'Inter', Arial, sans-serif;
        font-size: 13px;
        fill: #94a3b8;
        font-weight: 500;
        letter-spacing: 0.3px;
      }}

      .metric {{
        font-family: 'Inter', Arial, sans-serif;
        font-size: 16px;
        font-weight: 700;
        fill: #38bdf8;
        text-anchor: middle;
      }}

      .label {{
        font-family: 'Inter', Arial, sans-serif;
        font-size: 11px;
        fill: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
      }}
    </style>
  </defs>

  <!-- Background -->
  <rect width="980" height="340" rx="18" fill="url(#bgGradient)" stroke="#1e293b" stroke-width="1"/>

  <!-- Decorative waves -->
  <g opacity="0.08">
    <path d="M0 80 Q245 40 490 80 T980 80" fill="none" stroke="#38bdf8" stroke-width="2"/>
    <path d="M0 120 Q245 100 490 120 T980 120" fill="none" stroke="#38bdf8" stroke-width="1.5"/>
  </g>

  <!-- Header -->
  <text x="50" y="42" class="title">🦅 Contribution Eagle</text>
  <text x="50" y="62" class="subtitle">Flying through your contribution calendar, hunting low-activity days</text>

  <!-- Contribution grid -->
  <g id="gridGroup">
    {''.join(rects)}
  </g>

  <!-- Flight path (dashed line) -->
  <polyline points="{' '.join([f'{d["x"] + 5},{d["y"] + 5}' for d in path_days])}" 
    fill="none" stroke="#38bdf8" stroke-width="2" stroke-dasharray="4 6" opacity="0.5"/>

  <!-- Eagle animation (moving along path with transformations) -->
  <g id="eagleGroup" filter="url(#glow)">
    <text x="55" y="90" font-size="32" fill="#ffffff" text-anchor="middle">🦅</text>
    <animateMotion dur="18s" repeatCount="indefinite" keyPoints="0;1" keyTimes="0;1">
      <mpath href="#flightPath"/>
    </animateMotion>
  </g>

  <path id="flightPath" d="M {' L '.join([f'{d["x"] + 5} {d["y"] + 5}' for d in path_days])}" 
    fill="none" stroke="transparent" stroke-width="1"/>

  <!-- Stats panel -->
  <rect x="40" y="265" width="900" height="60" rx="12" fill="#0f172a" stroke="#1e293b" stroke-width="1" opacity="0.9"/>

  <!-- Stats labels and values -->
  <text x="90" y="285" class="label">Target Days</text>
  <text x="90" y="310" class="metric">{len(path_days)}</text>

  <text x="280" y="285" class="label">Status</text>
  <text x="280" y="310" class="metric">Active Hunt</text>

  <text x="500" y="285" class="label">Total Contributions</text>
  <text x="500" y="310" class="metric">{sum(d["count"] for d in days)}</text>

  <text x="750" y="285" class="label">Best Day</text>
  <text x="750" y="310" class="metric">{max(d["count"] for d in days)} commits</text>
</svg>
'''

os.makedirs("dist", exist_ok=True)

with open("dist/github-contribution-eagle.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("✅ Generated dist/github-contribution-eagle.svg")
print(f"📊 Stats: {len(path_days)} target days, {sum(d['count'] for d in days)} total commits")
