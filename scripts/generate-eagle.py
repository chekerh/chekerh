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

# Lowest-commit days first, but avoid too many identical zero-only points.
targets = sorted(days, key=lambda d: (d["count"], d["date"]))[:16]

# Add a few stronger days at the end so the eagle "levels up".
high_days = sorted(days, key=lambda d: d["count"], reverse=True)[:5]
path_days = targets + high_days

points = " ".join([f"{d['x']},{d['y']}" for d in path_days])

messages = []
for d in path_days:
    if d["count"] == 0:
        label = f"{d['date']} · quiet day · {d['count']} commits"
    elif d["count"] <= 2:
        label = f"{d['date']} · low activity · {d['count']} commits"
    elif d["count"] <= 8:
        label = f"{d['date']} · building momentum · {d['count']} commits"
    else:
        label = f"{d['date']} · high-focus day · {d['count']} commits"
    messages.append(label)

message_values = "; ".join(messages)
message_key_times = "; ".join(
    [str(round(i / (len(messages) - 1), 3)) for i in range(len(messages))]
)

count_values = "; ".join([str(d["count"]) for d in path_days])
date_values = "; ".join([d["date"] for d in path_days])

rects = []
for d in days:
    fill = d["color"] if d["count"] > 0 else "#161b22"
    opacity = "1" if d["count"] > 0 else "0.75"
    rects.append(
        f'<rect x="{d["x"]}" y="{d["y"]}" width="10" height="10" rx="2" fill="{fill}" opacity="{opacity}"/>'
    )

target_rings = []
for d in path_days:
    target_rings.append(
        f'''
        <circle cx="{d["x"] + 5}" cy="{d["y"] + 5}" r="8" fill="none" stroke="#38bdf8" stroke-width="1.5" opacity="0.65">
          <animate attributeName="r" values="5;11;5" dur="2s" repeatCount="indefinite"/>
          <animate attributeName="opacity" values="0.2;0.9;0.2" dur="2s" repeatCount="indefinite"/>
        </circle>
        '''
    )

svg = f'''<svg width="920" height="320" viewBox="0 0 920 320" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="920" y2="320">
      <stop offset="0%" stop-color="#020617"/>
      <stop offset="60%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#0ea5e9"/>
    </linearGradient>

    <filter id="glow">
      <feGaussianBlur stdDeviation="3.5" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>

    <style>
      .title {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 26px;
        font-weight: 800;
        fill: #ffffff;
      }}

      .subtitle {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 14px;
        fill: #cbd5e1;
      }}

      .metric {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 18px;
        font-weight: 800;
        fill: #38bdf8;
      }}

      .small {{
        font-family: Arial, Helvetica, sans-serif;
        font-size: 12px;
        fill: #94a3b8;
      }}
    </style>
  </defs>

  <rect width="920" height="320" rx="26" fill="url(#bg)"/>

  <g opacity="0.22">
    <path d="M0 70 C160 20 280 120 450 70 C650 10 740 115 920 50" fill="none" stroke="#38bdf8" stroke-width="3"/>
    <path d="M0 105 C160 55 280 155 450 105 C650 45 740 150 920 85" fill="none" stroke="#ffffff" stroke-width="2"/>
  </g>

  <text x="38" y="42" class="title">Contribution Eagle</text>
  <text x="38" y="66" class="subtitle">Flying through the lowest-commit days first, then climbing toward high-focus days.</text>

  <g>
    {''.join(rects)}
  </g>

  <g>
    {''.join(target_rings)}
  </g>

  <polyline points="{points}" fill="none" stroke="#38bdf8" stroke-width="2" stroke-dasharray="6 8" opacity="0.6"/>

  <g filter="url(#glow)">
    <text font-size="30" x="0" y="0">🦅
      <animateMotion dur="18s" repeatCount="indefinite" rotate="auto">
        <mpath href="#flightPath"/>
      </animateMotion>
    </text>
  </g>

  <path id="flightPath" d="M {' L '.join([f'{d["x"] + 1} {d["y"] + 1}' for d in path_days])}" fill="none" stroke="transparent"/>

  <rect x="38" y="245" width="844" height="48" rx="14" fill="#020617" opacity="0.82" stroke="#38bdf8" stroke-opacity="0.35"/>

  <text x="62" y="268" class="subtitle">
    <animate attributeName="textContent"
      dur="18s"
      repeatCount="indefinite"
      values="{message_values}"
      keyTimes="{message_key_times}" />
  </text>

  <text x="62" y="288" class="small">Current target date:</text>
  <text x="178" y="288" class="metric">
    <animate attributeName="textContent"
      dur="18s"
      repeatCount="indefinite"
      values="{date_values}"
      keyTimes="{message_key_times}" />
  </text>

  <text x="650" y="288" class="small">Commits eaten:</text>
  <text x="770" y="288" class="metric">
    <animate attributeName="textContent"
      dur="18s"
      repeatCount="indefinite"
      values="{count_values}"
      keyTimes="{message_key_times}" />
  </text>
</svg>
'''

os.makedirs("dist", exist_ok=True)

with open("dist/github-contribution-eagle.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("Generated dist/github-contribution-eagle.svg")
