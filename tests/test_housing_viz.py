"""Smoke tests on a small fake frame with the dataset's schema.

The real data needs a Kaggle token, so CI checks the plotting code and the
region mapping against the dataset's 20 country names instead.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pytest  # noqa: E402

import housing_viz as hv  # noqa: E402

# Country names as they appear in the dataset (read from the notebook output).
COUNTRIES = ["Australia", "Brazil", "Canada", "China", "France", "Germany",
             "India", "Italy", "Japan", "Mexico", "Netherlands", "Russia",
             "South Africa", "South Korea", "Spain", "Sweden", "Switzerland",
             "UAE", "UK", "USA"]


@pytest.fixture
def df():
    rng = np.random.default_rng(0)
    rows = [(c, y) for c in COUNTRIES for y in range(2015, 2025)]
    raw = pd.DataFrame(rows, columns=["Country", "Year"])
    for col in ["House Price Index", "Rent Index", "Affordability Ratio",
                "Mortgage Rate (%)", "Inflation Rate (%)", "GDP Growth (%)",
                "Population Growth (%)"]:
        raw[col] = rng.uniform(1, 10, len(raw))
    return hv._clean_columns(raw)


def test_columns_cleaned(df):
    assert {"House_Price_Index", "Mortgage_Rate_pct", "Affordability_Ratio"} <= set(df.columns)


def test_region_map_covers_every_country():
    assert set(COUNTRIES) <= set(hv.REGION_MAP)


def test_region_boxplot_rejects_unmapped(df):
    with pytest.raises(ValueError):
        hv.region_boxplot(df, {"USA": "Americas"})


def test_all_plots_run(df):
    hv.line_hpi_all(df); plt.close("all")
    hv.top_growth(df); plt.close("all")
    hv.yoy_heatmap(df); plt.close("all")
    hv.region_boxplot(df); plt.close("all")
    hv.corr_heatmap(df, "Japan", ["House_Price_Index", "Rent_Index"]); plt.close("all")
    hv.plot_hpi_smoothed(df, "USA"); plt.close("all")
    hv.plotly_affordability_slider(df)


def test_load_from_local_csv(tmp_path, df):
    p = tmp_path / "housing.csv"
    df.to_csv(p, index=False)
    assert len(hv.load_housing_data(p)) == 200


def test_persistence_check_flags_random_data(df):
    out = hv.persistence_check(df)
    assert out["n_rows"] == 200 and out["n_countries"] == 20
    assert abs(out["median_lag1_autocorr"]) < 0.5
