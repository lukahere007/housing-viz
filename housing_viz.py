"""
housing_viz.py - plotting helpers for the Kaggle "Global Housing Market
Analysis 2015-2024" dataset (20 countries x 10 years = 200 rows).

Author: Luke Wamalwa

Note: the dataset looks randomly generated (see README, "About the data"),
so these functions are best read as a visualisation toolkit, not as a
source of real-world housing conclusions.
"""
from __future__ import annotations

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns

sns.set_theme(style="whitegrid")

KAGGLE_DATASET = "atharvasoundankar/global-housing-market-analysis-2015-2024"
DATA_DIR = pathlib.Path(__file__).resolve().parent / "data"

# Country names exactly as they appear in the dataset (with spaces).
REGION_MAP: dict[str, str] = {
    "USA": "Americas", "Canada": "Americas", "Brazil": "Americas",
    "Mexico": "Americas",
    "UK": "Europe", "Germany": "Europe", "France": "Europe", "Italy": "Europe",
    "Spain": "Europe", "Netherlands": "Europe", "Sweden": "Europe",
    "Switzerland": "Europe", "Russia": "Europe/Asia",
    "China": "Asia", "India": "Asia", "Japan": "Asia", "South Korea": "Asia",
    "Australia": "Oceania", "UAE": "Middle East", "South Africa": "Africa",
}


# ╭─────────────────────────── 1. DATA I/O ───────────────────────────╮
def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (df.columns
                    .str.strip()
                    .str.replace(" ", "_")
                    .str.replace("%", "pct")
                    .str.replace(r"[()]", "", regex=True))
    return df


def load_housing_data(csv_path: str | pathlib.Path | None = None,
                      dataset: str = KAGGLE_DATASET) -> pd.DataFrame:
    """Load and clean the dataset.

    Order of preference: an explicit `csv_path`, any CSV in `data/`, and
    finally a download through kagglehub (needs a Kaggle API token; cached
    in ~/.cache/kagglehub after the first call).
    """
    if csv_path is None:
        local = sorted(DATA_DIR.glob("*.csv"))
        if local:
            csv_path = local[0]
    if csv_path is None:
        import kagglehub  # imported lazily so the plots work without it
        root = pathlib.Path(kagglehub.dataset_download(dataset))
        csv_path = next(root.rglob("*.csv*"))
    return _clean_columns(pd.read_csv(csv_path))


# Backwards-compatible name used in the original notebooks.
download_housing_dataset = load_housing_data
# ╰────────────────────────────────────────────────────────────╯


# ╭──────────────────── 2. GENERIC PLOT FUNCTIONS ───────────────────╮
def line_hpi_all(df, ax=None):
    ax = ax or plt.gca()
    sns.lineplot(data=df, x="Year", y="House_Price_Index",
                 hue="Country", estimator=None, linewidth=1.2, ax=ax)
    ax.set_title("House-Price Index by Country (2015-2024)", weight="bold")
    return ax


def top_growth(df, top_n=5, ax=None):
    wide = df.pivot(index="Country", columns="Year", values="House_Price_Index")
    growth = (wide[wide.columns.max()] - wide[wide.columns.min()]).sort_values(ascending=False)
    focus = df[df.Country.isin(growth.head(top_n).index)]
    ax = ax or plt.gca()
    sns.lineplot(data=focus, x="Year", y="House_Price_Index",
                 hue="Country", marker="o", linewidth=2, ax=ax)
    ax.set_title(f"Top {top_n} markets by HPI change, first to last year", weight="bold")
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


def region_boxplot(df, region_map: dict[str, str] | None = None, ax=None):
    region_map = region_map or REGION_MAP
    missing = sorted(set(df.Country) - set(region_map))
    if missing:
        raise ValueError(f"No region for: {missing}")
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
    ax.set_title(f"{country} – correlation matrix (n = {len(df[df.Country == country])} years)")
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


# ╭──────────── 4. IS THERE ANY SIGNAL? (sanity check) ────────────╮
def persistence_check(df, col: str = "Affordability_Ratio") -> dict:
    """Quick test of whether a country-year series behaves like real data.

    Real housing indicators are persistent: this year's value is close to
    last year's, and countries differ from each other. Independent random
    draws show lag-1 autocorrelation near zero and no country effect.
    """
    from scipy import stats

    wide = df.pivot(index="Country", columns="Year", values=col).sort_index(axis=1)
    lag1 = [np.corrcoef(r[:-1], r[1:])[0, 1] for r in wide.to_numpy()]
    anova = stats.f_oneway(*[g[col].to_numpy() for _, g in df.groupby("Country")])
    return {
        "n_rows": len(df),
        "min": float(df[col].min()),
        "max": float(df[col].max()),
        "median_lag1_autocorr": float(np.median(lag1)),
        "countries_with_positive_lag1": int(sum(a > 0 for a in lag1)),
        "n_countries": int(wide.shape[0]),
        "median_abs_yearly_change": float(wide.diff(axis=1).abs().stack().median()),
        "country_anova_p": float(anova.pvalue),
    }
# ╰────────────────────────────────────────────────────────────╯
