"""Cover and social cards for the fan-out article, styled to my Medium cards.

Same design as my MoJ Crown Court series (cream ground, serif title in navy
then red italic, three stat cards with coloured rules, pull-quote, byline):
a landscape cover for Medium's featured image and a square for social posts.
Every number is read from the Gold CSVs that notebook 03 writes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import GOLD_DIR  # noqa: E402

CREAM = "#F4F1E9"; INK = "#13273A"; RED = "#D12E26"; ROYAL = "#1D4ED8"; STEEL = "#2E5F8A"
ORANGE = "#E08A1E"; MUTED = "#8A94A0"; LABEL = "#9AA1AC"; WHITE = "#FFFFFF"; PINK = "#F7E7E4"
WATERMARK = "#ECE7DB"
SERIF, MONO, SANS = "DejaVu Serif", "DejaVu Sans Mono", "DejaVu Sans"
OUT = GOLD_DIR / "02_charts"


def figures() -> dict:
    """The three card numbers, from notebook 03's outputs."""
    con = pd.read_csv(GOLD_DIR / "01_fan_out" / "contrast.csv").set_index("lookup")
    rank = pd.read_csv(GOLD_DIR / "01_fan_out" / "rank_change.csv")
    main = con.index[1]
    inflation = con.loc[main, "inflation"]
    rate_move = abs(con.loc[main, "england_pct_over_18"] - con.iloc[0].england_pct_over_18)
    return {"inflation": f"×{inflation:.2f}",
            "rate_move": f"{rate_move:.2f} pts",
            "rank": f"{int((rank.rank_change != 0).sum())} of {len(rank)}"}


def rrect(ax, x, y, w, h, fc, rad=0.6, z=1):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rad}",
                                fc=fc, ec="none", lw=0, zorder=z, mutation_aspect=0.55))


def build(square: bool = False) -> Path:
    f = figures()
    if square:
        fig = plt.figure(figsize=(9, 9), dpi=140); W, H = 100, 100
    else:
        fig = plt.figure(figsize=(12, 6.3), dpi=150); W, H = 100, 52.5
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_xlim(0, W); ax.set_ylim(0, H)
    ax.add_patch(Rectangle((0, 0), W, H, fc=CREAM, zorder=0))
    top = H - 6

    # Watermark: the inflation factor, faint, in the open space between the
    # title and the cards. The landscape has no open space it wouldn't crowd,
    # so it goes without.
    if square:
        ax.text(W - 4, 56, f["inflation"], fontsize=62, fontweight="bold", color=WATERMARK,
                ha="right", va="bottom", family=SERIF, zorder=0.5)

    # Kicker
    ax.text(6, top, "NHS DATA ENGINEERING", fontsize=12, color=ROYAL, family=MONO, fontweight="bold", va="center")
    ax.text(6 + (30 if square else 22.5), top, "· MEDIUM · NOVEMBER 2026", fontsize=12, color=MUTED,
            family=MONO, va="center")
    ax.add_patch(Rectangle((6, top - 3.2), 7, 0.5, fc=RED, zorder=2))

    # Title
    ty = top - 9
    tfs = 40 if square else 33
    ax.text(6, ty, "The Join You", fontsize=tfs, color=INK, family=SERIF, fontweight="bold", va="top")
    ax.text(6, ty - (11 if square else 8.5), "Never Documented.", fontsize=tfs, color=RED,
            family=SERIF, fontweight="bold", style="italic", va="top")

    # Stat cards
    if square:
        cx, cw, ys, ch, num_fs, lab_fs, lab_x = 6, 88, [42, 28, 14], 12, 26, 11, 0.42
    else:
        cx, cw, ys, ch, num_fs, lab_fs, lab_x = 54, 42, [34, 20, 6], 12, 24, 10.5, 0.47
    stats = [(f["inflation"], RED, "DENOMINATOR INFLATED", "NO ERROR RAISED"),
             (f["rate_move"], STEEL, "ENGLAND RATE MOVED", "STILL LOOKS RIGHT"),
             (f["rank"], ORANGE, "SPECIALTIES CHANGE", "LEAGUE-TABLE RANK")]
    for (num, col, l1, l2), cy in zip(stats, ys):
        rrect(ax, cx, cy, cw, ch, WHITE, rad=0.7, z=2)
        ax.add_patch(Rectangle((cx + 0.8, cy + ch - 0.55), cw - 1.6, 0.55, fc=col, zorder=3))
        ax.text(cx + 3, cy + ch / 2, num, fontsize=num_fs, color=col, family=SERIF, fontweight="bold",
                va="center", zorder=4)
        ax.text(cx + cw * lab_x, cy + ch / 2, f"{l1}\n{l2}", fontsize=lab_fs, color=LABEL, family=SANS,
                fontweight="bold", va="center", linespacing=1.4, zorder=4)

    # Pull-quote
    if square:
        qx, qy, qw, qh = 6, 2.5, 88, 9
    else:
        qx, qy, qw, qh = 6, 8, 44, 12.5
    rrect(ax, qx, qy, qw, qh, PINK, rad=0.6, z=1)
    ax.add_patch(Rectangle((qx, qy), 0.7, qh, fc=RED, zorder=3))
    ax.text(qx + 3, qy + qh * 0.64, "Same file. Same measure. No error.", fontsize=12.5,
            color=INK, style="italic", family=SERIF, va="center", zorder=4)
    ax.text(qx + 3, qy + qh * 0.30, "Two answers that both look right.", fontsize=13,
            color=RED, fontweight="bold", family=SERIF, va="center", zorder=4)

    # Footer
    if not square:
        ax.text(6, 2.6, "Yusuf Ismail", fontsize=12, color=INK, fontweight="bold", family=SANS, va="bottom")
        ax.text(6, 1.2, "medium.com/@yusufismail_91982", fontsize=9.5, color=ROYAL, family=MONO, va="bottom")
        rrect(ax, 84, 1.2, 12, 3.2, INK, rad=0.5, z=3)
        ax.text(90, 2.8, "READ ON MEDIUM →", fontsize=8.5, color=WHITE, fontweight="bold", family=MONO,
                ha="center", va="center", zorder=4)

    out = OUT / ("social_square.png" if square else "cover_landscape.png")
    fig.savefig(out, facecolor=CREAM)
    plt.close(fig)
    return out


if __name__ == "__main__":
    print("cards:", build(False).name, build(True).name)
