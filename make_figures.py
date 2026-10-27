"""Regenerate every PNG in figs/ (and optionally the Plotly slider as HTML).

Usage:
    python make_figures.py              # data from data/*.csv or kagglehub
    python make_figures.py --html       # also write figs/affordability_slider.html
    python make_figures.py --csv path/to/file.csv
"""
from __future__ import annotations

import argparse
import pathlib

import matplotlib

matplotlib.use("Agg")  # write files, never open windows
import matplotlib.pyplot as plt  # noqa: E402
import seaborn as sns  # noqa: E402

import housing_viz as hv  # noqa: E402

OUT_DIR = pathlib.Path(__file__).resolve().parent / "figs"
CORR_VARS = ["House_Price_Index", "Rent_Index", "Mortgage_Rate_pct",
             "Inflation_Rate_pct", "GDP_Growth_pct", "Population_Growth_pct"]


def _save(tag: str, dpi: int = 300) -> None:
    plt.savefig(OUT_DIR / f"{tag}.png", dpi=dpi, bbox_inches="tight")
    plt.close("all")


def main(csv: str | None = None, html: bool = False) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    df = hv.load_housing_data(csv)

    plt.figure(figsize=(12, 6)); hv.line_hpi_all(df); _save("hpi_spaghetti")
    plt.figure(figsize=(9, 5)); hv.top_growth(df, top_n=5); _save("top5_growth")

    g = sns.FacetGrid(df, col="Year", col_wrap=3, height=4, sharex=False)
    g.map_dataframe(hv.affordability_bar, n_countries=10)
    plt.tight_layout(); _save("affordability_facets")

    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharey=True)
    for ax, c in zip(axes.ravel(), ["USA", "Japan", "Germany", "Australia"]):
        hv.plot_hpi_smoothed(df, c, ax=ax)
    plt.tight_layout(); _save("hpi_smoothed_panel")

    plt.figure(figsize=(10, 6)); hv.yoy_heatmap(df); _save("yoy_heatmap")
    plt.figure(figsize=(9, 5)); hv.region_boxplot(df); _save("region_boxplot")
    plt.figure(figsize=(6, 5)); hv.corr_heatmap(df, "Japan", CORR_VARS); _save("japan_corr")

    if html:
        hv.plotly_affordability_slider(df).write_html(OUT_DIR / "affordability_slider.html")
    print(hv.persistence_check(df))
    print(f"Figures written to {OUT_DIR}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--csv", help="path to the dataset CSV (optional)")
    p.add_argument("--html", action="store_true", help="also export the Plotly slider")
    a = p.parse_args()
    main(a.csv, a.html)
