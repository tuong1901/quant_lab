"""Run with: python -m src.features.candle.visualize [--output candle_anatomy.png]."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from src.features.candle import add_candle_anatomy, add_candle_normalization, add_reversal_patterns
from src.features.candle.demo import DEMO_REVERSAL_CRITERIA, build_demo_frame


def build_featured_demo():
    """
    [PURPOSE]: Create the deterministic candle-feature table used by the anatomy visualization.
    [DEPENDENCIES]: Reuses the existing candle demo data and feature pipeline.
    [ARGS]: None.
    [RETURNS]: DataFrame with OHLC, anatomy, normalization, and reversal-pattern columns.
    [SIDE EFFECTS]: None.
    """
    return add_reversal_patterns(add_candle_normalization(add_candle_anatomy(build_demo_frame()), "atr"), DEMO_REVERSAL_CRITERIA)


def plot_candle_anatomy(featured):
    """
    [PURPOSE]: Render candles with body/wicks and their computed feature values.
    [DEPENDENCIES]: Requires Matplotlib and the candle feature output columns.
    [ARGS]: featured — DataFrame returned by build_featured_demo.
    [RETURNS]: Matplotlib Figure.
    [SIDE EFFECTS]: Creates a figure in the active Matplotlib backend.
    """
    figure, axis = plt.subplots(figsize=(16, 9))
    for index, row in featured.iterrows():
        color = "#16a34a" if row.candle_direction > 0 else "#dc2626" if row.candle_direction < 0 else "#64748b"
        axis.vlines(index, row.low, row.high, color=color, linewidth=2, zorder=1)
        body_bottom = min(row.open, row.close)
        body_height = max(row.candle_body, 0.25)
        axis.add_patch(Rectangle((index - 0.32, body_bottom), 0.64, body_height, facecolor=color, edgecolor="#111827", zorder=2))
        labels = [
            f"range={row.candle_range:.1f}", f"body={row.candle_body:.1f}",
            f"upper={row.upper_wick:.1f}", f"lower={row.lower_wick:.1f}",
            f"body%={row.candle_body_ratio:.2f}" if row.candle_range > 0 else "body%=NaN",
            f"close pos={row.close_position:.2f}" if row.candle_range > 0 else "close pos=NaN",
        ]
        patterns = [name for name in ("bullish_pin_bar", "bearish_pin_bar", "bullish_engulfing", "bearish_engulfing") if row[name]]
        if patterns:
            labels.append("PATTERN: " + ", ".join(patterns))
        axis.annotate("\n".join(labels), (index, row.high), xytext=(0, 12), textcoords="offset points", ha="center", fontsize=8)
    axis.set_xticks(featured.index)
    axis.set_xticklabels(featured["name"], rotation=18, ha="right")
    axis.set_ylim(featured["low"].min() - 4.0, featured["high"].max() + 16.0)
    axis.set_title("Candle Anatomy: body, wicks, normalized geometry, and reversal evidence", pad=18)
    axis.set_ylabel("Price")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    return figure


def main() -> None:
    """
    [PURPOSE]: Display or save the candle anatomy visualization.
    [DEPENDENCIES]: build_featured_demo and plot_candle_anatomy.
    [ARGS]: None; reads optional --output command-line argument.
    [RETURNS]: None.
    [SIDE EFFECTS]: Opens a Matplotlib window or writes a PNG image.
    """
    parser = argparse.ArgumentParser(description="Visualize the candle feature demo.")
    parser.add_argument("--output", help="Optional PNG output path; omit to open an interactive window.")
    args = parser.parse_args()
    figure = plot_candle_anatomy(build_featured_demo())
    if args.output:
        output = Path(args.output)
        figure.savefig(output, dpi=160)
        print(f"Saved candle anatomy visualization: {output.resolve()}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
