"""
Generate synthetic e-commerce engagement data with real-world messiness.
"""
import numpy as np
import pandas as pd
import random
import string
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

NUM_USERS = 1000  # reduced from 10000 for faster evaluation (still ~48K events)
NUM_DAYS = 28
START_DATE = datetime(2023, 7, 1)

COUNTRIES = ["US", "IN", "UK", "DE", "CA", "AU"]
COUNTRY_WEIGHTS = [0.30, 0.25, 0.15, 0.12, 0.10, 0.08]
PLATFORMS = ["mobile", "desktop"]
PLATFORM_WEIGHTS = [0.59, 0.41]

BASE_PROBS = {
    "open_app": 0.85,
    "view_item": 0.75,
    "add_to_cart": 0.30,
    "purchase": 0.25,
}

CART_MULTIPLIER = 0.35

# Users
users = []
for i in range(NUM_USERS):
    uid = f"u_{i:05d}"
    platform = np.random.choice(PLATFORMS, p=PLATFORM_WEIGHTS)
    country = np.random.choice(COUNTRIES, p=COUNTRY_WEIGHTS)
    signup_date = START_DATE - timedelta(days=np.random.randint(30, 365))
    age_bucket = np.random.choice(["18-24", "25-34", "35-44", "45-54", "55+", None],
                                   p=[0.15, 0.30, 0.25, 0.15, 0.10, 0.05])
    referral_source = np.random.choice(["organic", "paid", "social", "email", "direct", ""],
                                        p=[0.25, 0.20, 0.20, 0.15, 0.15, 0.05])
    plan_type = np.random.choice(["free", "basic", "premium", None],
                                  p=[0.50, 0.25, 0.15, 0.10])

    users.append({
        "user_id": uid,
        "platform": platform,
        "country": country,
        "signup_date": signup_date.strftime("%Y-%m-%d"),
        "age_bucket": age_bucket,
        "referral_source": referral_source,
        "plan_type": plan_type,
    })

users_df = pd.DataFrame(users)

# Inject messiness in users
dup_idx = np.random.choice(len(users_df), size=int(len(users_df) * 0.005), replace=False)
users_df = pd.concat([users_df, users_df.iloc[dup_idx]], ignore_index=True)

mess_idx = np.random.choice(len(users_df), size=50, replace=False)
for idx in mess_idx:
    if users_df.at[idx, "platform"] == "mobile":
        users_df.at[idx, "platform"] = np.random.choice(["Mobile", "MOBILE", "mobile "])
    else:
        users_df.at[idx, "platform"] = np.random.choice(["Desktop", "DESKTOP", "desktop "])

# Events
events = []
clean_users = pd.DataFrame(users[:NUM_USERS])

for day in range(NUM_DAYS):
    date = START_DATE + timedelta(days=day)

    for _, user in clean_users.iterrows():
        uid = user["user_id"]
        platform = user["platform"]
        country = user["country"]

        if np.random.random() > BASE_PROBS["open_app"]:
            continue

        hour = int(np.random.normal(14, 4))
        hour = max(0, min(23, hour))
        minute = np.random.randint(0, 60)
        second = np.random.randint(0, 60)
        ts = date + timedelta(hours=hour, minutes=minute, seconds=second)

        events.append({
            "user_id": uid,
            "event_type": "open_app",
            "event_time": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "session_id": f"s_{''.join(random.choices(string.ascii_lowercase, k=8))}",
            "device_model": np.random.choice(["iPhone14", "iPhone15", "Pixel7", "Galaxy S23",
                                               "iPad Pro", "MacBook", "ThinkPad", "Surface", ""]),
        })

        if np.random.random() < BASE_PROBS["view_item"]:
            ts2 = ts + timedelta(seconds=np.random.randint(10, 300))
            events.append({
                "user_id": uid,
                "event_type": "view_item",
                "event_time": ts2.strftime("%Y-%m-%d %H:%M:%S"),
                "session_id": events[-1]["session_id"],
                "device_model": events[-1]["device_model"],
            })

            cart_prob = BASE_PROBS["add_to_cart"]
            if platform == "mobile" and day >= 21:
                cart_prob *= CART_MULTIPLIER

            if np.random.random() < cart_prob:
                ts3 = ts2 + timedelta(seconds=np.random.randint(10, 600))
                events.append({
                    "user_id": uid,
                    "event_type": "add_to_cart",
                    "event_time": ts3.strftime("%Y-%m-%d %H:%M:%S"),
                    "session_id": events[-1]["session_id"],
                    "device_model": events[-1]["device_model"],
                })

                if np.random.random() < BASE_PROBS["purchase"]:
                    ts4 = ts3 + timedelta(seconds=np.random.randint(30, 900))
                    events.append({
                        "user_id": uid,
                        "event_type": "purchase",
                        "event_time": ts4.strftime("%Y-%m-%d %H:%M:%S"),
                        "session_id": events[-1]["session_id"],
                        "device_model": events[-1]["device_model"],
                    })

events_df = pd.DataFrame(events)

# Inject messiness in events
dup_idx = np.random.choice(len(events_df), size=int(len(events_df) * 0.003), replace=False)
events_df = pd.concat([events_df, events_df.iloc[dup_idx]], ignore_index=True)

tz_idx = np.random.choice(len(events_df), size=200, replace=False)
for idx in tz_idx:
    events_df.at[idx, "event_time"] = events_df.at[idx, "event_time"] + "+00:00"

null_idx = np.random.choice(len(events_df), size=int(len(events_df) * 0.002), replace=False)
for idx in null_idx:
    events_df.at[idx, "event_type"] = ""

junk_idx = np.random.choice(len(events_df), size=100, replace=False)
for idx in junk_idx:
    events_df.at[idx, "event_type"] = np.random.choice(["page_load", "error", "heartbeat"])

for _ in range(50):
    events_df = pd.concat([events_df, pd.DataFrame([{
        "user_id": f"u_{99999}",
        "event_type": "open_app",
        "event_time": "2023-07-15 12:00:00",
        "session_id": "s_orphan",
        "device_model": "",
    }])], ignore_index=True)

events_df = events_df.sample(frac=1, random_state=42).reset_index(drop=True)
users_df = users_df.sample(frac=1, random_state=42).reset_index(drop=True)

users_df.to_csv("users.csv", index=False)
events_df.to_csv("events.csv", index=False)

print(f"Generated {len(users_df)} users, {len(events_df)} events")
print(f"Platforms: {users_df['platform'].value_counts().to_dict()}")
print(f"Countries: {users_df['country'].value_counts().to_dict()}")
print(f"Event types: {events_df['event_type'].value_counts().to_dict()}")