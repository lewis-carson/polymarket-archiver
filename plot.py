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
for chosen_file, curve, times in zip(chosen_files, padded_curves, padded_times):
    valid_idx = np.where(~np.isnan(times))[0]
    if len(valid_idx) == 0:
        continue
    t_end = times[valid_idx[-1]]
    t_x = times[valid_idx] - t_end  # normalise: T minus end
    curve_valid = curve[valid_idx]
    plt.plot(t_x, curve_valid, alpha=0.5)
    # Plot outcome dot if available
    with open(os.path.join(HIST_DIR, chosen_file), 'r') as f:
        data = json.load(f)
    outcome = data.get("outcome")
    if outcome is not None:
        color = 'green' if str(outcome).lower() == 'yes' else 'red'
        plt.scatter([0], [curve_valid[-1]], color=color, s=40, zorder=10)
plt.title(f"Aligned Price History for {len(padded_curves)} Markets (end-aligned, x = T minus ms)")
plt.xlabel("T minus ms (0 = end)")
plt.ylabel("Price")
plt.tight_layout()
plt.show()