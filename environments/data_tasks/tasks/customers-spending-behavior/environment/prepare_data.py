"""
Generate synthetic customer spending data and install required dependencies.
Produces /repo/data/customer_spending.csv for the customers-spending-behavior task.
"""
import subprocess
import sys
import os

# Install extra deps not included in the base pip install
subprocess.run(
    [sys.executable, "-m", "pip", "install", "seaborn", "nbformat", "nbconvert", "ipykernel", "jupyter", "--quiet"],
    check=True,
)

import numpy as np
import pandas as pd

np.random.seed(42)

N = 3900

CATEGORIES = {
    "Clothing": ["Blouse", "Sweater", "Jeans", "T-shirt", "Jacket", "Dress", "Shorts", "Hoodie"],
    "Footwear": ["Sandals", "Sneakers", "Boots", "Loafers", "Heels"],
    "Outerwear": ["Coat", "Raincoat", "Windbreaker", "Parka"],
    "Accessories": ["Belt", "Scarf", "Hat", "Gloves", "Sunglasses", "Bag"],
}
ALL_CATEGORIES = list(CATEGORIES.keys())
CATEGORY_WEIGHTS = [0.45, 0.20, 0.15, 0.20]

GENDERS = ["Male", "Female"]
SIZES = ["S", "M", "L", "XL"]
COLORS = ["Gray", "Maroon", "Blue", "Black", "White", "Red", "Green", "Yellow", "Pink", "Purple"]
SEASONS = ["Winter", "Spring", "Summer", "Fall"]
SHIPPING = ["Express", "Free Shipping", "Next Day Air", "Standard", "Store Pickup", "2-Day Shipping"]
PAYMENT = ["Venmo", "Cash", "Credit Card", "PayPal", "Bank Transfer", "Debit Card"]
FREQUENCY = ["Weekly", "Bi-Weekly", "Fortnightly", "Monthly", "Quarterly", "Annually"]
SUBSCRIPTION = ["Yes", "No"]
DISCOUNT = ["Yes", "No"]
LOCATIONS = [
    "Kentucky", "Maine", "Massachusetts", "Rhode Island", "California", "Texas",
    "Florida", "New York", "Illinois", "Ohio", "Georgia", "North Carolina",
    "Michigan", "New Jersey", "Virginia", "Washington", "Arizona", "Tennessee",
    "Indiana", "Missouri",
]

categories = np.random.choice(ALL_CATEGORIES, size=N, p=CATEGORY_WEIGHTS)
items = [
    np.random.choice(CATEGORIES[cat]) for cat in categories
]

df = pd.DataFrame({
    "Customer ID": np.arange(1, N + 1),
    "Age": np.random.randint(18, 71, size=N),
    "Gender": np.random.choice(GENDERS, size=N),
    "Item Purchased": items,
    "Category": categories,
    "Purchase Amount (USD)": np.random.randint(20, 101, size=N),
    "Location": np.random.choice(LOCATIONS, size=N),
    "Size": np.random.choice(SIZES, size=N),
    "Color": np.random.choice(COLORS, size=N),
    "Season": np.random.choice(SEASONS, size=N),
    "Review Rating": np.round(np.random.uniform(2.5, 5.0, size=N), 1),
    "Subscription Status": np.random.choice(SUBSCRIPTION, size=N, p=[0.35, 0.65]),
    "Shipping Type": np.random.choice(SHIPPING, size=N),
    "Discount Applied": np.random.choice(DISCOUNT, size=N, p=[0.40, 0.60]),
    "Promo Code Used": np.random.choice(DISCOUNT, size=N, p=[0.35, 0.65]),
    "Previous Purchases": np.random.randint(0, 51, size=N),
    "Payment Method": np.random.choice(PAYMENT, size=N),
    "Frequency of Purchases": np.random.choice(FREQUENCY, size=N),
})

os.makedirs("/repo/data", exist_ok=True)
df.to_csv("/repo/data/customer_spending.csv", index=False)

print(f"Generated {len(df)} rows → /repo/data/customer_spending.csv")
print(f"Categories: {df['Category'].value_counts().to_dict()}")
print(f"Subscription split: {df['Subscription Status'].value_counts().to_dict()}")
