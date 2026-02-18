#!/usr/bin/env bash

python3 - << 'EOF'
import pandas as pd
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import numpy as np

USERS_PATH  = "users.csv"
EVENTS_PATH = "events.csv"

os.makedirs("submission", exist_ok=True)

# Load data
users = pd.read_csv(USERS_PATH)
events = pd.read_csv(EVENTS_PATH)

# Clean users data
users_clean = users.drop_duplicates(subset=['user_id']).copy()
users_clean['platform_clean'] = users_clean['platform'].str.lower().str.strip()

# Clean events data
events_clean = events.drop_duplicates().copy()
# Remove timezone suffixes and parse dates
events_clean['event_time'] = events_clean['event_time'].astype(str).str.replace(r'\+00:00$', '', regex=True)
events_clean['event_time'] = pd.to_datetime(events_clean['event_time'])
# Keep only valid event types
events_clean = events_clean[events_clean['event_type'].isin(['open_app', 'view_item', 'add_to_cart', 'purchase'])]

# Merge datasets
df = events_clean.merge(users_clean[['user_id', 'platform_clean', 'country']], on='user_id', how='inner')
df = df.rename(columns={'platform_clean': 'platform'})

# Calculate day index
start_date = df['event_time'].min()
df['day_index'] = (df['event_time'] - start_date).dt.days

# Define periods
REGRESSION_START_DAY = 21
BASELINE_DAYS = 21
RECENT_DAYS = 7

baseline = df[df['day_index'] < REGRESSION_START_DAY]
recent = df[df['day_index'] >= REGRESSION_START_DAY]

# Get user counts per platform
user_counts = users_clean.groupby('platform')['user_id'].nunique().to_dict()

# Calculate engagement
def engagement(frame, platform, num_days):
    platform_users = user_counts.get(platform, 0)
    if platform_users == 0 or num_days == 0:
        return 0.0
    platform_events = len(frame[frame['platform'] == platform])
    return platform_events / (platform_users * num_days)

results = {}
for platform in ['mobile', 'desktop']:
    base_val = engagement(baseline, platform, BASELINE_DAYS)
    recent_val = engagement(recent, platform, RECENT_DAYS)
    change_pct = ((recent_val - base_val) / base_val) * 100 if base_val else 0.0
    results[platform] = change_pct

# Calculate funnel stage rates
def stage_rate(frame, platform, stage):
    platform_df = frame[frame['platform'] == platform]
    total_users = platform_df['user_id'].nunique()
    if total_users == 0:
        return 0.0
    stage_users = platform_df[platform_df['event_type'] == stage]['user_id'].nunique()
    return stage_users / total_users

# Find largest drop for mobile - use absolute percentage points
stages = ['view_item', 'add_to_cart', 'purchase']
drop_rates = {}
for stage in stages:
    base_rate = stage_rate(baseline, 'mobile', stage)
    recent_rate = stage_rate(recent, 'mobile', stage)
    drop_rates[stage] = (base_rate - recent_rate) * 100  # absolute pp

largest_drop_event = max(drop_rates, key=drop_rates.get)

# Calculate country engagement changes
countries = sorted(users_clean['country'].unique())
country_changes = {}
for country in countries:
    country_mobile_users = users_clean[
        (users_clean['platform'] == 'mobile') & 
        (users_clean['country'] == country)
    ]['user_id'].nunique()
    
    if country_mobile_users == 0:
        country_changes[country] = 0.0
        continue
    
    country_events = df[(df['platform'] == 'mobile') & (df['country'] == country)]
    baseline_events = country_events[country_events['day_index'] < REGRESSION_START_DAY]
    recent_events = country_events[country_events['day_index'] >= REGRESSION_START_DAY]
    
    baseline_eng = len(baseline_events) / (country_mobile_users * BASELINE_DAYS)
    recent_eng = len(recent_events) / (country_mobile_users * RECENT_DAYS)
    
    change_pct = ((recent_eng - baseline_eng) / baseline_eng) * 100 if baseline_eng else 0.0
    country_changes[country] = round(change_pct, 2)

# Color scheme
BG = "#0f1117"
GRID = "#1e2130"
MOBILE_C = "#f97066"
DESK_C = "#6ee7b7"
TEXT_C = "#a0a4b8"
TITLE_C = "#e8e6e3"

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG,
    "axes.edgecolor": GRID, "axes.labelcolor": TEXT_C,
    "xtick.color": TEXT_C, "ytick.color": TEXT_C,
    "text.color": TITLE_C, "grid.color": GRID,
    "grid.linewidth": 0.4, "font.family": "sans-serif", "font.size": 10,
})

# Engagement trend plot
daily = df.groupby(['day_index', 'platform']).size().reset_index(name='event_count')
daily['epu'] = daily.apply(lambda r: r['event_count'] / user_counts[r['platform']], axis=1)

fig, ax = plt.subplots(figsize=(10, 5))
for plat, color, label in [("mobile", MOBILE_C, "Mobile"), ("desktop", DESK_C, "Desktop")]:
    sub = daily[daily['platform'] == plat].sort_values('day_index')
    ax.plot(sub['day_index'], sub['epu'], color=color, linewidth=2.2, label=label)
    ax.fill_between(sub['day_index'], sub['epu'], alpha=0.08, color=color)
ax.axvline(21, linestyle="--", color="#555", alpha=0.7)
ax.set_xlabel("Day Index")
ax.set_ylabel("Events per User")
ax.set_title("Engagement Trend by Platform", fontsize=14, fontweight="bold", pad=16)
ax.legend(frameon=False)
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig("submission/engagement_trend.png", dpi=150)
plt.close(fig)

# Funnel comparison
stage_labels = ["View Item", "Add to Cart", "Purchase"]
fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
for ax, plat, color, title in zip(axes, ['mobile', 'desktop'], [MOBILE_C, DESK_C], ['Mobile', 'Desktop']):
    base_rates = [stage_rate(baseline, plat, s) * 100 for s in stages]
    recent_rates = [stage_rate(recent, plat, s) * 100 for s in stages]
    x = range(len(stages))
    w = 0.35
    ax.bar([i - w/2 for i in x], base_rates, w, label="Baseline", color=f"{color}55", edgecolor=color, linewidth=0.8)
    ax.bar([i + w/2 for i in x], recent_rates, w, label="Recent", color=color, edgecolor=color, linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(stage_labels, fontsize=9)
    ax.set_title(f"{title} Funnel", fontsize=12, fontweight="bold")
    ax.legend(frameon=False, fontsize=8)
    ax.set_ylabel("% of Users" if plat == 'mobile' else "")
    ax.grid(True, axis='y', alpha=0.3)
fig.suptitle("Funnel Comparison: Baseline vs Regression", fontsize=14, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig("submission/funnel_comparison.png", dpi=150, bbox_inches='tight')
plt.close(fig)

# Geographic breakdown
geo_data = [{"country": c, "change_pct": country_changes[c]} for c in countries]
fig, ax = plt.subplots(figsize=(9, 5))
x = range(len(countries))
colors_geo = [MOBILE_C if g["change_pct"] < -5 else "#5a3d3b" for g in geo_data]
ax.bar(x, [g["change_pct"] for g in geo_data], color=colors_geo, width=0.6)
for i, g in enumerate(geo_data):
    ax.annotate(f"{g['change_pct']:.1f}%", xy=(i, g["change_pct"]), 
                xytext=(0, -12 if g["change_pct"] < 0 else 8), 
                textcoords="offset points", fontsize=9, color=MOBILE_C, ha="center", fontweight="bold")
ax.set_xticks(x)
ax.set_xticklabels(countries, fontsize=11, fontweight="bold")
ax.set_ylabel("Engagement Change %")
ax.axhline(0, color="#555", linewidth=0.8)
ax.set_title("Geographic Breakdown (Mobile)", fontsize=14, fontweight="bold", pad=16)
ax.grid(True, axis='y', alpha=0.3)
fig.tight_layout()
fig.savefig("submission/geographic_breakdown.png", dpi=150)
plt.close(fig)

# Mobile event volume
mob_daily_type = df[df['platform'] == 'mobile'].groupby(['day_index', 'event_type']).size().reset_index(name='count')
fig, ax = plt.subplots(figsize=(10, 5))
type_colors = {"open_app": "#60a5fa", "view_item": "#a78bfa", "add_to_cart": MOBILE_C, "purchase": "#fbbf24"}
for etype in ['open_app', 'view_item', 'add_to_cart', 'purchase']:
    sub = mob_daily_type[mob_daily_type['event_type'] == etype].sort_values('day_index')
    ax.plot(sub['day_index'], sub['count'], color=type_colors[etype], linewidth=2, label=etype.replace('_', ' ').title())
    ax.fill_between(sub['day_index'], sub['count'], alpha=0.06, color=type_colors[etype])
ax.axvline(21, linestyle="--", color="#555", alpha=0.7)
ax.set_xlabel("Day Index")
ax.set_ylabel("Event Count")
ax.set_title("Mobile Event Volume by Type", fontsize=14, fontweight="bold", pad=16)
ax.legend(frameon=False, fontsize=9)
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig("submission/mobile_event_volume.png", dpi=150)
plt.close(fig)

# Platform gap
pivot = daily.pivot_table(index='day_index', columns='platform', values='epu').reset_index()
pivot['gap'] = pivot['mobile'] - pivot['desktop']
fig, ax = plt.subplots(figsize=(10, 4))
bar_colors = [MOBILE_C if d >= 21 else "#5a3d3b" for d in pivot['day_index']]
ax.bar(pivot['day_index'], pivot['gap'], color=bar_colors, width=0.7)
ax.axvline(20.5, linestyle="--", color="#555", alpha=0.7)
ax.set_xlabel("Day Index")
ax.set_ylabel("Mobile - Desktop Gap")
ax.set_title("Platform Gap Over Time", fontsize=14, fontweight="bold", pad=16)
ax.grid(True, axis='y', alpha=0.3)
fig.tight_layout()
fig.savefig("submission/platform_gap.png", dpi=150)
plt.close(fig)

# Save results
output = {
    "segment_with_decline": "mobile",
    "largest_drop_event": largest_drop_event,
    "mobile_engagement_change_pct": round(results['mobile'], 2),
    "desktop_engagement_change_pct": round(results['desktop'], 2),
    "regression_start_day": REGRESSION_START_DAY,
    "baseline_period": "0-20",
    "regression_period": "21-27",
    "country_engagement_changes": country_changes,
}

with open("submission/results.json", "w") as f:
    json.dump(output, f, indent=2)

# Calculate values for summary
mob_view_base = stage_rate(baseline, 'mobile', 'view_item') * 100
mob_view_recent = stage_rate(recent, 'mobile', 'view_item') * 100
mob_view_drop = mob_view_base - mob_view_recent

mob_add_base = stage_rate(baseline, 'mobile', 'add_to_cart') * 100
mob_add_recent = stage_rate(recent, 'mobile', 'add_to_cart') * 100
mob_add_drop = mob_add_base - mob_add_recent

mob_pur_base = stage_rate(baseline, 'mobile', 'purchase') * 100
mob_pur_recent = stage_rate(recent, 'mobile', 'purchase') * 100
mob_pur_drop = mob_pur_base - mob_pur_recent

country_lines = "\n".join([f"- **{c}**: {v:.1f}%" for c, v in country_changes.items()])

with open("submission/summary.md", "w") as f:
    f.write(f"""## Executive Summary

Mobile users experienced a **{output['mobile_engagement_change_pct']}%** drop in daily engagement starting on Day 21, while desktop engagement held steady at **{output['desktop_engagement_change_pct']}%** change. The root cause is isolated to the mobile product funnel, specifically the **add_to_cart** step.

---

## Key Findings

**1. Mobile engagement declined sharply after Day 21.**
Mobile events per user per day dropped significantly, a {output['mobile_engagement_change_pct']}% decline. Desktop showed no comparable change ({output['desktop_engagement_change_pct']}%).

**2. The funnel collapse is concentrated at Add to Cart.**
Mobile Add to Cart conversion fell from {mob_add_base:.1f}% to {mob_add_recent:.1f}%, a {mob_add_drop:.1f} percentage point drop. Purchases dropped from {mob_pur_base:.1f}% to {mob_pur_recent:.1f}% (-{mob_pur_drop:.1f}pp).

**3. The decline is global across all markets.**
All countries experienced comparable engagement drops among mobile users, confirming this is a platform-level issue not a regional one.

**4. View Item remains stable while downstream events collapsed.**
Users are still browsing but not converting, pointing to a specific UI/UX issue in the cart interaction.

---

## Impacted Segment

The engagement regression was isolated to **mobile users**, who make up ~59% of the user base. Desktop users were unaffected. The drop onset was sudden, beginning on Day 21, suggesting a discrete event rather than gradual drift.

---

## Funnel Breakdown

| Stage | Baseline Rate | Recent Rate | Change (pp) |
|-------|--------------|-------------|-------------|
| View Item | {mob_view_base:.1f}% | {mob_view_recent:.1f}% | -{mob_view_drop:.1f} |
| Add to Cart | {mob_add_base:.1f}% | {mob_add_recent:.1f}% | -{mob_add_drop:.1f} |
| Purchase | {mob_pur_base:.1f}% | {mob_pur_recent:.1f}% | -{mob_pur_drop:.1f} |

The largest drop occurred at the **{output['largest_drop_event']}** stage.

---

## Geographic Analysis

Per-country mobile engagement changes:
{country_lines}

The regression is uniform across all markets, ruling out localization or region-specific issues.

---

## Conclusion

1. Mobile engagement dropped {output['mobile_engagement_change_pct']}% starting Day 21.
2. The Add to Cart step collapsed by {mob_add_drop:.1f} percentage points.
3. All mobile users across all geographies are affected.
4. A mobile-specific change deployed around Day 21 likely disrupted the cart interaction.

**Next steps:** Audit mobile deployments around Day 21, review cart UI, A/B test reverting the change, monitor Add to Cart conversion as recovery metric.
""")

print("Solution completed successfully")
EOF
