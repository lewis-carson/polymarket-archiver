import os
import json
import random
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

HIST_DIR = "market_histories"

N = 100
files = [f for f in os.listdir(HIST_DIR) if f.endswith('.json')]
if not files:
    print("No market history files found.")
    exit(1)

chosen_files = random.sample(files, min(N, len(files)))
all_curves = []
all_times = []
max_len = 0

for chosen_file in chosen_files:
    with open(os.path.join(HIST_DIR, chosen_file), 'r') as f:
        data = json.load(f)
    history = data.get("history", [])
    if not history or len(history) < 2:
        continue
    ts = np.array([point["t"] for point in history])
    ps = np.array([point["p"] for point in history])
    all_curves.append(ps)
    all_times.append(ts)
    if len(ps) > max_len:
        max_len = len(ps)

if not all_curves:
    print("No valid market histories to plot.")
    exit(1)

# Pad each curve and its time on the left so all end at the right margin
padded_curves = []
padded_times = []
for curve, times in zip(all_curves, all_times):
    pad_len = max_len - len(curve)
    # Use float dtype to allow np.nan
    padded_curve = np.pad(curve.astype(float), (pad_len, 0), mode='constant', constant_values=np.nan)
    padded_time = np.pad(times.astype(float), (pad_len, 0), mode='constant', constant_values=np.nan)
    padded_curves.append(padded_curve)
    padded_times.append(padded_time)

plt.figure(figsize=(12, 6))
for curve, times in zip(padded_curves, padded_times):
    # Compute x axis as time to end in days (or hours if <2 days)
    valid = ~np.isnan(times)
    if not np.any(valid):
        continue
    t_end = times[valid][-1]
    t_x = (times[valid] - t_end) / 1000  # ms to seconds
    if abs(t_x[0]) > 2*24*3600:
        t_x = t_x / (24*3600)  # days
        x_label = "Days before end"
    else:
        t_x = t_x / 3600  # hours
        x_label = "Hours before end"
    plt.plot(t_x, curve[valid], alpha=0.5)
plt.title(f"Aligned Price History for {len(padded_curves)} Markets (end-aligned, x = time before end)")
plt.xlabel(x_label + " (0 = end)")
plt.ylabel("Price")
plt.tight_layout()
plt.show()