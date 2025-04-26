# -*- coding: utf-8 -*-
"""
Created on Fri Apr 25 20:15:05 2025

@author: lukew
"""

# ─────────────────────────────────────────────────────────────
# housing_viz.py  –  helper module for the Global Housing data
# ─────────────────────────────────────────────────────────────
from __future__ import annotations

import pathlib
import kagglehub
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

sns.set_theme(style="whitegrid")

# ╭─────────────────────────── 1. DATA I/O ───────────────────────────╮
def download_housing_dataset(
        url: str = "atharvasoundankar/global-housing-market-analysis-2015-2024"
) -> pd.DataFrame:
    """Download + clean the Kaggle dataset; cached after first call."""
    root = pathlib.Path(kagglehub.dataset_download(url))
    csv  = next(root.rglob("*.csv*"))
    df   = pd.read_csv(csv)

    df.columns = (df.columns
                    .str.strip()
                    .str.replace(" ", "_")
                    .str.replace("%", "pct")
                    .str.replace(r"[()]", "", regex=True))
    return df
# ╰────────────────────────────────────────────────────────────╯


# ╭──────────────────── 2. GENERIC PLOT FUNCTIONS ───────────────────╮
def line_hpi_all(df, ax=None):
    ax = ax or plt.gca()
    sns.lineplot(data=df, x="Year", y="House_Price_Index",
                 hue="Country", estimator=None, linewidth=1.2, ax=ax)
    ax.set_title("House-Price Index by Country (2015-2024)", weight="bold")
    return ax


def top_growth(df, top_n=5, ax=None):
    growth = (df.groupby("Country")
                .apply(lambda g: g.loc[g.Year==2024, "House_Price_Index"].iat[0]
                                - g.loc[g.Year==2015, "House_Price_Index"].iat[0])
                .sort_values(ascending=False))
    focus = df[df.Country.isin(growth.head(top_n).index)]
    ax = ax or plt.gca()
    sns.lineplot(data=focus, x="Year", y="House_Price_Index",
                 hue="Country", marker="o", linewidth=2, ax=ax)
    ax.set_title(f"Top {top_n} fastest-growing markets", weight="bold")
    return ax


def pairplot_country(df, country, vars_pair=None):
    vars_pair = vars_pair or ["House_Price_Index", "Rent_Index",
                              "Mortgage_Rate_pct", "Inflation_Rate_pct",
                              "GDP_Growth_pct"]
    g = sns.pairplot(df[df.Country == country][["Year"] + vars_pair],
                     diag_kind="kde", corner=True)
    g.fig.suptitle(f"{country}: key relationships", y=1.02, weight="bold")
    return g


def affordability_bar(data, ax=None, n_countries=None, **kwargs):
    """Bar chart used inside FacetGrid – `data` already subset to one Year."""
    year = int(data["Year"].iat[0])
    snap = data.sort_values("Affordability_Ratio", ascending=False)
    if n_countries:
        snap = snap.head(n_countries)

    ax = ax or plt.gca()
    sns.barplot(data=snap, y="Country", x="Affordability_Ratio",
                hue="Country", palette="rocket_r",
                legend=False, ax=ax, **kwargs)
    ax.set_title(year)
    ax.set_xlabel("Affordability Ratio (higher = worse)")
    ax.set_ylabel("")
    return ax


def yoy_heatmap(df, ax=None):
    gdf = (df.sort_values(["Country", "Year"])
             .assign(YoY=lambda d: d.groupby("Country")
                                    .House_Price_Index.pct_change()*100)
             .pivot(index="Country", columns="Year", values="YoY"))
    ax = ax or plt.gca()
    sns.heatmap(gdf, cmap="coolwarm", center=0, annot=True,
                fmt=".1f", linewidth=.4, ax=ax)
    ax.set_title("% YoY change in House-Price Index")
    return ax


def region_boxplot(df, region_map: dict[str,str], ax=None):
    local = df.copy()
    local["Region"] = local.Country.map(region_map)
    ax = ax or plt.gca()
    sns.boxplot(data=local, x="Region", y="Affordability_Ratio",
                order=sorted(local.Region.dropna().unique()), ax=ax)
    ax.set_title("Affordability Ratio by Region (2015-2024)")
    ax.tick_params(axis="x", rotation=30)
    return ax


def corr_heatmap(df, country, vars_num, ax=None):
    corr = df[df.Country == country][vars_num].corr()
    ax = ax or plt.gca()
    sns.heatmap(corr, vmin=-1, vmax=1, cmap="vlag",
                annot=True, ax=ax)
    ax.set_title(f"{country} – correlation matrix")
    return ax


def plot_hpi_smoothed(df, country, window=3, ax=None,
                      annual_kw=None, smooth_kw=None):
    annual_kw = annual_kw or dict(marker="o", label="Annual")
    smooth_kw = smooth_kw or dict(linewidth=3, label=f"{window}-yr avg")
    ax = ax or plt.gca()

    g = (df[df.Country == country]
           .sort_values("Year")
           .assign(Smooth=lambda d: d.House_Price_Index
                                   .rolling(window, center=True).mean()))
    ax.plot(g.Year, g.House_Price_Index, **annual_kw)
    ax.plot(g.Year, g.Smooth, **smooth_kw)
    ax.set_title(f"{country} – HPI smoothed")
    ax.set_ylabel("House_Price_Index")
    ax.legend(frameon=False)
    return ax
# ╰────────────────────────────────────────────────────────────╯


# ╭──────── 3. INTERACTIVE PLOTLY SLIDER (optional) ───────────╮
def plotly_affordability_slider(df):
    fig = px.bar(df.sort_values("Affordability_Ratio", ascending=False),
                 y="Country", x="Affordability_Ratio",
                 animation_frame="Year", animation_group="Country",
                 orientation="h", color="Country", height=600,
                 labels={"Affordability_Ratio": "Affordability Ratio"},
                 title="Affordability Ratio – least affordable markets")
    fig.update_layout(xaxis_title="Affordability Ratio (higher = worse)",
                      yaxis_title="")
    return fig
# ╰────────────────────────────────────────────────────────────╯


# ───────────────────────────  DEMO  ───────────────────────────
if __name__ == "__main__":        # runs only if you execute the file directly
    import seaborn as sns, matplotlib.pyplot as plt

    df_demo = download_housing_dataset()

    plt.figure(figsize=(12, 6))
    line_hpi_all(df_demo); plt.show()

    g_demo = sns.FacetGrid(df_demo, col="Year", col_wrap=3, height=4, sharex=False)
    g_demo.map_dataframe(affordability_bar, n_countries=10)
    plt.tight_layout(); plt.show()
