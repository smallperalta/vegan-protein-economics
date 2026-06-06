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
    "price_per_kg", "protein_per_100g", "price_per_100g_protein_raw", "url"
]

# Drop rows with missing values in key columns
df = df.dropna(subset=["product", "category", "protein_per_100g", "price_per_kg"])

# ---------------------------------------------------------------------------
# Computed columns
# ---------------------------------------------------------------------------

# Recalculate price per 100g protein from raw data (don't trust the CSV column)
df["price_per_100g_protein"] = (df["price_per_kg"] / 10) / (df["protein_per_100g"] / 100)
df["price_per_100g_protein"] = df["price_per_100g_protein"].round(2)
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
    #title=dict(text="Plant based products: protein density vs price", x=0.5),
    title=None,
    margin=dict(t=30),
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
 
# ---------------------------------------------------------------------------
# Build table
# ---------------------------------------------------------------------------
# select only the columns we want to show — not all of them
display_df = df[["product", "category", "protein_per_100g", "price_per_kg", "price_per_100g_protein", "url"]].copy()
# Add clickable link column
display_df["url"] = display_df["url"].apply(
    lambda u: f'<a href="{u}" target="_blank">link</a>' if pd.notna(u) and u != "" else ""
)
# rename to human-readable headers
display_df.columns = ["Product", "Category", "Protein (g/100g)", "Price (€/kg)", "€ per 100g protein", "URL"]
# default sort: cheapest protein first
display_df = display_df.sort_values("€ per 100g protein")


# index=False: don't show the row numbers pandas adds by default
# classes="product-table": adds a CSS class so DataTables can find it
# border=0: no old-school HTML table border attribute
# escape=False: so the <a> tags render as real links, not as text
table_html = display_df.to_html(index=False, classes="product-table", border=0, escape=False)


# ---------------------------------------------------------------------------
# Build full HTML page
# ---------------------------------------------------------------------------

chart_div = fig.to_html(
    full_html=False,
    include_plotlyjs=PLOTLYJS,
    config={"responsive": True},
)

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Vegan Protein per Euro</title>
  <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 20px 40px;
      background: #fafafa;
      color: #333;
    }}
    h1 {{
      font-size: 1.8em;
      margin-bottom: 4px;
    }}
    .subtitle {{
      color: #888;
      font-size: 0.95em;
      margin-bottom: 24px;
    }}
    .chart-container {{
      background: white;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 40px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }}
    .table-container {{
      background: white;
      border-radius: 8px;
      padding: 24px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }}
    h2 {{
      font-size: 1.2em;
      margin-bottom: 16px;
    }}
    table.product-table {{
      width: 100%;
      font-size: 0.9em;
    }}
  </style>
</head>
<body>

  <h1>Plant-based Protein per Euro: are you spending your money wisely?</h1>
  <p class="subtitle">Finnish plant-based products, compared by cost and protein density. Hover over the dots to get more info.</p>

  <div class="chart-container">
    {chart_div}
  </div>

  <div class="table-container">
  <p style="color:#888; font-size:0.85em;">
    ⚠️ Prices and nutritional values are approximate and may vary by store and date. 
    Always check the product label.
  </p>
    <h2>All products</h2>
    {table_html}
  </div>

  <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
  <script>
    $(document).ready(function() {{
      $(".product-table").DataTable({{
        pageLength: 25,
        order: [[4, "asc"]],
        columnDefs: [{{ targets: [2, 3, 4, 5], className: "dt-right" }}]
      }});
    }});
  </script>

</body>
</html>"""

OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
 
with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(page)

mode = "deploy (CDN)" if DEPLOY else "local (bundled JS)"
print(f"Chart written to {OUTPUT_HTML} [{mode}]")
print(f"  {len(df)} products across {len(categories)} categories")
if DEPLOY:
    print("\n  Live site (after push):")
    print("  https://smallperalta.github.io/vegan-protein-economics/")
else:
    print("\n  To view locally:")
    print("  open docs/index.html")