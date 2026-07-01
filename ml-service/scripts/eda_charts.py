"""
eda_charts.py
Day 2: Exploratory Data Analysis - generates 6 professional PNG charts
from the cleaned real US DOT flight delay dataset.

Charts produced (saved to data/charts/):
    1. delay_rate_distribution.png    - overall delay rate histogram
    2. delay_by_month.png             - seasonality: which months are worst
    3. delay_by_carrier.png           - which airlines run latest
    4. delay_causes_breakdown.png     - what causes delays (pie/bar)
    5. delay_trend_by_year.png        - has on-time performance improved?
    6. delay_rate_heatmap.png         - carrier vs month heatmap

Run from ml-service/ with venv activated:
    python eda_charts.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os
import warnings
warnings.filterwarnings("ignore")

CLEAN_PATH  = "data/flight_delay_clean.csv"
CHARTS_DIR  = "data/charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

NAVY        = "#1F3864"
BLUE        = "#2E75B6"
LIGHTBLUE   = "#9DC3E6"
ORANGE      = "#E67E22"
RED         = "#C0392B"
GREEN       = "#27AE60"
GREY        = "#7F8C8D"

plt.rcParams.update({
    "font.family":      "DejaVu Sans",
    "font.size":        11,
    "axes.titlesize":   14,
    "axes.titleweight": "bold",
    "axes.titlepad":    14,
    "axes.labelsize":   12,
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "figure.dpi":       150,
    "savefig.dpi":      150,
    "savefig.bbox":     "tight",
    "savefig.facecolor":"white",
})

MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]

def add_watermark(ax, text="US DOT/BTS Data 2013-2023"):
    ax.text(0.99, 0.01, text, transform=ax.transAxes,
            fontsize=8, color=GREY, ha="right", va="bottom", alpha=0.7)

def save(fig, name):
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")

print("Loading cleaned dataset...")
df = pd.read_csv(CLEAN_PATH)
print(f"  Rows: {len(df):,}  |  Carriers: {df['carrier'].nunique()}  |  Airports: {df['airport'].nunique()}")
print(f"  Years: {df['year'].min()}-{df['year'].max()}")
print(f"  Mean delay rate: {df['delay_rate'].mean():.2%}")
print("\nGenerating 6 EDA charts...")

# Chart 1: Distribution
print("\n[1/6] Delay rate distribution...")
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(df["delay_rate"], bins=60, color=BLUE, edgecolor="white", linewidth=0.4, alpha=0.9)
mean_val = df["delay_rate"].mean()
median_val = df["delay_rate"].median()
ax.axvline(mean_val,   color=ORANGE, linewidth=2, linestyle="--", label=f"Mean   {mean_val:.1%}")
ax.axvline(median_val, color=RED,    linewidth=2, linestyle=":",  label=f"Median {median_val:.1%}")
ax.set_title("Distribution of Flight Delay Rate\n(per Carrier-Airport-Month)")
ax.set_xlabel("Delay Rate  (fraction of flights delayed 15+ min)")
ax.set_ylabel("Number of Records")
ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
ax.legend()
add_watermark(ax)
save(fig, "delay_rate_distribution.png")

# Chart 2: By Month
print("[2/6] Delay rate by month...")
monthly = df.groupby("month")["delay_rate"].agg(["mean","std"]).reset_index()
monthly["month_label"] = [MONTH_LABELS[m-1] for m in monthly["month"]]
fig, ax = plt.subplots(figsize=(11, 5))
colors = [RED if m in [6,7,8,12] else BLUE for m in monthly["month"]]
bars = ax.bar(monthly["month_label"], monthly["mean"], color=colors, edgecolor="white", linewidth=0.4, zorder=3)
ax.errorbar(monthly["month_label"], monthly["mean"], yerr=monthly["std"],
            fmt="none", color=GREY, capsize=4, linewidth=1.2, zorder=4)
for bar, val in zip(bars, monthly["mean"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
            f"{val:.1%}", ha="center", va="bottom", fontsize=9, color=NAVY, fontweight="bold")
ax.set_title("Average Flight Delay Rate by Month\n(Red = summer/holiday peak months)")
ax.set_xlabel("Month")
ax.set_ylabel("Average Delay Rate")
ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
ax.set_ylim(0, monthly["mean"].max() * 1.20)
ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
add_watermark(ax)
save(fig, "delay_by_month.png")

# Chart 3: By Carrier
print("[3/6] Delay rate by carrier...")
carrier_stats = (df.groupby(["carrier","carrier_name"])["delay_rate"]
                   .agg(["mean","count"]).reset_index()
                   .sort_values("mean", ascending=True))
carrier_stats = carrier_stats[carrier_stats["count"] >= 100]
fig, ax = plt.subplots(figsize=(11, max(5, len(carrier_stats)*0.45)))
colors = [RED if v > carrier_stats["mean"].mean() else BLUE for v in carrier_stats["mean"]]
bars = ax.barh(carrier_stats["carrier_name"], carrier_stats["mean"],
               color=colors, edgecolor="white", linewidth=0.4)
for bar, val, cnt in zip(bars, carrier_stats["mean"], carrier_stats["count"]):
    ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height()/2,
            f"{val:.1%}  (n={cnt:,})", va="center", fontsize=9, color=NAVY)
overall_mean = df["delay_rate"].mean()
ax.axvline(overall_mean, color=ORANGE, linewidth=1.8, linestyle="--",
           label=f"Overall mean {overall_mean:.1%}")
ax.set_title("Average Delay Rate by Airline\n(Red = above average, Blue = below average)")
ax.set_xlabel("Average Delay Rate")
ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
ax.set_xlim(0, carrier_stats["mean"].max() * 1.35)
ax.legend(loc="lower right")
ax.grid(axis="x", linestyle="--", alpha=0.4)
add_watermark(ax)
save(fig, "delay_by_carrier.png")

# Chart 4: Causes Breakdown
print("[4/6] Delay causes breakdown...")
cause_cols   = ["carrier_ct_share","weather_ct_share","nas_ct_share",
                "security_ct_share","late_aircraft_ct_share"]
cause_labels = ["Carrier","Weather","NAS / ATC","Security","Late Aircraft"]
cause_colors = [BLUE, LIGHTBLUE, ORANGE, GREY, RED]
cause_means  = df[cause_cols].mean()
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
wedges, texts, autotexts = ax1.pie(cause_means, labels=cause_labels,
    colors=cause_colors, autopct="%1.1f%%", startangle=140, pctdistance=0.80,
    wedgeprops={"edgecolor":"white","linewidth":1.5})
for t in autotexts:
    t.set_fontsize(10)
    t.set_fontweight("bold")
ax1.set_title("Delay Cause Composition\n(average share per record)")
sorted_idx  = cause_means.argsort()[::-1]
sorted_vals = cause_means.iloc[sorted_idx]
sorted_labs = [cause_labels[i] for i in sorted_idx]
sorted_cols = [cause_colors[i] for i in sorted_idx]
bars = ax2.bar(sorted_labs, sorted_vals, color=sorted_cols, edgecolor="white", linewidth=0.5)
for bar, val in zip(bars, sorted_vals):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
             f"{val:.1%}", ha="center", fontsize=10, fontweight="bold")
ax2.set_title("Delay Cause Share - Ranked")
ax2.set_ylabel("Average Share of Total Delay Counts")
ax2.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
ax2.set_ylim(0, sorted_vals.max() * 1.25)
ax2.grid(axis="y", linestyle="--", alpha=0.4)
fig.suptitle("What Causes Flight Delays? (2013-2023)", fontsize=15, fontweight="bold", y=1.02)
add_watermark(ax2)
save(fig, "delay_causes_breakdown.png")

# Chart 5: Trend by Year
print("[5/6] Delay trend by year...")
yearly = df.groupby("year")["delay_rate"].agg(["mean","std","count"]).reset_index()
fig, ax = plt.subplots(figsize=(11, 5))
ax.fill_between(yearly["year"], yearly["mean"] - yearly["std"],
                yearly["mean"] + yearly["std"], alpha=0.15, color=BLUE, label="+-1 std dev")
ax.plot(yearly["year"], yearly["mean"], color=BLUE, linewidth=2.5,
        marker="o", markersize=7, markerfacecolor="white",
        markeredgecolor=BLUE, markeredgewidth=2, label="Mean delay rate", zorder=5)
covid_row = yearly[yearly["year"] == 2020]
if not covid_row.empty:
    val = covid_row["mean"].values[0]
    ax.annotate(f"COVID-19\n{val:.1%}", xy=(2020, val),
                xytext=(2020.3, val + 0.02), fontsize=9, color=GREY,
                arrowprops={"arrowstyle":"->","color":GREY})
for _, row in yearly.iterrows():
    ax.text(row["year"], row["mean"] + 0.008, f"{row['mean']:.1%}",
            ha="center", fontsize=8.5, color=NAVY, fontweight="bold")
ax.set_title("US Flight Delay Rate Trend: 2013-2023\n(Has on-time performance improved over time?)")
ax.set_xlabel("Year")
ax.set_ylabel("Average Delay Rate")
ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))
ax.set_xticks(yearly["year"])
ax.set_ylim(0, (yearly["mean"] + yearly["std"]).max() * 1.20)
ax.legend()
ax.grid(axis="y", linestyle="--", alpha=0.4)
add_watermark(ax)
save(fig, "delay_trend_by_year.png")

# Chart 6: Heatmap
print("[6/6] Carrier vs month heatmap...")
top_carriers = (df.groupby("carrier_name")["delay_rate"].count()
                  .nlargest(10).index.tolist())
heat_df = (df[df["carrier_name"].isin(top_carriers)]
             .groupby(["carrier_name","month"])["delay_rate"]
             .mean().unstack(level="month"))
heat_df.columns = [MONTH_LABELS[m-1] for m in heat_df.columns]
fig, ax = plt.subplots(figsize=(13, 6))
sns.heatmap(heat_df, annot=True, fmt=".1%", cmap="RdYlGn_r",
            linewidths=0.5, linecolor="white", ax=ax,
            annot_kws={"size": 8},
            cbar_kws={"label": "Delay Rate"})
ax.set_title("Delay Rate by Airline x Month\n(Top 10 Airlines by Data Volume - Red = more delays)", pad=14)
ax.set_xlabel("Month")
ax.set_ylabel("")
ax.tick_params(axis="y", rotation=0)
ax.tick_params(axis="x", rotation=0)
add_watermark(ax)
save(fig, "delay_rate_heatmap.png")

print("\nAll 6 charts saved to: data/charts/")
print("\nKey findings from your real data:")
print(f"  Overall delay rate: {df['delay_rate'].mean():.2%}")
print(f"  Worst month:  {MONTH_LABELS[df.groupby('month')['delay_rate'].mean().idxmax()-1]}")
print(f"  Best month:   {MONTH_LABELS[df.groupby('month')['delay_rate'].mean().idxmin()-1]}")
print(f"  Highest-delay carrier: {df.groupby('carrier_name')['delay_rate'].mean().idxmax()}")
print(f"  Lowest-delay carrier:  {df.groupby('carrier_name')['delay_rate'].mean().idxmin()}")
