import os
import json
import urllib.request
from datetime import date, timedelta
import math

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

# Get lowest-commit days FIRST (eagle eats these)
targets = sorted(days, key=lambda d: (d["count"], d["date"]))[:14]

# Calculate total commits from target days (commits eaten)
commits_eaten = sum(d["count"] for d in targets)

# High-activity days as final victories
high_days = sorted(days, key=lambda d: d["count"], reverse=True)[:3]
path_days = targets + high_days

rects = []
for d in days:
    fill = d["color"] if d["count"] > 0 else "#161b22"
    opacity = "1" if d["count"] > 0 else "0.75"
    rects.append(
        f'<rect x="{d["x"]}" y="{d["y"]}" width="10" height="10" rx="2" fill="{fill}" opacity="{opacity}"/>'
    )

# Calculate direction angles for each segment of the path
def get_eagle_rotation(p1, p2):
    """Calculate angle between two points for proper eagle rotation"""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle = math.degrees(math.atan2(dy, dx))
    return angle

# Generate SVG data for directional eagles (8-point compass)
def get_eagle_by_angle(angle):
    """Return eagle rotation transform based on angle"""
    # Normalize angle to 0-360
    angle = angle % 360
    # 8-directional rotations: right, top-right, top, top-left, left, bottom-left, bottom, bottom-right
    directions = {
        "right": (0, "🦅"),
        "top_right": (45, "🦅"),
        "top": (90, "🦅"),
        "top_left": (135, "🦅"),
        "left": (180, "🦅"),
        "bottom_left": (225, "🦅"),
        "bottom": (270, "🦅"),
        "bottom_right": (315, "🦅"),
    }
    return angle

# Create motion path for smooth animation - NO VISIBLE LINE
path_points = " ".join([f"{d['x'] + 5},{d['y'] + 5}" for d in path_days])

# SVG with CLEAN DESIGN: no bubbles, no direction lines, proper 8-direction eagle animation
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
  <text x="50" y="62" class="subtitle">Hunting low-activity days • Adaptive directional flight • Full ecosystem tracking</text>

  <!-- Contribution grid -->
  <g id="gridGroup">
    {''.join(rects)}
  </g>

  <!-- INVISIBLE flight path - NO VISIBLE LINES, NO BUBBLES -->
  <path id="flightPath" d="M {path_points}" fill="none" stroke="transparent" stroke-width="0"/>

  <!-- Eagle animation with 8-directional support and proper rotation -->
  <g id="eagleContainer" filter="url(#glow)">
    <g id="eagleMoving">
      <text x="0" y="0" font-size="36" fill="#ffffff" text-anchor="middle" dy="0.3em" 
            style="transform-origin: center center; will-change: transform;">🦅
        <animateMotion dur="24s" repeatCount="indefinite" rotate="auto" keyPoints="0;1" keyTimes="0;1">
          <mpath href="#flightPath"/>
        </animateMotion>
        <!-- Adaptive rotation for 8-directional movement -->
        <animateTransform 
          attributeName="transform" 
          type="rotate"
          dur="24s" 
          repeatCount="indefinite"
          keyPoints="0;0.125;0.25;0.375;0.5;0.625;0.75;0.875;1"
          keyTimes="0;0.125;0.25;0.375;0.5;0.625;0.75;0.875;1"
          values="0 0 0;45 0 0;90 0 0;135 0 0;180 0 0;225 0 0;270 0 0;315 0 0;360 0 0"
        />
      </text>
    </g>
  </g>

  <!-- Stats panel -->
  <rect x="40" y="265" width="900" height="60" rx="12" fill="#0f172a" stroke="#1e293b" stroke-width="1" opacity="0.9"/>

  <!-- Stats with FIXED TEXT VALUES -->
  <g>
    <!-- Commits Eaten -->
    <text x="100" y="285" class="label">Commits Eaten</text>
    <text x="100" y="310" class="metric">{commits_eaten}</text>

    <!-- Target Days -->
    <text x="280" y="285" class="label">Target Days</text>
    <text x="280" y="310" class="metric">{len(targets)}</text>

    <!-- Total Contributions -->
    <text x="480" y="285" class="label">Total Contributions</text>
    <text x="480" y="310" class="metric">{sum(d["count"] for d in days)}</text>

    <!-- Hunt Status -->
    <text x="750" y="285" class="label">Hunt Status</text>
    <text x="750" y="310" class="metric">Active</text>
  </g>
</svg>
'''

os.makedirs("dist", exist_ok=True)

with open("dist/github-contribution-eagle.svg", "w", encoding="utf-8") as f:
    f.write(svg)

print("✅ Generated dist/github-contribution-eagle.svg")
print(f"🦅 Eagle Statistics:")
print(f"   • Commits Eaten: {commits_eaten}")
print(f"   • Target Days: {len(targets)}")
print(f"   • Total Contributions: {sum(d['count'] for d in days)}")
print(f"   • Path: {len(path_days)} waypoints")
print(f"   • Animation: 8-directional adaptive rotation")
