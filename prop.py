import os
import json
import numpy as np
import pandas as pd

# Directory containing market history files
dir_path = "market_histories"

results = []
for fname in os.listdir(dir_path):
    if not fname.endswith('.json'):
        continue
    if 'vs' in fname.lower():
        continue  # Skip markets with 'vs' in the title
    with open(os.path.join(dir_path, fname), 'r') as f:
        data = json.load(f)
    history = data.get("history", [])
    if not history or len(history) < 2:
        continue
    ts = np.array([point["t"] for point in history])
    ps = np.array([point["p"] for point in history])
    t_end = ts[-1]
    # Find the price closest to 7 days (604800 seconds) before the end
    t_target = t_end - 604800  # timestamps are in seconds
    idx = np.searchsorted(ts, t_target, side='left')
    if idx == 0:
        price_week_out = ps[0]
    elif idx >= len(ts):
        price_week_out = ps[-1]
    else:
        # Interpolate between idx-1 and idx
        t0, t1 = ts[idx-1], ts[idx]
        p0, p1 = ps[idx-1], ps[idx]
        if t1 == t0:
            price_week_out = p0
        else:
            price_week_out = p0 + (p1 - p0) * (t_target - t0) / (t1 - t0)
    results.append({
        "file": fname,
        "price_week_out": float(price_week_out),
        "end_price": float(ps[-1]),
        "outcome": data.get("outcome")
    })

# Calculate payout as the difference between the price a week out and the end price
payout_sum = 0.0
count = 0
for r in results:
    price_week_out = r['price_week_out']
    end_price = r['end_price']
    payout = end_price - price_week_out
    payout_sum += payout
    count += 1
if count > 0:
    avg_payout = payout_sum / count
    print(f"\nIf you bought 1 unit of every market a week out and sold at the end:")
    print(f"  Total payout (sum of end - week-out): {payout_sum:.2f}")
    print(f"  Number of markets: {count}")
    print(f"  Average payout per market: {avg_payout:.4f}")
else:
    print("No markets found for payout calculation.")

# Calculate return if you bought everything > 0.8 a week out
payout_sum_08 = 0.0
count_08 = 0
for r in results:
    price_week_out = r['price_week_out']
    end_price = r['end_price']
    if price_week_out > 0.8:
        payout = end_price - price_week_out
        payout_sum_08 += payout
        count_08 += 1
if count_08 > 0:
    avg_payout_08 = payout_sum_08 / count_08
    print(f"\nIf you bought 1 unit of every market with price > 0.8 a week out and sold at the end:")
    print(f"  Total payout (sum of end - week-out): {payout_sum_08:.2f}")
    print(f"  Number of markets: {count_08}")
    print(f"  Average payout per market: {avg_payout_08:.4f}")
else:
    print("No markets with price > 0.8 a week out found for payout calculation.")

# Calculate return if you bought everything with outcome "Yes" a week out
payout_sum_yes = 0.0
count_yes = 0
for r in results:
    price_week_out = r['price_week_out']
    end_price = r['end_price']
    if r['outcome'] == "Yes":
        payout = end_price - price_week_out
        payout_sum_yes += payout
        count_yes += 1
if count_yes > 0:
    avg_payout_yes = payout_sum_yes / count_yes
    print(f"\nIf you bought 1 unit of every market with outcome 'Yes' a week out and sold at the end:")
    print(f"  Total payout (sum of end - week-out): {payout_sum_yes:.2f}")
    print(f"  Number of markets: {count_yes}")
    print(f"  Average payout per market: {avg_payout_yes:.4f}")
else:
    print("No markets with outcome 'Yes' found for payout calculation.")

# Calculate return for outcome "No" over different time horizons
horizons = [1/24, 1/4, 1/2, 1, 2, 3, 5, 7, 10, 14]  # days out
print("\nReturn for outcome 'No' over different time horizons:")
for days in horizons:
    payout_sum_no_h = 0.0
    count_no_h = 0
    seconds_out = days * 86400
    for r in results:
        fname = r['file']
        with open(os.path.join(dir_path, fname), 'r') as f:
            data = json.load(f)
        history = data.get("history", [])
        if not history or len(history) < 2:
            continue
        ts = np.array([point["t"] for point in history])
        ps = np.array([point["p"] for point in history])
        t_end = ts[-1]
        t_target = t_end - seconds_out
        idx = np.searchsorted(ts, t_target, side='left')
        if idx == 0:
            price_out = ps[0]
        elif idx >= len(ts):
            price_out = ps[-1]
        else:
            t0, t1 = ts[idx-1], ts[idx]
            p0, p1 = ps[idx-1], ps[idx]
            if t1 == t0:
                price_out = p0
            else:
                price_out = p0 + (p1 - p0) * (t_target - t0) / (t1 - t0)
        end_price = ps[-1]
        if data.get('outcome') == "No":
            payout = end_price - price_out
            payout_sum_no_h += payout
            count_no_h += 1
    if count_no_h > 0:
        avg_payout_no_h = payout_sum_no_h / count_no_h
        print(f"  {days} days out: total payout = {payout_sum_no_h:.2f}, N = {count_no_h}, avg per market = {avg_payout_no_h:.4f}")
    else:
        print(f"  {days} days out: No markets with outcome 'No' found.")
