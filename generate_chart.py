"""
generate_chart.py
-----------------
Reads data/products.csv and generates docs/index.html — the interactive
Vegan Protein per Euro chart hosted on GitHub Pages.

Usage:
    python generate_chart.py            # bundles Plotly JS, works offline
    python generate_chart.py --deploy   # loads Plotly from CDN, smaller file

Output:
    docs/index.html  (commit and push to update the live site)
"""

import sys
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

INPUT_CSV = Path("data/products.csv")
OUTPUT_HTML = Path("docs/index.html")

DEPLOY = "--deploy" in sys.argv
PLOTLYJS = "cdn" if DEPLOY else True

CATEGORY_COLORS = [
    "#7eb8d4",  # soft blue
    "#f4a96a",  # peach
    "#8ecf8e",  # sage green
    "#f28b8b",  # soft red
    "#b8a0d4",  # lavender
    "#c4987a",  # warm brown
    "#f5b8d4",  # blush pink
    "#a8a8a8",  # muted grey
    "#d4cf6e",  # soft yellow-green
    "#76cfc9",  # teal mint
]

# ---------------------------------------------------------------------------
# Load & validate
# ---------------------------------------------------------------------------

df = pd.read_csv(INPUT_CSV, sep=";")

# Rename columns to clean internal names
df.columns = [
    "product", "category", "package_size_g", "protein_in_package_g",
    "price_per_kg", "protein_per_100g", "price_per_100g_protein_raw"
]

# Drop rows with missing values in key columns
df = df.dropna(subset=["product", "category", "protein_per_100g", "price_per_kg"])

# ---------------------------------------------------------------------------
# Computed columns
# ---------------------------------------------------------------------------

# Recalculate price per 100g protein from raw data (don't trust the CSV column)
df["price_per_100g_protein"] = (df["price_per_kg"] / 10) / (df["protein_per_100g"] / 100)

# Value score: composite 0-100, higher = better value
# Equally weights protein density and cost efficiency, both normalised 0-1
max_protein = df["protein_per_100g"].max()
max_price = df["price_per_100g_protein"].max()

df["value_score"] = (
    (df["protein_per_100g"] / max_protein) * 0.5 +
    (1 - df["price_per_100g_protein"] / max_price) * 0.5
) * 100

df["value_score"] = df["value_score"].round(1)

# ---------------------------------------------------------------------------
# Axis ranges
# ---------------------------------------------------------------------------

x_max = df["protein_per_100g"].max() * 1.05
y_max = df["price_per_100g_protein"].max() * 1.05
x_min = df["protein_per_100g"].min() * 0.95
y_min = 0

# ---------------------------------------------------------------------------
# Build traces — one per category
# ---------------------------------------------------------------------------

categories = df["category"].unique()
traces = []

for i, cat in enumerate(categories):
    sub = df[df["category"] == cat]
    color = CATEGORY_COLORS[i % len(CATEGORY_COLORS)]

    traces.append(go.Scatter(
        x=sub["protein_per_100g"],
        y=sub["price_per_100g_protein"],
        mode="markers",
        name=cat,
        legendgroup=cat,
        text=sub["product"],
        customdata=list(zip(
            sub["price_per_kg"].round(2),
            sub["value_score"],
        )),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Protein: %{x} g / 100g<br>"
            "Price: %{y:.2f} € / 100g protein<br>"
            "Shelf price: €%{customdata[0]} / kg<br>"
            "Value score: %{customdata[1]}/100"
            "<extra></extra>"
        ),
        marker=dict(
            symbol="circle",
            color=color,
            size=15,
            opacity=0.85,
            line=dict(width=1, color="black"),
        ),
    ))

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

layout = go.Layout(
    title=dict(text="Plant based products: protein density vs price", x=0.5),
    xaxis=dict(
        title=dict(text="Protein (g per 100g)", standoff=15),
        range=[x_min, x_max],
        zeroline=False,
        gridcolor="#eee",
        showline=True, linecolor="#333", linewidth=1, mirror=True,
    ),
    yaxis=dict(
        title=dict(text="Price (€ per 100g protein)", standoff=15),
        range=[y_min, y_max],
        zeroline=False,
        gridcolor="#eee",
        showline=True, linecolor="#333", linewidth=1, mirror=True,
    ),
    hovermode="closest",
    legend=dict(
        x=1.05,
        y=0.5,
        title=dict(
            text="Product groups<br><sup>Double-click a category to isolate it</sup>",
            font=dict(size=13),
        ),
    ),
    plot_bgcolor="#fff",
    annotations=[
        # Top-left: bad value zone
        dict(
            xref="paper", yref="paper",
            x=0.01, y=0.99,
            text="↖ more expensive,<br>less protein-dense",
            showarrow=False,
            font=dict(size=11, color="#bbb", style="italic"),
            xanchor="left", yanchor="top",
        ),
        # Bottom-right: best value zone
        dict(
            xref="paper", yref="paper",
            x=0.99, y=0.01,
            text="cheaper,<br>more protein-dense ↘",
            showarrow=False,
            font=dict(size=11, color="#8ecf8e", style="italic"),
            xanchor="right", yanchor="bottom",
        ),
    ],
)

# ---------------------------------------------------------------------------
# Assemble figure and export
# ---------------------------------------------------------------------------

fig = go.Figure(data=traces, layout=layout)

OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)

fig.write_html(
    OUTPUT_HTML,
    include_plotlyjs=PLOTLYJS,
    full_html=True,
    config={"responsive": True},
)

mode = "deploy (CDN)" if DEPLOY else "local (bundled JS)"
print(f"Chart written to {OUTPUT_HTML} [{mode}]")
print(f"  {len(df)} products across {len(categories)} categories")
if DEPLOY:
    print("\n  Live site (after push):")
    print("  https://smallperalta.github.io/vegan-protein-economics/")
else:
    print("\n  To view locally:")
    print("  open docs/index.html")