import os
import json
import random
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import sys
from matplotlib.widgets import Button  # <-- Correct import for widgets

# Allow directory to be specified as a command-line argument
if len(sys.argv) > 1:
    HIST_DIR = sys.argv[1]
else:
    HIST_DIR = "market_histories"

N = 100
files = [f for f in os.listdir(HIST_DIR) if f.endswith('.json')]
if not files:
    print("No market history files found.")
    exit(1)

total_blocks = (len(files) + N - 1) // N
current_block = [0]  # Use list for mutability in closures

fig, ax = plt.subplots(figsize=(12, 6))
plt.subplots_adjust(bottom=0.18)

plot_lines = []
scatter_dots = []

# Helper to clear old plot elements
def clear_plot():
    for line in plot_lines:
        line.remove()
    plot_lines.clear()
    for dot in scatter_dots:
        dot.remove()
    scatter_dots.clear()
    ax.cla()

def plot_block(block_idx, sorted_curves=None):
    clear_plot()
    if sorted_curves is not None:
        curves_with_price = sorted_curves
    else:
        start = block_idx * N
        end = min(start + N, len(files))
        chosen_files = files[start:end]
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
            ax.set_title("No valid market histories to plot.")
            fig.canvas.draw_idle()
            return
        # Pad each curve and its time on the left so all end at the right margin
        padded_curves = []
        padded_times = []
        for curve, times in zip(all_curves, all_times):
            pad_len = max_len - len(curve)
            padded_curve = np.pad(curve.astype(float), (pad_len, 0), mode='constant', constant_values=np.nan)
            padded_time = np.pad(times.astype(float), (pad_len, 0), mode='constant', constant_values=np.nan)
            padded_curves.append(padded_curve)
            padded_times.append(padded_time)
        curves_with_price = []
        for chosen_file, curve, times in zip(chosen_files, padded_curves, padded_times):
            valid_idx = np.where(~np.isnan(times))[0]
            if len(valid_idx) == 0:
                continue
            t_end = times[valid_idx[-1]]
            t_x = times[valid_idx] - t_end
            curve_valid = curve[valid_idx]
            day_idx = np.where(t_x >= -86400 * 7)[0]
            if len(day_idx) == 0:
                continue
            t_x_day = t_x[day_idx]
            curve_day = curve_valid[day_idx]
            end_price = curve_day[-1]
            curves_with_price.append((end_price, chosen_file, t_x_day, curve_day, times))
    for _, chosen_file, t_x_day, curve_day, times in curves_with_price:
        # Only plot the last 7 days before resolution
        day_idx = np.where(t_x_day >= -86400 * 7)[0]
        if len(day_idx) == 0:
            continue
        t_x_day_plot = t_x_day[day_idx]
        curve_day_plot = curve_day[day_idx]
        # Highlight in red if resolves on 1 but started below 0.5, or resolves on 0 but started above 0.5
        with open(os.path.join(HIST_DIR, chosen_file), 'r') as f:
            data = json.load(f)
        outcome = data.get("outcome")
        start_price = curve_day_plot[0]
        end_price = curve_day_plot[-1]
        highlight = False
        if outcome is not None:
            if str(outcome).lower() == 'yes' and start_price < 0.5 and end_price > 0.99:
                highlight = True
            elif str(outcome).lower() == 'no' and start_price > 0.5 and end_price < 0.01:
                highlight = True
        line_color = 'red' if highlight else 'black'
        line, = ax.plot(t_x_day_plot, curve_day_plot, color=line_color, linewidth=0.8, alpha=0.2)
        plot_lines.append(line)
        # Plot outcome dot if available
        if outcome is not None:
            color = 'green' if str(outcome).lower() == 'yes' else 'red'
            dot = ax.scatter([0], [curve_day_plot[-1]], color=color, s=40, zorder=10)
            scatter_dots.append(dot)
    ax.set_title(f"Price History for {len(curves_with_price)} Markets (block {block_idx+1}/{total_blocks}, last 7 days, end-aligned, x = T minus s)")
    ax.set_xlabel("T minus seconds (0 = end)")
    ax.set_ylabel("Price")
    ax.set_xlim([-86400*7, 0])
    ax.set_ylim([0, 1])
    fig.canvas.draw_idle()

# Precompute and sort all curves by final price before paging
all_files = files[:]
all_curves = []
all_times = []
max_len = 0
for chosen_file in all_files:
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
    ax.set_title("No valid market histories to plot.")
    fig.canvas.draw_idle()
    plt.show()
    exit(0)
# Pad each curve and its time on the left so all end at the right margin
padded_curves = []
padded_times = []
for curve, times in zip(all_curves, all_times):
    pad_len = max_len - len(curve)
    padded_curve = np.pad(curve.astype(float), (pad_len, 0), mode='constant', constant_values=np.nan)
    padded_time = np.pad(times.astype(float), (pad_len, 0), mode='constant', constant_values=np.nan)
    padded_curves.append(padded_curve)
    padded_times.append(padded_time)
curves_with_price = []
for chosen_file, curve, times in zip(all_files, padded_curves, padded_times):
    valid_idx = np.where(~np.isnan(times))[0]
    if len(valid_idx) == 0:
        continue
    t_end = times[valid_idx[-1]]
    t_x = times[valid_idx] - t_end
    curve_valid = curve[valid_idx]
    day_idx = np.where(t_x >= -86400 * 7)[0]
    if len(day_idx) == 0:
        continue
    t_x_day = t_x[day_idx]
    curve_day = curve_valid[day_idx]
    end_price = curve_day[-1]
    curves_with_price.append((end_price, chosen_file, t_x_day, curve_day, times))
# Sort by final price, descending
curves_with_price.sort(key=lambda x: -x[0])
# Now, for paging, use the sorted list
blocks = [curves_with_price[i:i+N] for i in range(0, len(curves_with_price), N)]
total_blocks = len(blocks)
current_block = [0]

def next_block(event):
    if current_block[0] < total_blocks - 1:
        current_block[0] += 1
        plot_block(current_block[0], sorted_curves=blocks[current_block[0]])

def prev_block(event):
    if current_block[0] > 0:
        current_block[0] -= 1
        plot_block(current_block[0], sorted_curves=blocks[current_block[0]])

# Add buttons
axprev = plt.axes([0.3, 0.05, 0.07, 0.045])
axnext = plt.axes([0.6, 0.05, 0.07, 0.045])
bprev = Button(axprev, 'Previous')
bnext = Button(axnext, 'Next')
bprev.on_clicked(prev_block)
bnext.on_clicked(next_block)

# Initial plot
plot_block(current_block[0], sorted_curves=blocks[current_block[0]])

# Compute and print ratios for No/Yes that ended high
num_yes = 0
num_yes_high = 0
num_no = 0
num_no_high = 0
for end_price, chosen_file, t_x_day, curve_day, times in curves_with_price:
    with open(os.path.join(HIST_DIR, chosen_file), 'r') as f:
        data = json.load(f)
    outcome = str(data.get("outcome")).lower()

    if abs(end_price - 0.5) < 0.3:
        continue
    
    if outcome == 'yes':
        num_yes += 1
        if end_price > 0.8:
            num_yes_high += 1
    elif outcome == 'no':
        num_no += 1
        if end_price > 0.8:
            num_no_high += 1
if num_yes > 0:
    print(f"Ratio of YES that ended high: {num_yes_high}/{num_yes} = {num_yes_high/num_yes:.3f}")
else:
    print("No YES outcomes found.")
if num_no > 0:
    print(f"Ratio of NO that ended high: {num_no_high}/{num_no} = {num_no_high/num_no:.3f}")
else:
    print("No NO outcomes found.")

plt.show()